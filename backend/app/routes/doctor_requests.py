from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

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
    requests = doctor_requests_collection.find({"status": {"$in": ["pending", "approving"]}}).sort("created_at", -1)
    return {"requests": [public_request(item) for item in requests]}


@router.put("/{request_id}/approve")
async def approve_doctor_request(
    request_id: str,
    current_user: User = Depends(get_current_admin),
):
    # Commit the decision atomically before creating an account. Reject can only
    # win while pending; an interrupted approval stays visible and retryable.
    request = doctor_requests_collection.find_one_and_update(
        {"request_id": request_id, "status": "pending"},
        {"$set": {"status": "approving", "reviewed_at": datetime.now(timezone.utc), "reviewed_by": current_user.username}},
        return_document=ReturnDocument.AFTER,
    )
    if not request:
        request = doctor_requests_collection.find_one({"request_id": request_id, "status": {"$in": ["approving", "approved"]}})
    if not request:
        raise HTTPException(status_code=404, detail="Pending doctor request not found.")
    if request["status"] == "approved":
        return {"status": "approved", "request_id": request_id}

    email = request["email"].strip().lower()
    registration_number = request["medical_registration_no"].strip()

    existing = users_collection.find_one({"$or": [{"username": email}, {"email": email}]})
    if existing and existing.get("approval_request_id") != request_id:
        doctor_requests_collection.update_one({"request_id": request_id, "status": "approving"}, {"$set": {"status": "pending"}})
        raise HTTPException(status_code=409, detail="An account already exists for this email.")
    registered = users_collection.find_one({"license_number": registration_number})
    if registered and registered.get("approval_request_id") != request_id:
        doctor_requests_collection.update_one({"request_id": request_id, "status": "approving"}, {"$set": {"status": "pending"}})
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
        "approval_request_id": request_id,
    }
    try:
        users_collection.update_one({"username": email}, {"$setOnInsert": doctor}, upsert=True)
    except DuplicateKeyError:
        # A simultaneous retry may have completed the same idempotent upsert.
        existing = users_collection.find_one({"username": email, "approval_request_id": request_id})
        if not existing:
            doctor_requests_collection.update_one({"request_id": request_id, "status": "approving"}, {"$set": {"status": "pending"}})
            raise HTTPException(status_code=409, detail="A matching doctor account already exists.")
    account = users_collection.find_one({"username": email, "approval_request_id": request_id, "role": "doctor"})
    if not account:
        doctor_requests_collection.update_one({"request_id": request_id, "status": "approving"}, {"$set": {"status": "pending"}})
        raise HTTPException(status_code=409, detail="An account was created by another request. Administrator reconciliation is required.")

    doctor_requests_collection.update_one(
        {"request_id": request_id, "status": "approving"},
        {"$set": {"status": "approved"}},
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
