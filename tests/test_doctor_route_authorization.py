"""Exercise real authentication dependencies, not an overridden identity."""
from datetime import datetime, timedelta, timezone
import mongomock
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from session_helpers import session_headers
from backend.app import auth
from backend.app.routes import access_requests as access, patient_drugs as doctor

PRIVATE_ROUTES = ['/doctor/patients/P1/medications', '/doctor/patients/patient/drugs',
                  '/doctor/patients/patient/report', '/doctor/patients/P1/regimen']
LIST_ROUTES = ['/doctor/patients', '/doctor/medication-history']


@pytest.mark.parametrize('route', PRIVATE_ROUTES + LIST_ROUTES)
@pytest.mark.parametrize('identity', ['anonymous', 'patient', 'no_consent', 'expired', 'revoked'])
def test_doctor_routes_fail_closed(monkeypatch, route, identity):
    db = mongomock.MongoClient().authorization
    monkeypatch.setattr(auth, 'users_collection', db.users)
    for module in (access, doctor):
        for name in ('users', 'access_requests', 'patient_schedules', 'medication_history'):
            monkeypatch.setattr(module, name + '_collection', db[name])
    monkeypatch.setattr(access, 'access_log_collection', db.access_log)
    db.users.insert_many([{'username': 'patient', 'patient_id': 'P1', 'role': 'patient'},
                          {'username': 'doctor', 'role': 'doctor'}])
    db.patient_schedules.insert_one({'patient_username': 'patient', 'medicine_name': 'PRIVATE MEDICINE'})
    db.medication_history.insert_one({'patient_username': 'patient', 'medicine_name': 'PRIVATE MEDICINE'})
    if identity in ('expired', 'revoked'):
        db.access_requests.insert_one({'doctorId': 'doctor', 'patientId': 'P1',
            'status': 'REVOKED' if identity == 'revoked' else 'ACCEPTED',
            'expiresAt': datetime.now(timezone.utc) + timedelta(days=1 if identity == 'revoked' else -1)})
    headers = {} if identity == 'anonymous' else session_headers('patient' if identity == 'patient' else 'doctor')
    response = TestClient(app).get(route, headers=headers)
    expected = 401 if identity == 'anonymous' else (403 if identity == 'patient' or route in PRIVATE_ROUTES else 200)
    assert response.status_code == expected
    assert 'PRIVATE MEDICINE' not in response.text
    if expected == 200:
        assert response.json().get('patients', response.json().get('history')) == []
