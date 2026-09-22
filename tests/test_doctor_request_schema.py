import os

from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "a" * 32)
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB", "mmss_test")

from backend.app import auth as auth_module
from backend.app import database as database_module
from backend.app.auth import authenticate_user, get_password_hash
from backend.app.routes import auth as route_auth
from backend.app.routes import doctor_requests as doctor_requests_route
from backend.main import app

users_collection = database_module.users_collection

# Ensure the app-level auth modules use the same live collections as the project db.
auth_module.users_collection = database_module.users_collection
route_auth.users_collection = database_module.users_collection
route_auth.doctor_requests_collection = database_module.doctor_requests_collection
doctor_requests_route.users_collection = database_module.users_collection
doctor_requests_route.doctor_requests_collection = database_module.doctor_requests_collection

client = TestClient(app)


def test_doctor_request_accepts_legacy_camelcase_payload_fields():
    payload = {
        "name": "Dr Example",
        "email": "doc-camel@example.com",
        "phone": "1234567890",
        "medicalRegistrationNo": "DOC-LEGACY-001",
        "specialization": "Cardiology",
        "hospital": "City Hospital",
        "password": "secretpass",
        "confirmPassword": "secretpass",
    }

    response = client.post("/auth/doctor-request", json=payload)

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "pending"


def test_approved_doctor_can_login_with_normalized_email():
    database_module.users_collection.delete_many({})
    database_module.doctor_requests_collection.delete_many({})
    auth_module.users_collection = database_module.users_collection
    route_auth.users_collection = database_module.users_collection
    route_auth.doctor_requests_collection = database_module.doctor_requests_collection
    doctor_requests_route.users_collection = database_module.users_collection
    doctor_requests_route.doctor_requests_collection = database_module.doctor_requests_collection

    admin_email = "admin@example.com"
    admin_password = "AdminPass123!"
    users_collection.insert_one({
        "username": admin_email,
        "email": admin_email,
        "role": "admin",
        "full_name": "Admin",
        "hashed_password": get_password_hash(admin_password),
        "disabled": False,
    })

    payload = {
        "name": "Dr Example",
        "email": "Doc.Login@Example.com",
        "phone": "1234567890",
        "medicalRegistrationNo": "DOC-APPROVED-001",
        "specialization": "Cardiology",
        "hospital": "City Hospital",
        "password": "DoctorPass123!",
        "confirmPassword": "DoctorPass123!",
    }

    request_response = client.post("/auth/doctor-request", json=payload)
    request_id = request_response.json()["request_id"]

    admin_login = client.post("/auth/token", data={"username": admin_email, "password": admin_password})
    admin_token = admin_login.json()["access_token"]

    approval_response = client.put(
        f"/admin/doctor-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert approval_response.status_code == 200, approval_response.text
    approved_user = users_collection.find_one({"$or": [{"username": "doc.login@example.com"}, {"email": "doc.login@example.com"}]})
    assert approved_user is not None
    assert approved_user["role"] == "doctor"
    assert approved_user["email"] == "doc.login@example.com"
    assert authenticate_user({}, "Doc.Login@Example.com", "DoctorPass123!") is not False

    login_response = client.post("/auth/token", data={"username": "Doc.Login@Example.com", "password": "DoctorPass123!"})
    assert login_response.status_code == 200, login_response.text
    assert login_response.json()["role"] == "doctor"
