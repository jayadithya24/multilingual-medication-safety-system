from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.auth import User, get_current_active_user
from backend.app.database import (
    access_requests_collection,
    patient_schedules_collection,
    users_collection,
)


router = APIRouter(tags=["medication access"])


class AccessRequestCreate(BaseModel):
    patient_id: str = Field(..., min_length=1)


def require_role(current_user: User, role: str) -> None:
    if not current_user or not getattr(current_user, "role", None):
        raise HTTPException(status_code=401, detail="Authentication required.")
    if current_user.role != role:
        raise HTTPException(status_code=403, detail=f"Only {role} accounts can access this endpoint.")


def public_request(request: dict) -> dict:
    request.pop("_id", None)
    return request


def get_patient_by_id(patient_id: str) -> dict:
    patient = users_collection.find_one({"patient_id": patient_id, "role": "patient"})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return patient


def has_accepted_access(doctor_id: str, patient_id: str) -> bool:
    return access_requests_collection.find_one({
        "doctorId": doctor_id,
        "patientId": patient_id,
        "status": "ACCEPTED",
    }) is not None


@router.post("/doctor/access-request")
async def create_access_request(
    payload: AccessRequestCreate,
    current_user: User = Depends(get_current_active_user),
):
    require_role(current_user, "doctor")
    patient = get_patient_by_id(payload.patient_id)
    patient_id = patient["patient_id"]

    existing = access_requests_collection.find_one({
        "doctorId": current_user.username,
        "patientId": patient_id,
        "status": "PENDING",
    })
    if existing:
        return {"status": "success", "request": public_request(existing)}

    request = {
        "requestId": f"AR-{uuid4().hex[:12].upper()}",
        "doctorId": current_user.username,
        "patientId": patient_id,
        "patientName": patient.get("full_name", "Patient"),
        "doctorName": current_user.full_name or current_user.username,
        "status": "PENDING",
        "createdAt": datetime.now(timezone.utc),
        "respondedAt": None,
    }
    access_requests_collection.insert_one(request)
    return {"status": "success", "request": public_request(request)}


@router.get("/patient/access-requests")
async def get_patient_access_requests(current_user: User = Depends(get_current_active_user)):
    require_role(current_user, "patient")
    patient = users_collection.find_one({"username": current_user.username, "role": "patient"})
    requests = list(access_requests_collection.find(
        {"patientId": patient.get("patient_id") if patient else None}
    ).sort("createdAt", -1))
    return {"status": "success", "requests": [public_request(item) for item in requests]}


async def respond_to_request(request_id: str, decision: str, current_user: User):
    require_role(current_user, "patient")
    patient = users_collection.find_one({"username": current_user.username, "role": "patient"})
    request = access_requests_collection.find_one({
        "requestId": request_id,
        "patientId": patient.get("patient_id") if patient else None,
    })
    if not request:
        raise HTTPException(status_code=404, detail="Access request not found.")
    if request["status"] != "PENDING":
        raise HTTPException(status_code=409, detail="Access request has already been answered.")

    access_requests_collection.update_one(
        {"requestId": request_id, "patientId": patient["patient_id"], "status": "PENDING"},
        {"$set": {"status": decision, "respondedAt": datetime.now(timezone.utc)}},
    )
    updated = access_requests_collection.find_one({"requestId": request_id})
    return {"status": "success", "request": public_request(updated)}


@router.put("/patient/access-request/{request_id}/accept")
async def accept_access_request(request_id: str, current_user: User = Depends(get_current_active_user)):
    return await respond_to_request(request_id, "ACCEPTED", current_user)


@router.put("/patient/access-request/{request_id}/reject")
async def reject_access_request(request_id: str, current_user: User = Depends(get_current_active_user)):
    return await respond_to_request(request_id, "REJECTED", current_user)


@router.get("/doctor/access-requests")
async def get_doctor_access_requests(current_user: User = Depends(get_current_active_user)):
    require_role(current_user, "doctor")
    requests = list(access_requests_collection.find({"doctorId": current_user.username}).sort("createdAt", -1))
    return {"status": "success", "requests": [public_request(item) for item in requests]}


@router.get("/doctor/patients/{patient_id}/medications")
async def get_patient_medications(
    patient_id: str,
    current_user: User = Depends(get_current_active_user),
):
    require_role(current_user, "doctor")
    
    patient = get_patient_by_id(patient_id)
    if not has_accepted_access(current_user.username, patient["patient_id"]):
        raise HTTPException(status_code=403, detail="Patient medication access has not been accepted.")

    medications = list(patient_schedules_collection.find(
        {"patient_username": patient["username"]}
    ).sort("scheduled_time", 1))
    for medication in medications:
        medication.pop("_id", None)
    return {"status": "success", "patient_id": patient["patient_id"], "medications": medications}


__all__ = ["has_accepted_access"]
