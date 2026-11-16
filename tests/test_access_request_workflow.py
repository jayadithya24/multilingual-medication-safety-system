import os
from datetime import timedelta

import mongomock

os.environ.setdefault("JWT_SECRET_KEY", "a" * 32)
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB", "mmss_test")

import backend.app.database as database_module
import backend.app.auth as auth_module
import backend.app.routes.access_requests as access_requests_module
from backend.main import app
from fastapi.testclient import TestClient


database_module.client = mongomock.MongoClient()
database_module.db = database_module.client[os.environ["MONGO_DB"]]
database_module.users_collection = database_module.db["users"]
database_module.doctor_requests_collection = database_module.db["doctor_requests"]
database_module.patient_schedules_collection = database_module.db["patient_schedules"]
database_module.medication_history_collection = database_module.db["medication_history"]
database_module.access_requests_collection = database_module.db["access_requests"]
database_module.fcm_tokens_collection = database_module.db["fcm_tokens"]
database_module.reminder_deliveries_collection = database_module.db["reminder_deliveries"]

auth_module.users_collection = database_module.users_collection
access_requests_module.users_collection = database_module.users_collection
access_requests_module.access_requests_collection = database_module.access_requests_collection


client = TestClient(app)


from session_helpers import session_headers


def _share_code(patient_headers):
    response = client.post("/patient/share-code", headers=patient_headers)
    assert response.status_code == 200, response.text
    return response.json()["share_code"]


def setup_function():
    database_module.users_collection.delete_many({})
    database_module.access_requests_collection.delete_many({})

    database_module.users_collection.insert_one({
        "username": "doctor@example.com",
        "full_name": "Dr. Smith",
        "email": "doctor@example.com",
        "role": "doctor",
        "hashed_password": auth_module.get_password_hash("secret"),
        "doctor_id": "DR-001",
        "specialization": "General Medicine",
        "hospital": "City General Hospital",
    })

    database_module.users_collection.insert_one({
        "username": "patient@example.com",
        "full_name": "Patient User",
        "email": "patient@example.com",
        "role": "patient",
        "hashed_password": auth_module.get_password_hash("secret"),
        "patient_id": "P-100",
    })


def test_doctor_request_and_patient_approval_workflow():
    doctor_headers = session_headers("doctor@example.com")
    patient_headers = session_headers("patient@example.com")

    response = client.post(
        "/doctor/access-request",
        json={"share_code": _share_code(patient_headers)},
        headers=doctor_headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "success"
    request_id = payload["request"]["requestId"]

    pending = client.get("/patient/access-requests", headers=patient_headers)
    assert pending.status_code == 200, pending.text
    assert len(pending.json()["requests"]) == 1
    assert pending.json()["requests"][0]["status"] == "PENDING"

    accepted = client.put(f"/patient/access-request/{request_id}/accept", headers=patient_headers)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["request"]["status"] == "ACCEPTED"

    approved = client.get("/doctor/patients/P-100/medications", headers=doctor_headers)
    assert approved.status_code == 200, approved.text
    assert access_requests_module.has_accepted_access("doctor@example.com", "P-100") is True


def test_rejection_block_access_and_pending_status_is_respected():
    doctor_headers = session_headers("doctor@example.com")
    patient_headers = session_headers("patient@example.com")

    response = client.post(
        "/doctor/access-request",
        json={"share_code": _share_code(patient_headers)},
        headers=doctor_headers,
    )
    request_id = response.json()["request"]["requestId"]

    rejected = client.put(f"/patient/access-request/{request_id}/reject", headers=patient_headers)
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["request"]["status"] == "REJECTED"

    blocked = client.get("/doctor/patients/P-100/medications", headers=doctor_headers)
    assert blocked.status_code == 403, blocked.text
    assert blocked.json()["detail"] == "Patient access is not authorized."
    unknown = client.get("/doctor/patients/P-DOES-NOT-EXIST/medications", headers=doctor_headers)
    assert unknown.status_code == 403
    assert unknown.json() == blocked.json()

    pending_response = client.get("/patient/access-requests", headers=patient_headers)
    assert pending_response.status_code == 200
    assert pending_response.json()["requests"][0]["status"] == "REJECTED"
