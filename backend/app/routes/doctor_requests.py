from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError

from backend.app.auth import User, get_current_admin
from backend.app.database import doctor_requests_collection as mongo_doctor_requests_collection, users_collection as mongo_users_collection

users_collection = mongo_users_collection
doctor_requests_collection = mongo_doctor_requests_collection


router = APIRouter(prefix="/admin/doctor-requests", tags=["admin doctor requests"])


def public_request(request: dict) -> dict:
    request.pop("_id", None)
    request.pop("hashed_password", None)
    return request


@router.get("")
async def list_doctor_requests(current_user: User = Depends(get_current_admin)):
    requests = doctor_requests_collection.find({"status": "pending"}).sort("created_at", -1)
    return {"requests": [public_request(item) for item in requests]}


@router.put("/{request_id}/approve")
async def approve_doctor_request(
    request_id: str,
    current_user: User = Depends(get_current_admin),
):
    request = doctor_requests_collection.find_one({"request_id": request_id, "status": "pending"})
    if not request:
        raise HTTPException(status_code=404, detail="Pending doctor request not found.")

    email = request["email"].strip().lower()
    registration_number = request["medical_registration_no"].strip()

    if users_collection.find_one({"$or": [{"username": email}, {"email": email}]}):
        raise HTTPException(status_code=409, detail="An account already exists for this email.")
    if users_collection.find_one({"license_number": registration_number}):
        raise HTTPException(status_code=409, detail="A doctor account already uses this registration number.")

    doctor = {
        "username": email,
        "full_name": request["full_name"].strip(),
        "email": email,
        "role": "doctor",
        "hashed_password": request["hashed_password"],
        "doctor_id": f"DR-{uuid4().hex[:10].upper()}",
        "specialization": request["specialization"].strip(),
        "license_number": registration_number,
        "phone": request.get("phone").strip() if request.get("phone") else None,
        "hospital": request.get("hospital").strip() if request.get("hospital") else None,
        "disabled": False,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        users_collection.insert_one(doctor)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="A matching doctor account already exists.")

    doctor_requests_collection.update_one(
        {"request_id": request_id, "status": "pending"},
        {"$set": {"status": "approved", "reviewed_at": datetime.now(timezone.utc), "reviewed_by": current_user.username}},
    )
    return {"status": "approved", "request_id": request_id}


@router.put("/{request_id}/reject")
async def reject_doctor_request(
    request_id: str,
    current_user: User = Depends(get_current_admin),
):
    result = doctor_requests_collection.update_one(
        {"request_id": request_id, "status": "pending"},
        {"$set": {"status": "rejected", "reviewed_at": datetime.now(timezone.utc), "reviewed_by": current_user.username}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Pending doctor request not found.")
    return {"status": "rejected", "request_id": request_id}
