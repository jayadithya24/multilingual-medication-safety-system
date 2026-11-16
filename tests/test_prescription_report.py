from types import SimpleNamespace
from datetime import datetime, timezone, timedelta

import mongomock
import pytest
from fastapi import HTTPException

from backend.app.routes import patient_drugs as routes
from backend.app.routes import access_requests


@pytest.fixture
def report_data(monkeypatch):
    db = mongomock.MongoClient().db
    for name in ("users", "patient_schedules", "medication_history"):
        monkeypatch.setattr(routes, name + "_collection", db[name])
    for module in (routes, access_requests):
        monkeypatch.setattr(module, "access_requests_collection", db.access_requests)
    monkeypatch.setattr(access_requests, "access_log_collection", db.access_log)
    db.access_requests.insert_one({"requestId": "R1", "doctorId": "doctor", "patientId": "P1", "status": "ACCEPTED",
        "respondedAt": datetime.now(timezone.utc), "expiresAt": datetime.now(timezone.utc) + timedelta(days=7), "scope": "medicines_and_history"})
    db.users.insert_one({"username": "patient", "patient_id": "P1", "role": "patient", "hashed_password": "secret", "full_name": "Test Patient"})
    return db


def test_report_includes_prescriptions_without_taken_doses(report_data):
    report_data.patient_schedules.insert_many([
        {"patient_username": "patient", "medicine_name": "Example", "dosage": "test dose", "frequency": "daily", "instructions": "Saved instructions", "status": "active"},
        {"patient_username": "patient", "medicine_name": "Older", "status": "removed"},
        {"patient_username": "other", "medicine_name": "Private"},
    ])
    result = routes.get_patient_report("patient", SimpleNamespace(role="doctor", username="doctor"))
    assert len(result["prescriptions"]) == 2
    assert result["prescriptions"][0]["instructions"] == "Saved instructions"
    assert result["history"] == []
    assert "hashed_password" not in result["patient"]
    assert all("_id" not in item for item in result["prescriptions"])


@pytest.mark.parametrize("role,username", [("patient", "doctor"), ("doctor", "unapproved")])
def test_report_requires_doctor_and_consent(report_data, role, username):
    with pytest.raises(HTTPException) as error:
        routes.get_patient_report("patient", SimpleNamespace(role=role, username=username))
    assert error.value.status_code == 403
