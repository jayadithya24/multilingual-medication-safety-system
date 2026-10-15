import mongomock
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app import auth, database
from backend.app.routes import access_requests, patient_drugs


@pytest.fixture
def client(monkeypatch):
    db = mongomock.MongoClient().portal_review
    for module in (auth, access_requests, patient_drugs):
        monkeypatch.setattr(module, "users_collection", db.users)
    for module in (access_requests, patient_drugs):
        monkeypatch.setattr(module, "access_requests_collection", db.access_requests)
    monkeypatch.setattr(access_requests, "patient_schedules_collection", db.schedules)
    app.dependency_overrides[auth.get_current_active_user] = lambda: auth.User(username="review-doctor", role="doctor")
    try:
        yield TestClient(app), db
    finally:
        app.dependency_overrides.clear()


def test_non_admin_cannot_import_database(client):
    browser, _ = client
    response = browser.post("/admin/load-mongo", json={})
    assert response.status_code == 403


def test_empty_patient_directory_does_not_invent_patients(client):
    browser, _ = client
    assert browser.get("/doctor/patients").json()["patients"] == []


def test_demo_style_patient_id_cannot_bypass_consent(client):
    browser, db = client
    db.users.insert_one({"username": "real-patient", "patient_id": "PAT-DEMO-001", "role": "patient"})
    response = browser.get("/doctor/patients/PAT-DEMO-001/medications")
    assert response.status_code == 403


def test_legacy_demo_credentials_are_not_valid_accounts(client):
    browser, _ = client
    for username in ("doctor", "patient"):
        assert browser.post("/auth/token", data={"username": username, "password": "secret"}).status_code == 401


def test_explicit_mock_mode_never_attempts_real_mongo(monkeypatch):
    monkeypatch.setattr(database, "USE_MONGOMOCK", True)
    def forbidden(*args, **kwargs):
        raise AssertionError("Tests must not contact the real database")
    monkeypatch.setattr(database, "MongoClient", forbidden)
    client, _ = database._get_database_client()
    assert isinstance(client, mongomock.MongoClient)


def test_real_mongo_failure_does_not_fall_back_to_ephemeral_storage(monkeypatch):
    monkeypatch.setattr(database, "USE_MONGOMOCK", False)
    monkeypatch.setattr(database, "MONGO_URI", "mongodb://localhost:27017")
    def offline(*args, **kwargs):
        raise RuntimeError("database offline")
    monkeypatch.setattr(database, "MongoClient", offline)
    with pytest.raises(RuntimeError, match="database offline"):
        database._get_database_client()
