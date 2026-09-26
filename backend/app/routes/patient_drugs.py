from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from backend.app.auth import get_current_active_user
from backend.app.database import (
    access_requests_collection,
    users_collection,
    patient_schedules_collection,
    medication_history_collection,
)
from backend.app.routes.access_requests import has_accepted_access


router = APIRouter(
    prefix="/doctor",
    tags=["doctor patient drugs"]
)


def require_doctor(current_user):
    if not current_user or not getattr(current_user, "role", None):
        raise HTTPException(status_code=401, detail="Authentication required.")
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctor accounts can access this endpoint.")


@router.get("/patients/{patient_username}/report")
def get_patient_report(patient_username: str, current_user=Depends(get_current_active_user)):
    require_doctor(current_user)
    patient = users_collection.find_one({"username": patient_username, "role": "patient"})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    if not has_accepted_access(current_user.username, patient.get("patient_id")):
        raise HTTPException(status_code=403, detail="Patient medication access has not been accepted.")

    def records(collection, sort_field):
        result = list(collection.find({"patient_username": patient_username}, {"_id": 0}).sort(sort_field, -1))
        for record in result:
            for key, value in record.items():
                if isinstance(value, datetime):
                    record[key] = (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).isoformat()
        return result

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "doctor": current_user.username,
        "patient": {key: patient.get(key) for key in (
            "username", "patient_id", "full_name", "age", "gender", "medical_condition"
        )},
        "prescriptions": records(patient_schedules_collection, "created_at"),
        "history": records(medication_history_collection, "taken_at"),
    }


@router.get("/patients")
async def get_patients(
    current_user=Depends(get_current_active_user)
):
    require_doctor(current_user)

    # Patient identity and consent state are the only data shown before approval.
    patients = list(
        users_collection.find(
            {"role": "patient"},
            {
                "_id": 0,
                "full_name": 1,
                "patient_id": 1,
                "username": 1,
            }
        )
    )

    for patient in patients:
        request = access_requests_collection.find_one(
            {
                "doctorId": current_user.username,
                "patientId": patient.get("patient_id"),
            },
            sort=[("createdAt", -1)],
        )
        patient["status"] = request["status"] if request else "NONE"
        patient["requestId"] = request.get("requestId") if request else None

    return {
        "status": "success",
        "patients": patients
    }

@router.get("/patients/{patient_username}/drugs")
async def get_patient_drugs(
    patient_username: str,
    current_user=Depends(get_current_active_user)
):
    require_doctor(current_user)

    patient = users_collection.find_one({"username": patient_username, "role": "patient"})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    if not has_accepted_access(current_user.username, patient.get("patient_id")):
        raise HTTPException(status_code=403, detail="Patient medication access has not been accepted.")

    schedules = list(
        patient_schedules_collection.find(
            {
                "patient_username": patient_username
            }
        ).sort("scheduled_time", 1)
    )

    for schedule in schedules:
        schedule.pop("_id", None)

    if not schedules:
        raise HTTPException(
            status_code=404,
            detail="No medication records found for this patient."
        )

    return {
        "status": "success",
        "patient_username": patient_username,
        "medications": schedules
    }
@router.get("/medication-history")
async def get_doctor_medication_history(
    current_user=Depends(get_current_active_user)
):
    require_doctor(current_user)

    accepted_patient_ids = [request["patientId"] for request in access_requests_collection.find(
        {"doctorId": current_user.username, "status": "ACCEPTED"},
        {"patientId": 1, "_id": 0},
    )]
    accepted_patients = [patient["username"] for patient in users_collection.find(
        {"patient_id": {"$in": accepted_patient_ids}, "role": "patient"},
        {"username": 1, "_id": 0},
    )]

    history = list(
        medication_history_collection.find(
            {"patient_username": {"$in": accepted_patients}}
        ).sort("taken_at", -1)
    )

    for record in history:
        record.pop("_id", None)
        taken_at = record.get("taken_at")
        if isinstance(taken_at, datetime):
            if taken_at.tzinfo is None:
                taken_at = taken_at.replace(tzinfo=timezone.utc)
            record["taken_at"] = taken_at.isoformat()

    return {
        "status": "success",
        "history": history
    }
