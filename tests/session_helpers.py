"""Synthetic cookie sessions for isolated authorization tests only."""
import secrets
from datetime import datetime, timedelta, timezone
from backend.app import browser_sessions

ORIGIN = {'Origin': 'http://localhost:5173'}


def session_headers(username):
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    browser_sessions.sessions.insert_one({'digest': browser_sessions.digest(token), 'username': username,
        'expires_at': now + timedelta(minutes=30), 'absolute_expires_at': now + timedelta(hours=8)})
    return {**ORIGIN, 'Cookie': f'{browser_sessions.COOKIE}={token}'}
