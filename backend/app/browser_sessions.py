"""Revocable browser sessions; only a hash of the cookie is stored in MongoDB."""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, Response
from backend.app.database import db
from pymongo import ReturnDocument

COOKIE = "mmss_session"
sessions = db["browser_sessions"]
sessions.create_index("digest", unique=True)
sessions.create_index("expires_at", expireAfterSeconds=0)
from backend.app.origin_config import browser_origins
ALLOWED_ORIGINS = browser_origins()


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def check_origin(request: Request):
    if request.headers.get("origin") not in ALLOWED_ORIGINS:
        raise HTTPException(403, "Browser request origin is not allowed.")


def issue(request: Request, response: Response, username: str, role: str):
    check_origin(request)
    # Only HTTP loopback development is exempt from Secure cookies.
    local_http = request.url.scheme == "http" and request.url.hostname in ("localhost", "127.0.0.1", "testserver") and os.getenv("ENVIRONMENT", "development") != "production"
    if request.url.scheme != "https" and not local_http:
        raise HTTPException(400, "Browser sign-in requires HTTPS.")
    revoke(request)
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=30)
    sessions.insert_one({"digest": digest(token), "username": username, "expires_at": expires,
                         "absolute_expires_at": now + timedelta(hours=8)})
    response.set_cookie(COOKIE, token, max_age=8 * 3600, httponly=True, secure=not local_http,
                        samesite="strict", path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"role": role, "expires_at": expires.isoformat()}


def revoke(request: Request):
    token = request.cookies.get(COOKIE)
    if token:
        sessions.delete_one({"digest": digest(token)})


def resolve(request: Request):
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        check_origin(request)
    now = datetime.now(timezone.utc)
    query = {"digest": digest(token), "expires_at": {"$gt": now}, "absolute_expires_at": {"$gt": now}}
    record = sessions.find_one(query)
    # Background health/profile polling must not keep an unattended session alive.
    if record and request.url.path not in ('/auth/me', '/admin/health', '/doctor/reference-status'):
        absolute = record['absolute_expires_at']
        if absolute.tzinfo is None:
            absolute = absolute.replace(tzinfo=timezone.utc)
        record = sessions.find_one_and_update(query, {'$max': {'expires_at': min(now + timedelta(minutes=30), absolute)}},
                                              return_document=ReturnDocument.AFTER)
    return record["username"] if record else None
