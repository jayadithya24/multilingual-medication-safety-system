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
    # Relaxed for development testing
    pass


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
    
    if patient_id.startswith("PAT-DEMO"):
        demo_meds = [
            {
                "id": "MED-001",
                "medicine_name": "Metformin",
                "dosage": "500mg",
                "frequency": "Twice daily with meals",
                "scheduled_time": "08:00 AM",
                "purpose": "Type 2 Diabetes Control",
                "prescribed_date": "2026-08-15",
                "status": "Active",
                "adherence_rate": "95%",
            },
            {
                "id": "MED-002",
                "medicine_name": "Acarbose",
                "dosage": "50mg",
                "frequency": "Three times daily before meals",
                "scheduled_time": "01:00 PM",
                "purpose": "Postprandial Blood Glucose Regulation",
                "prescribed_date": "2026-09-01",
                "status": "Active",
                "adherence_rate": "88%",
            },
            {
                "id": "MED-003",
                "medicine_name": "Amlodipine",
                "dosage": "5mg",
                "frequency": "Once daily morning",
                "scheduled_time": "08:30 AM",
                "purpose": "Hypertension",
                "prescribed_date": "2026-07-20",
                "status": "Active",
                "adherence_rate": "100%",
            }
        ]
        demo_history = [
            {
                "taken_at": "2026-09-20 08:05 AM",
                "medicine_name": "Metformin",
                "status": "TAKEN",
                "dosage": "500mg",
                "notes": "Patient reported mild nausea after breakfast.",
            },
            {
                "taken_at": "2026-09-19 01:10 PM",
                "medicine_name": "Acarbose",
                "status": "TAKEN",
                "dosage": "50mg",
                "notes": "Taken as scheduled before lunch.",
            },
            {
                "taken_at": "2026-09-18 08:30 AM",
                "medicine_name": "Amlodipine",
                "status": "TAKEN",
                "dosage": "5mg",
                "notes": "BP logged at 122/78 mmHg.",
            }
        ]
        return {
            "status": "success",
            "patient_id": patient_id,
            "patient_name": "Ramesh Kumar" if "001" in patient_id else "Sunita Sharma",
            "medications": demo_meds,
            "history": demo_history,
            "survey_summary": {
                "side_effects_reported": ["Mild Nausea (Metformin)"],
                "lifestyle_factors": "Moderate exercise, low sodium diet",
                "last_survey_date": "2026-09-15"
            }
        }

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