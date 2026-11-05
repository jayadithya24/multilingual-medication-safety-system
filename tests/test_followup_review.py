from datetime import datetime, timedelta, timezone
import hashlib

import mongomock
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app import auth, browser_sessions
from backend.app.origin_config import browser_origins
from backend.app.request_limits import RequestLimits
from backend.app.routes.auth import RegisterRequest, DoctorRegisterRequest


@pytest.mark.parametrize('model', [RegisterRequest, DoctorRegisterRequest])
def test_registration_rejects_overlong_kannada_password(model):
    fields = dict(name='Example', email='person@example.test', password='ಕ' * 25,
                  confirm_password='ಕ' * 25, doctor_id='DOC01', specialization='General')
    with pytest.raises(ValidationError):
        model(**fields)
    fields.update(password='ಕ' * 24, confirm_password='ಕ' * 24)
    valid = model(**fields)
    assert auth.verify_password(valid.password, auth.get_password_hash(valid.password))
    with pytest.raises(ValueError, match='72'):
        auth.get_password_hash('ಕ' * 25)


@pytest.mark.parametrize('value', ['', ' ', 'http://localhost:5173', 'https://good.test,http://bad.test',
                                  'https://good.test/path', 'https://*.test'])
def test_production_requires_explicit_https_origins(monkeypatch, value):
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.setenv('BROWSER_ORIGINS', value)
    with pytest.raises(RuntimeError):
        browser_origins()


def test_production_origin_whitespace_normalized(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.setenv('BROWSER_ORIGINS', ' https://clinic.example , https://admin.example ')
    assert browser_origins() == ('https://clinic.example', 'https://admin.example')


@pytest.mark.parametrize('path', ['/patient-schedule', '/patient/profile', '/doctor/access-request'])
def test_body_cap_on_private_routes_before_handler(path):
    app = FastAPI()
    app.add_middleware(RequestLimits)
    @app.post(path)
    async def handler(request: Request):
        return {'size': len(await request.body())}
    client = TestClient(app)
    assert client.post(path, content=b'x', headers={'Content-Length': '65537'}).status_code == 413
    assert client.post(path, content=(b'x' * 1024 for _ in range(65))).status_code == 413
    assert client.post(path, content=b'{}').status_code == 200


def test_signed_in_users_behind_same_ip_have_independent_limits(monkeypatch):
    store = mongomock.MongoClient().test.sessions
    monkeypatch.setattr(browser_sessions, 'sessions', store)
    now = datetime.now(timezone.utc)
    for user in ('one', 'two'):
        store.insert_one({'username': user, 'digest': hashlib.sha256(user.encode()).hexdigest(),
                          'expires_at': now + timedelta(minutes=10),
                          'absolute_expires_at': now + timedelta(hours=1)})
    app = FastAPI()
    app.add_middleware(RequestLimits)
    @app.get('/voice-search')
    def handler():
        return {'ok': True}
    client = TestClient(app)
    for _ in range(20):
        assert client.get('/voice-search', headers={'Cookie': 'mmss_session=one'}).status_code == 200
    assert client.get('/voice-search', headers={'Cookie': 'mmss_session=one'}).status_code == 429
    assert client.get('/voice-search', headers={'Cookie': 'mmss_session=two'}).status_code == 200
    # Invalid cookies cannot manufacture authenticated quota buckets.
    for n in range(20):
        assert client.get('/voice-search', headers={'Cookie': f'mmss_session=invalid{n}'}).status_code == 200
    assert client.get('/voice-search', headers={'Cookie': 'mmss_session=another-invalid'}).status_code == 429
    assert store.find_one({'username': 'one'})['expires_at'].replace(tzinfo=timezone.utc) <= now + timedelta(minutes=10)
