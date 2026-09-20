from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError

from backend.app.auth import User, get_current_admin
from backend.app.database import doctor_requests_collection, users_collection


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
    if users_collection.find_one({"username": request["email"]}):
        raise HTTPException(status_code=409, detail="An account already exists for this email.")
    if users_collection.find_one({"license_number": request["medical_registration_no"]}):
        raise HTTPException(status_code=409, detail="A doctor account already uses this registration number.")

    doctor = {
        "username": request["email"],
        "full_name": request["full_name"],
        "email": request["email"],
        "role": "doctor",
        "hashed_password": request["hashed_password"],
        "doctor_id": f"DR-{uuid4().hex[:10].upper()}",
        "specialization": request["specialization"],
        "license_number": request["medical_registration_no"],
        "phone": request.get("phone"),
        "hospital": request.get("hospital"),
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