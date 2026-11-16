"""Bound public requests; production uses shared MongoDB counters.

Uses the ASGI client address. Only trust forwarded headers from an explicitly
configured reverse proxy; local startup disables proxy headers entirely.
"""
from collections import OrderedDict
import time
import os
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from starlette.responses import JSONResponse
from starlette.requests import Request


class RequestLimits:
    def __init__(self, app):
        self.app = app
        self.windows = OrderedDict()
        self.shared = os.getenv('ENVIRONMENT', '').lower() == 'production' or os.getenv('RATE_LIMIT_BACKEND') == 'mongo'
        if self.shared:
            from backend.app.database import db
            self.buckets = db['request_limits']
            self.buckets.create_index('expires_at', expireAfterSeconds=0)

    def shared_count(self, key, seconds=60):
        from pymongo import ReturnDocument
        now = time.time()
        window = int(now) // seconds
        identifier = hashlib.sha256(repr((key, seconds)).encode()).hexdigest() + ':' + str(window)
        row = self.buckets.find_one_and_update({'_id': identifier}, {'$inc': {'count': 1}, '$setOnInsert': {
            'expires_at': datetime.fromtimestamp((window + 2) * seconds, timezone.utc)}}, upsert=True, return_document=ReturnDocument.AFTER)
        return row['count'] - 1, now - window * seconds

    async def consume(self, key, limit, seconds=60):
        if self.shared:
            count, elapsed = await asyncio.to_thread(self.shared_count, key, seconds)
        else:
            timestamp = time.monotonic()
            start, count = self.windows.get(key, (timestamp, 0))
            if timestamp - start >= seconds:
                start, count = timestamp, 0
            self.windows[key] = (start, count + 1)
            self.windows.move_to_end(key)
            while len(self.windows) > 10000:
                self.windows.popitem(last=False)
            elapsed = timestamp - start
        if count >= limit:
            return JSONResponse({'detail': 'Too many requests. Please retry shortly.'}, 429,
                                headers={'Retry-After': str(max(1, int(seconds - elapsed)))})
        return None

    def identity(self, scope):
        # Validate against the session store without renewing idle expiry. A
        # made-up, revoked or expired cookie never gets a fresh quota bucket.
        from backend.app.browser_sessions import COOKIE, digest, sessions
        token = Request(scope).cookies.get(COOKIE)
        if token and len(token) <= 256:
            now = datetime.now(timezone.utc)
            record = sessions.find_one({'digest': digest(token), 'expires_at': {'$gt': now},
                                        'absolute_expires_at': {'$gt': now}})
            if record:
                return 'user:' + hashlib.sha256(record['username'].encode()).hexdigest(), True
        return 'ip:' + (scope.get('client') or ('unknown', 0))[0], False

    async def rate_response(self, scope, path, heavy, auth):
        try:
            peer = 'ip:' + (scope.get('client') or ('unknown', 0))[0]
            # Source checks precede cookie lookup and cannot be reset by minting
            # accounts or switching sessions. Shared counters apply in production.
            if heavy:
                response = await self.consume((peer, 'upload-source'), 60)
                if response is not None:
                    return response
            if auth and (path in ('/auth/register-session', '/auth/doctor-request', '/auth/register-doctor')
                         or scope.get('mmss_registration', False)):
                response = await self.consume((peer, 'registration-source'), 30, 3600)
                if response is not None:
                    return response
            # Login attempts are bounded by source even when a cookie is supplied.
            identity, signed_in = (('ip:' + (scope.get('client') or ('unknown', 0))[0], False)
                                   if auth else await asyncio.to_thread(self.identity, scope))
            group = ('auth' if auth else 'upload' if heavy else 'graph' if path.startswith('/neo4j/')
                     else 'catalog' if path.startswith('/medicine') else 'tts' if path == '/tts'
                     else 'health' if path == '/health' else 'analysis')
            limit = 60 if auth else 20 if heavy else 120 if signed_in else 300
            key = (identity, group)
            return await self.consume(key, limit)
        except Exception:
            return JSONResponse({'detail': 'Request limiting is unavailable. Please retry.'}, 503)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        path = scope['path'].rstrip('/')
        heavy = path in ('/upload-image', '/prescription-ocr', '/voice-search')
        auth = path.startswith('/auth/') and scope['method'] == 'POST'
        limited = auth or heavy or path.startswith(('/interaction', '/ml/', '/neo4j/', '/medicine/')) or path in ('/tts', '/medicines', '/health')
        max_size = 10 * 1024 * 1024 if heavy else 64 * 1024
        headers = dict(scope.get('headers', []))
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            return await JSONResponse({'detail': 'Invalid Content-Length.'}, 400)(scope, receive, send)
        if length < 0:
            return await JSONResponse({'detail': 'Invalid Content-Length.'}, 400)(scope, receive, send)
        if length > max_size or len(scope.get('query_string', b'')) > 65536:
            return await JSONResponse({'detail': 'Request is too large.'}, 413)(scope, receive, send)
        if limited and scope['method'] != 'OPTIONS' and path != '/auth/google-session':
            response = await self.rate_response(scope, path, heavy, auth)
            if response is not None:
                return await response(scope, receive, send)
        messages, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            size += len(message.get('body', b''))
            if size > max_size:
                return await JSONResponse({'detail': 'Request is too large.'}, 413)(scope, receive, send)
            messages.append(message)
            if not message.get('more_body', False):
                break
        if path == '/auth/google-session' and scope['method'] == 'POST':
            try:
                payload = json.loads(b''.join(message.get('body', b'') for message in messages))
                scope['mmss_registration'] = isinstance(payload, dict) and payload.get('mode') == 'register'
            except (ValueError, UnicodeError):
                pass
            response = await self.rate_response(scope, path, heavy, auth)
            if response is not None:
                return await response(scope, receive, send)
        iterator = iter(messages)
        async def replay():
            message = next(iterator, None)
            return message if message is not None else await receive()
        await self.app(scope, replay, send)
