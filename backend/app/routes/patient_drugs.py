from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from backend.app.auth import get_current_active_user
from backend.app.database import (
    users_collection,
    patient_schedules_collection,
    medication_history_collection,
)


router = APIRouter(
    prefix="/doctor",
    tags=["doctor patient drugs"]
)


def require_doctor(current_user):
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=403,
            detail="Only doctors can access patient drug lists."
        )


@router.get("/patients")
async def get_patients(
    current_user=Depends(get_current_active_user)
):
    require_doctor(current_user)

    # Get ALL registered patients from MongoDB
    patients = list(
        users_collection.find(
            {"role": "patient"},
            {
                "_id": 0,
                "username": 1,
                "full_name": 1,
                "email": 1,
                "patient_id": 1,
                "age": 1,
                "gender": 1,
                "medical_condition": 1,
            }
        )
    )

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

    history = list(
        medication_history_collection.find(
            {}
        ).sort("taken_at", -1)
    )

    for record in history:
        record.pop("_id", None)

    return {
        "status": "success",
        "history": history
    }