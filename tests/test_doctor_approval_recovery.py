import asyncio
from types import SimpleNamespace
import mongomock
import pytest
from fastapi import HTTPException
from backend.app.routes import doctor_requests as route


@pytest.fixture
def collections(monkeypatch):
    db = mongomock.MongoClient().recovery_test
    db.users.create_index("username", unique=True)
    db.users.create_index("license_number", unique=True, partialFilterExpression={"license_number": {"$type": "string"}})
    monkeypatch.setattr(route, "users_collection", db.users)
    monkeypatch.setattr(route, "doctor_requests_collection", db.requests)
    db.requests.insert_one({"request_id": "R1", "status": "pending", "email": "doctor@example.invalid",
                            "medical_registration_no": "REG1", "full_name": "Test Doctor",
                            "hashed_password": "test-hash", "specialization": "Test"})
    return db


def approve():
    return asyncio.run(route.approve_doctor_request("R1", SimpleNamespace(username="admin")))


def test_retry_after_account_created_but_status_write_failed(collections, monkeypatch):
    original = collections.requests.update_one
    def interrupt(query, update, **kwargs):
        if update.get("$set", {}).get("status") == "approved":
            raise RuntimeError("Simulated database interruption")
        return original(query, update, **kwargs)
    monkeypatch.setattr(collections.requests, "update_one", interrupt)
    with pytest.raises(RuntimeError):
        approve()
    assert collections.users.count_documents({}) == 1
    assert collections.requests.find_one({})["status"] == "approving"
    with pytest.raises(HTTPException):
        asyncio.run(route.reject_doctor_request("R1", SimpleNamespace(username="other-admin")))
    queue = asyncio.run(route.list_doctor_requests(SimpleNamespace(username="admin")))
    assert queue["requests"][0]["status"] == "approving"
    monkeypatch.setattr(collections.requests, "update_one", original)
    assert approve()["status"] == "approved"
    assert approve()["status"] == "approved"
    assert collections.users.count_documents({}) == 1


def test_rejection_wins_before_approval(collections):
    asyncio.run(route.reject_doctor_request("R1", SimpleNamespace(username="admin")))
    with pytest.raises(HTTPException):
        approve()
    assert collections.users.count_documents({}) == 0


def test_account_creation_conflict_does_not_overwrite_existing_user(collections):
    collections.users.insert_one({"username": "doctor@example.invalid", "role": "patient"})
    with pytest.raises(HTTPException) as error:
        approve()
    assert error.value.status_code == 409
    assert collections.users.find_one({})["role"] == "patient"
    assert collections.requests.find_one({})["status"] == "pending"
