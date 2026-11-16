from datetime import datetime, timezone, timedelta
import mongomock
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app import auth
from backend.app.routes import access_requests as access, patient_drugs as doctor


@pytest.fixture
def setup(monkeypatch):
    db = mongomock.MongoClient().privacy
    for module in (access, doctor):
        for name in ("users", "access_requests", "patient_schedules", "medication_history"):
            monkeypatch.setattr(module, name + "_collection", db[name])
    for name in ("share_codes", "access_log", "consent_attempts"):
        monkeypatch.setattr(access, name + "_collection", db[name])
    db.users.insert_many([{"username": "patient", "patient_id": "P1", "role": "patient", "full_name": "Private name"},
        {"username": "other", "patient_id": "P2", "role": "patient"}])
    db.patient_schedules.insert_one({"patient_username": "patient", "medicine_name": "Example"})
    user = {"username": "patient", "role": "patient"}
    app.dependency_overrides[auth.get_current_active_user] = lambda: auth.User(**user)
    yield TestClient(app), db, user
    app.dependency_overrides.clear()


def request(client, user):
    user.update(username="patient", role="patient")
    code = client.post('/patient/share-code').json()['share_code']
    user.update(username="doctor", role="doctor")
    response = client.post('/doctor/access-request', json={"share_code": code})
    assert response.status_code == 200
    assert client.post('/doctor/access-request', json={"share_code": code}).status_code == 404
    return response.json()['request']['requestId']


def test_directory_consent_revoke_and_all_record_routes(setup):
    client, db, user = setup
    user.update(username="doctor", role="doctor")
    assert client.get('/doctor/patients').json()['patients'] == []
    assert client.post('/doctor/access-request', json={"patient_id": "P1"}).status_code == 422
    rid = request(client, user)
    routes = ['/doctor/patients/P1/medications', '/doctor/patients/patient/drugs', '/doctor/patients/patient/report']
    for route in routes:
        assert client.get(route).status_code == 403
    user.update(username="other", role="patient")
    assert client.put(f'/patient/access-request/{rid}/accept').status_code != 200
    user.update(username="patient")
    assert client.put(f'/patient/access-request/{rid}/accept').status_code == 200
    user.update(username="doctor", role="doctor")
    assert len(client.get('/doctor/patients').json()['patients']) == 1
    for route in routes:
        assert client.get(route).status_code == 200
    assert client.get(routes[-1]).json()['consent']['scope'] == 'medicines_and_history'
    user.update(username="patient", role="patient")
    assert client.get('/patient/access-log').json()['events']
    assert client.put(f'/patient/access-request/{rid}/revoke').status_code == 200
    user.update(username="doctor", role="doctor")
    assert client.get('/doctor/patients').json()['patients'] == []
    for route in routes:
        assert client.get(route).status_code == 403
    assert client.get('/doctor/medication-history').json()['history'] == []


def test_expiry_and_legacy_grants_fail_closed(setup):
    client, db, user = setup
    rid = request(client, user)
    user.update(username="patient", role="patient")
    client.put(f'/patient/access-request/{rid}/accept')
    db.access_requests.update_one({"requestId": rid}, {"$set": {"expiresAt": datetime.now(timezone.utc) - timedelta(seconds=1)}})
    assert client.get('/patient/access-requests').json()['requests'][0]['status'] == 'EXPIRED'
    user.update(username="doctor", role="doctor")
    for route in ('/doctor/patients/P1/medications', '/doctor/patients/patient/drugs', '/doctor/patients/patient/report'):
        assert client.get(route).status_code == 403
    assert client.get('/doctor/patients').json()['patients'] == []
    assert client.get('/doctor/medication-history').json()['history'] == []
    db.access_requests.update_one({"requestId": rid}, {"$unset": {"expiresAt": ""}})
    assert client.get('/doctor/patients/P1/medications').status_code == 403


def test_denied_access_logged_and_doctor_cannot_edit_log(setup):
    client, db, user = setup
    user.update(username="doctor", role="doctor")
    for route in ('/doctor/patients/P1/medications', '/doctor/patients/patient/drugs', '/doctor/patients/patient/report'):
        assert client.get(route).status_code == 403
    assert db.access_log.count_documents({'action': {'$regex': '^DENIED_'}}) == 3
    assert client.get('/patient/access-log').status_code == 403
    assert client.delete('/patient/access-log').status_code == 405
    user.update(username="patient", role="patient")
    assert len(client.get('/patient/access-log').json()['events']) == 3


def test_wrong_codes_are_limited_per_doctor(setup):
    client, db, user = setup
    user.update(username="doctor", role="doctor")
    for _ in range(10):
        assert client.post('/doctor/access-request', json={'share_code': '0' * 16}).status_code == 404
    assert client.post('/doctor/access-request', json={'share_code': '0' * 16}).status_code == 429
    user.update(username="another-doctor")
    assert client.post('/doctor/access-request', json={'share_code': '0' * 16}).status_code == 404


def test_only_patient_can_renew_existing_grant(setup):
    client, db, user = setup
    rid = request(client, user)
    assert client.put(f'/patient/access-request/{rid}/renew').status_code == 403
    user.update(username="patient", role="patient")
    client.put(f'/patient/access-request/{rid}/accept')
    db.access_requests.update_one({'requestId': rid}, {'$set': {'expiresAt': datetime.now(timezone.utc) + timedelta(hours=1)}})
    response = client.put(f'/patient/access-request/{rid}/renew')
    assert response.status_code == 200
    assert datetime.fromisoformat(response.json()['request']['expiresAt']) > datetime.now(timezone.utc) + timedelta(days=6)
    assert db.access_log.count_documents({'action': 'RENEWED'}) == 1


def test_expired_code_and_pending_request_cannot_grant_access(setup):
    client, db, user = setup
    code = client.post('/patient/share-code').json()['share_code']
    db.share_codes.update_many({}, {"$set": {"expiresAt": datetime.now(timezone.utc) - timedelta(seconds=1)}})
    user.update(username="doctor", role="doctor")
    assert client.post('/doctor/access-request', json={"share_code": code}).status_code == 404
    rid = request(client, user)
    db.access_requests.update_one({"requestId": rid}, {"$set": {"expiresAt": datetime.now(timezone.utc) - timedelta(seconds=1)}})
    user.update(username="patient", role="patient")
    assert client.put(f'/patient/access-request/{rid}/accept').status_code == 409


def test_coverage_distinguishes_catalog_from_pair_evidence(setup):
    client, _, _ = setup
    response = client.post('/interaction/multi', json={"drugs": ['Aspirin', 'Ibuprofen', 'Unknown medicine']})
    coverage = response.json()['coverage']
    assert coverage['total_medicines'] == 3
    assert coverage['covered_medicines'] == 2
    assert coverage['unsupported_medicines'] == ['unknown medicine']
    assert coverage['total_pairs'] == 3
    result = client.get('/interaction', params={"drug1": 'Aspirin', "drug2": 'Unknown medicine'}).json()
    assert result['interaction'] is None
    assert result['coverage']['covered_medicines'] == 1
