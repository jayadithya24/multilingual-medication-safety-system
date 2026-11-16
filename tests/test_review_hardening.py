import io
from datetime import datetime, timedelta, timezone
import mongomock
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from backend.main import app
from backend.app import auth, browser_sessions, database
from backend.app.routes import access_requests as access, patient_drugs as doctor, upload
from session_helpers import session_headers, ORIGIN


@pytest.mark.parametrize('path', ['/auth/token', '/auth/patient-token', '/auth/register', '/auth/google'])
def test_old_bearer_endpoints_are_absent(path):
    assert TestClient(app).post(path, json={}).status_code == 404


def test_previously_valid_bearer_is_not_accepted():
    assert TestClient(app).get('/auth/me', headers={'Authorization': 'Bearer arbitrary-old-token'}).status_code == 401


def test_health_disclosure_requires_admin(monkeypatch):
    db = mongomock.MongoClient().private_health
    monkeypatch.setattr(auth, 'users_collection', db.users)
    db.users.insert_many([{'username': 'p', 'role': 'patient'}, {'username': 'a', 'role': 'admin'}])
    client = TestClient(app)
    assert client.get('/health').json() == {'status': 'running'}
    assert client.get('/admin/health').status_code == 401
    assert client.get('/admin/health', headers=session_headers('p')).status_code == 403
    assert 'firebase_admin_ready' in client.get('/admin/health', headers=session_headers('a')).json()


@pytest.mark.parametrize('path', ['/upload-image', '/prescription-ocr'])
@pytest.mark.parametrize('name,contents,status', [('bad.exe', b'x', 415), ('fake.jpg', b'not an image', 415)])
def test_reject_bad_upload_before_ocr(monkeypatch, path, name, contents, status):
    def forbidden(*args):
        raise AssertionError('OCR must not be invoked')
    monkeypatch.setattr(upload, 'extract_text', forbidden)
    monkeypatch.setattr(upload, 'extract_prescription_details', forbidden)
    assert TestClient(app).post(path, files={'file': (name, contents, 'image/jpeg')}).status_code == status


def test_image_dimensions_and_extension_checked(monkeypatch):
    from backend.app import image_validation
    from fastapi import HTTPException
    image = io.BytesIO()
    Image.new('RGB', (10, 10)).save(image, format='PNG')
    assert image_validation.validate_image('x.png', image.getvalue()) == '.png'
    with pytest.raises(HTTPException) as error:
        image_validation.validate_image('x.jpg', image.getvalue())
    assert error.value.status_code == 415
    monkeypatch.setattr(image_validation, 'MAX_PIXELS', 50)
    with pytest.raises(HTTPException) as error:
        image_validation.validate_image('x.png', image.getvalue())
    assert error.value.status_code == 413


def test_session_activity_slides_but_never_beyond_absolute_expiry(monkeypatch):
    from starlette.requests import Request
    store = mongomock.MongoClient().sliding.sessions
    monkeypatch.setattr(browser_sessions, 'sessions', store)
    headers = session_headers('person')
    record = store.find_one()
    now = datetime.now(timezone.utc)
    absolute = now + timedelta(minutes=5)
    store.update_one({'_id': record['_id']}, {'$set': {'expires_at': now + timedelta(seconds=10), 'absolute_expires_at': absolute}})
    request = Request({'type': 'http', 'method': 'GET', 'path': '/patient/profile', 'headers': [(b'cookie', headers['Cookie'].encode())]})
    assert browser_sessions.resolve(request) == 'person'
    row = store.find_one()
    assert abs((row['expires_at'].replace(tzinfo=timezone.utc) - absolute).total_seconds()) < .01
    store.update_one({'_id': record['_id']}, {'$set': {'absolute_expires_at': now - timedelta(seconds=1)}})
    assert browser_sessions.resolve(request) is None


def test_account_source_limit_does_not_lock_other_networks(monkeypatch):
    from backend.app import login_limits
    monkeypatch.setattr(login_limits, 'attempts', mongomock.MongoClient().limits.attempts)
    for _ in range(8):
        login_limits.reserve(' User@Example.test ', '192.0.2.1')
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        login_limits.reserve('user@example.test', '192.0.2.1')
    assert error.value.status_code == 429
    assert login_limits.reserve('user@example.test', '192.0.2.2')
    assert login_limits.reserve('different@example.test')


def test_production_rejects_mock_database(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.setattr(database, 'USE_MONGOMOCK', True)
    with pytest.raises(RuntimeError, match='in-memory'):
        database._get_database_client()


def test_log_dedup_and_security_pagination(monkeypatch):
    db = mongomock.MongoClient().logs
    monkeypatch.setattr(access, 'access_log_collection', db.logs)
    monkeypatch.setattr(access, 'users_collection', db.users)
    db.users.insert_one({'username': 'patient', 'role': 'patient', 'patient_id': 'P1'})
    for _ in range(3):
        access.log_access('doctor', 'P1', 'VIEW_HISTORY')
        access.log_access('doctor', 'P1', 'DENIED_VIEW_HISTORY')
    assert db.logs.count_documents({'category': 'read'}) == 1
    assert db.logs.count_documents({'category': 'security'}) == 1
    access.log_access('doctor', 'P1', 'REQUESTED')
    access.log_access('doctor', 'P1', 'REVOKED')
    app.dependency_overrides[auth.get_current_active_user] = lambda: auth.User(username='patient', role='patient')
    try:
        client = TestClient(app)
        first = client.get('/patient/access-log', params={'category': 'security', 'limit': 2}).json()
        second = client.get('/patient/access-log', params={'category': 'security', 'limit': 2, 'cursor': first['next_cursor']}).json()
        assert len(first['events']) == 2 and len(second['events']) == 1 and second['next_cursor'] is None
        assert client.get('/patient/access-log', params={'cursor': '2026-01-01|invalid'}).status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_report_uses_same_consent_snapshot(monkeypatch):
    db = mongomock.MongoClient().report_race
    for module in (doctor, access):
        for name in ('users', 'access_requests', 'patient_schedules', 'medication_history'):
            monkeypatch.setattr(module, name + '_collection', db[name])
    monkeypatch.setattr(access, 'access_log_collection', db.logs)
    db.users.insert_one({'username': 'patient', 'patient_id': 'P1', 'role': 'patient'})
    db.access_requests.insert_one({'doctorId': 'doctor', 'patientId': 'P1', 'status': 'ACCEPTED',
        'scope': 'medicines_and_history', 'expiresAt': datetime.now(timezone.utc) + timedelta(days=1)})
    original = access.authorize_access
    def revoke_after_authorization(*args):
        grant = original(*args)
        db.access_requests.delete_many({})
        return grant
    monkeypatch.setattr(doctor, 'authorize_access', revoke_after_authorization)
    report = doctor.get_patient_report('patient', auth.User(username='doctor', role='doctor'))
    assert report['consent']['scope'] == 'medicines_and_history'
