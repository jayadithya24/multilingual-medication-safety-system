from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.auth import get_current_active_user, User
from backend.app.database import (
    users_collection,
    medication_history_collection,
)


router = APIRouter(
    prefix="/patient",
    tags=["patient"]
)


class PatientProfileUpdate(BaseModel):
    full_name: str = Field(..., min_length=1)
    age: int = Field(..., ge=1, le=120)
    gender: str = Field(..., min_length=1)
    medical_condition: str = Field(..., min_length=1)


@router.get("/profile")
async def get_patient_profile(
    current_user: User = Depends(get_current_active_user)
):

    patient = users_collection.find_one({
        "username": current_user.username,
        "role": "patient"
    })

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    patient.pop("_id", None)

    return {
        "status": "success",
        "profile": patient
    }


@router.put("/profile")
async def update_patient_profile(
    payload: PatientProfileUpdate,
    current_user: User = Depends(get_current_active_user)
):

    patient = users_collection.find_one({
        "username": current_user.username,
        "role": "patient"
    })

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    users_collection.update_one(
        {
            "username": current_user.username,
            "role": "patient"
        },
        {
            "$set": {
                "full_name": payload.full_name.strip(),
                "age": payload.age,
                "gender": payload.gender,
                "medical_condition": payload.medical_condition
            }
        }
    )

    updated_patient = users_collection.find_one({
        "username": current_user.username,
        "role": "patient"
    })

    updated_patient.pop("_id", None)

    return {
        "status": "success",
        "message": "Patient profile updated successfully",
        "profile": updated_patient
    }
@router.get("/medication-history")
async def get_patient_medication_history(
    current_user=Depends(get_current_active_user)
):
    history = list(
        medication_history_collection.find(
            {
                "patient_username": current_user.username
            }
        ).sort("taken_at", -1)
    )

    for record in history:
        record.pop("_id", None)

    return {
        "status": "success",
        "history": history
    }