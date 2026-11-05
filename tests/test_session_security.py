from datetime import datetime, timedelta, timezone
import mongomock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app import auth, browser_sessions as sessions
from backend.app.routes import auth as routes
from backend.main import app

ORIGIN = {"Origin": "http://localhost:5173"}


@pytest.fixture
def browser(monkeypatch):
    db = mongomock.MongoClient().sessions_test
    monkeypatch.setattr(sessions, "sessions", db.sessions)
    monkeypatch.setattr(auth, "users_collection", db.users)
    monkeypatch.setattr(routes, "users_collection", db.users)
    db.users.insert_one({"username": "patient@example.test", "role": "patient",
                         "hashed_password": auth.get_password_hash("Strong-test-password")})
    # Fresh middleware window for each test.
    local = FastAPI()
    local.include_router(routes.router)
    yield TestClient(local), db


def login(browser):
    client, _ = browser
    return client.post('/auth/session', headers=ORIGIN,
                       data={"username": "patient@example.test", "password": "Strong-test-password"})


def test_cookie_private_hashed_expiring_and_revocable(browser):
    client, db = browser
    response = login(browser)
    assert response.status_code == 200 and 'access_token' not in response.json()
    assert 'HttpOnly' in response.headers['set-cookie'] and 'SameSite=strict' in response.headers['set-cookie']
    token = client.cookies.get(sessions.COOKIE)
    assert token not in str(db.sessions.find_one())
    assert client.get('/auth/me').status_code == 200
    assert client.post('/auth/logout', headers=ORIGIN).status_code == 200
    client.cookies.set(sessions.COOKIE, token)
    assert client.get('/auth/me').status_code == 401
    login(browser)
    db.sessions.update_many({}, {'$set': {'expires_at': datetime.now(timezone.utc) - timedelta(seconds=1)}})
    assert client.get('/auth/me').status_code == 401


@pytest.mark.parametrize('origin', [None, 'https://evil.example', 'http://localhost:9999'])
def test_login_and_logout_reject_missing_or_untrusted_origins(browser, origin):
    client, _ = browser
    headers = {'Origin': origin} if origin else {}
    assert client.post('/auth/session', headers=headers, data={'username': 'a', 'password': 'b'}).status_code == 403
    login(browser)
    assert client.post('/auth/logout', headers=headers).status_code == 403


def test_cookie_write_checks_origin_and_secure_on_https(browser):
    client, _ = browser
    login(browser)
    from starlette.requests import Request
    cookie = client.cookies.get(sessions.COOKIE)
    request = Request({'type': 'http', 'method': 'POST', 'headers': [(b'cookie', f'{sessions.COOKIE}={cookie}'.encode())]})
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        sessions.resolve(request)
    assert error.value.status_code == 403
    client.base_url = 'https://testserver'
    response = login(browser)
    assert 'Secure' in response.headers['set-cookie']


def test_validation_does_not_echo_credentials():
    client = TestClient(app)
    secret = 'sensitive-short'
    response = client.post('/auth/google-session', json={'credential': secret})
    assert response.status_code == 422 and secret not in response.text


def test_access_log_drops_query_values():
    import logging
    from backend.app.log_privacy import AccessPathFilter
    record = logging.LogRecord('uvicorn.access', logging.INFO, '', 0, '%s %s %s %s %s',
                               ('local', 'GET', '/tts?text=private&token=secret', '1.1', 200), None)
    AccessPathFilter().filter(record)
    assert 'private' not in record.getMessage() and 'secret' not in record.getMessage()


@pytest.mark.parametrize('payload', [{'sub': 'patient@example.test'}, {'sub': 'patient@example.test', 'exp': 1}])
def test_missing_or_expired_jwt_rejected(browser, payload):
    import jwt
    client, _ = browser
    token = jwt.encode(payload, 'test-key-that-is-long-enough-for-signing', algorithm='HS256')
    assert client.get('/auth/me', headers={'Authorization': f'Bearer {token}'}).status_code == 401
