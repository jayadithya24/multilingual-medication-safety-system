from datetime import datetime, timedelta, timezone
import csv
from pathlib import Path

import mongomock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app import browser_sessions, login_limits
from backend.app.request_limits import RequestLimits
from backend.main import app as real_app
from tools.deploy_preflight import check


def test_many_accounts_still_share_heavy_source_cap(monkeypatch):
    store = mongomock.MongoClient().test.sessions
    monkeypatch.setattr(browser_sessions, 'sessions', store)
    now = datetime.now(timezone.utc)
    for i in range(61):
        store.insert_one({'username': str(i), 'digest': browser_sessions.digest(str(i)),
                          'expires_at': now + timedelta(minutes=10),
                          'absolute_expires_at': now + timedelta(hours=1)})
    app = FastAPI()
    app.add_middleware(RequestLimits)
    @app.get('/voice-search')
    def work():
        return {'ok': True}
    client = TestClient(app)
    for i in range(60):
        assert client.get('/voice-search', headers={'Cookie': f'mmss_session={i}'}).status_code == 200
    # Source rejection occurs before even performing a cookie lookup.
    monkeypatch.setattr(RequestLimits, 'identity', lambda *args: pytest.fail('lookup after source cap'))
    response = client.get('/voice-search', headers={'Cookie': 'mmss_session=60'})
    assert response.status_code == 429


def test_creation_cap_shared_across_routes_workers_and_google_register(monkeypatch):
    from backend.app import database
    monkeypatch.setattr(database, 'db', mongomock.MongoClient().test)
    monkeypatch.setenv('RATE_LIMIT_BACKEND', 'mongo')
    def client():
        app = FastAPI()
        app.add_middleware(RequestLimits)
        @app.post('/auth/{kind}')
        def work(kind: str):
            return {'ok': True}
        return TestClient(app)
    first, second = client(), client()
    routes = ['/auth/register-session', '/auth/doctor-request', '/auth/register-doctor', '/auth/google-session']
    for i in range(30):
        assert (first if i % 2 else second).post(routes[i % 4], json={'mode': 'register'}).status_code == 200
    denied = first.post('/auth/google-session', json={'mode': 'register'})
    assert denied.status_code == 429 and int(denied.headers['retry-after']) > 0
    assert second.post('/auth/register-session').status_code == 429
    # Normal sign-in still works after account creation is exhausted.
    assert first.post('/auth/google-session', json={'mode': 'login'}).status_code == 200
    assert first.post('/auth/session').status_code == 200


def test_distributed_attempts_emit_monitoring_without_global_lock(monkeypatch, caplog):
    store = mongomock.MongoClient().test.attempts
    monkeypatch.setattr(login_limits, 'attempts', store)
    for i in range(34):
        assert login_limits.reserve('private@example.test', f'192.0.2.{i}')
    assert store.count_documents({'monitor_required': True}) == 1
    assert sum('distributed_login_threshold' in r.message for r in caplog.records) == 1
    assert 'private@example.test' not in caplog.text


def test_long_kannada_doctor_password_rejected_by_actual_route():
    value = 'ಕ' * 30
    response = TestClient(real_app).post('/auth/doctor-request', json={
        'name': 'Doctor', 'email': 'test@example.test', 'doctor_id': 'REG30',
        'specialization': 'General', 'password': value, 'confirm_password': value})
    assert response.status_code == 422
    assert value not in response.text


def test_preflight_requires_explicit_production(monkeypatch):
    monkeypatch.delenv('ENVIRONMENT', raising=False)
    monkeypatch.setenv('BROWSER_ORIGINS', 'https://clinic.example')
    monkeypatch.setenv('MONGO_URI', 'mongodb://test:password@example.invalid/test?tls=true')
    monkeypatch.setenv('FORWARDED_ALLOW_IPS', '127.0.0.1')
    monkeypatch.delenv('USE_MONGOMOCK', raising=False)
    monkeypatch.delenv('ENABLE_RESEARCH_ML_API', raising=False)
    assert any('ENVIRONMENT' in e for e in check())
    monkeypatch.setenv('ENVIRONMENT', 'production')
    assert check() == []
    monkeypatch.setenv('USE_MONGOMOCK', 'true')
    assert any('MONGOMOCK' in e for e in check())


@pytest.mark.parametrize('trusted', ['', '*', '127.0.0.1,*', '127.0.0.1,'])
def test_preflight_rejects_unsafe_proxy_trust(monkeypatch, trusted):
    monkeypatch.setenv('FORWARDED_ALLOW_IPS', trusted)
    assert any('FORWARDED_ALLOW_IPS' in e for e in check())


@pytest.mark.parametrize('uri', [
    'mongodb://test:password@example.invalid/test',
    'mongodb+srv://test:password@example.invalid/test?tls=false',
    'mongodb://test:password@example.invalid/test?tls=true&tlsAllowInvalidCertificates=true',
    'mongodb+srv://example.invalid/test',
])
def test_preflight_rejects_unsafe_mongo(monkeypatch, uri):
    monkeypatch.setenv('MONGO_URI', uri)
    assert any('MongoDB' in e for e in check())


def test_localized_export_matches_current_master_disease_names():
    root = Path(__file__).resolve().parents[1]
    with (root / 'datasets/tulu_master_dataset.csv').open(encoding='utf-8-sig') as stream:
        master = {r['drug_id']: r['disease'] for r in csv.DictReader(stream)}
    with (root / 'datasets/ml_ready/master_localized.csv').open(encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    tulu = [r for r in rows if r.get('language') == 'tulu']
    assert len(tulu) == 100
    assert all(r['disease'] == master[r['drug_id']] for r in tulu)
