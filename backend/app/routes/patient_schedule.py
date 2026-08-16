from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.auth import get_current_active_user, User
from backend.app.database import patient_schedules_collection


router = APIRouter(
    prefix="/patient-schedule",
    tags=["patient schedule"]
)


# ============================================================
# REQUEST MODEL
# ============================================================

class MedicationScheduleCreate(BaseModel):

    medicine_name: str = Field(..., min_length=1)

    dosage: str = Field(
        ...,
        min_length=1
    )

    instructions: str = ""

    frequency: str = Field(
        ...,
        min_length=1
    )

    scheduled_times: list[str] = Field(
        ...,
        min_length=1
    )

    reminder_enabled: bool = True


# ============================================================
# ADD MEDICATION TO SCHEDULE
# ============================================================

@router.post("")
async def create_medication_schedule(
    payload: MedicationScheduleCreate,
    current_user: User = Depends(
        get_current_active_user
    )
):

    if current_user.role != "patient":
        raise HTTPException(
            status_code=403,
            detail="Only patients can create medication schedules."
        )

    # Validate dosing times
    for time_value in payload.scheduled_times:

        try:
            datetime.strptime(
                time_value,
                "%H:%M"
            )

        except ValueError:

            raise HTTPException(
                status_code=400,
                detail=f"Invalid time format: {time_value}. Use HH:MM."
            )

    schedule_id = f"SCH-{uuid4().hex[:8].upper()}"

    schedule = {
        "schedule_id": schedule_id,

        "patient_username": current_user.username,

        "medicine_name": payload.medicine_name.strip(),

        "dosage": payload.dosage.strip(),

        "instructions": payload.instructions.strip(),

        "frequency": payload.frequency.strip(),

        "scheduled_times": payload.scheduled_times,

        "reminder_enabled": payload.reminder_enabled,

        "status": "active",

        "created_at": datetime.now(
            timezone.utc
        )
    }

    patient_schedules_collection.insert_one(
        schedule
    )

    schedule.pop("_id", None)

    return {
        "status": "success",
        "message": "Medication added to schedule.",
        "schedule": schedule
    }


# ============================================================
# GET MY MEDICATION SCHEDULE
# ============================================================

@router.get("")
async def get_my_medication_schedule(
    current_user: User = Depends(
        get_current_active_user
    )
):

    if current_user.role != "patient":
        raise HTTPException(
            status_code=403,
            detail="Only patients can access their medication schedule."
        )

    schedules = list(
        patient_schedules_collection.find(
            {
                "patient_username": current_user.username,
                "status": "active"
            }
        ).sort(
            "created_at",
            -1
        )
    )

    for schedule in schedules:
        schedule.pop("_id", None)

    return {
        "status": "success",
        "schedules": schedules
    }


# ============================================================
# DELETE MEDICATION SCHEDULE
# ============================================================

@router.delete("/{schedule_id}")
async def delete_medication_schedule(
    schedule_id: str,
    current_user: User = Depends(
        get_current_active_user
    )
):

    if current_user.role != "patient":
        raise HTTPException(
            status_code=403,
            detail="Only patients can delete medication schedules."
        )

    result = patient_schedules_collection.update_one(
        {
            "schedule_id": schedule_id,
            "patient_username": current_user.username
        },
        {
            "$set": {
                "status": "inactive"
            }
        }
    )

    if result.matched_count == 0:

        raise HTTPException(
            status_code=404,
            detail="Medication schedule not found."
        )

    return {
        "status": "success",
        "message": "Medication removed from schedule."
    }