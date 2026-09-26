from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.auth import get_current_active_user, User
from backend.app.database import (
    medication_history_collection,
    patient_schedules_collection,
    users_collection,
)


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
def create_medication_schedule(
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

        "patient_id": (users_collection.find_one(
            {"username": current_user.username, "role": "patient"},
            {"patient_id": 1, "_id": 0},
        ) or {}).get("patient_id"),

        "medicine_name": payload.medicine_name.strip(),

        "dosage": payload.dosage.strip(),

        "instructions": payload.instructions.strip(),

        "frequency": payload.frequency.strip(),

        "scheduled_times": sorted(set(datetime.strptime(value, "%H:%M").strftime("%H:%M") for value in payload.scheduled_times)),

        "reminder_enabled": payload.reminder_enabled,

        "is_active": True,

        "last_taken_at": None,

        "last_reminder_key": None,

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
def get_my_medication_schedule(
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
# GET REMOVED MEDICATION SCHEDULES
# ============================================================

@router.get("/removed")
def get_removed_medication_schedules(
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "patient":
        raise HTTPException(
            status_code=403,
            detail="Only patients can access removed medication schedules."
        )

    schedules = list(
        patient_schedules_collection.find(
            {
                "patient_username": current_user.username,
                "status": "inactive",
            }
        ).sort("deleted_at", -1)
    )

    for schedule in schedules:
        schedule.pop("_id", None)

    return {"status": "success", "schedules": schedules}


# ============================================================
# DELETE MEDICATION SCHEDULE
# ============================================================

@router.delete("/{schedule_id}")
def delete_medication_schedule(
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

    deleted_at = datetime.now(timezone.utc)
    result = patient_schedules_collection.update_one(
        {
            "schedule_id": schedule_id,
            "patient_username": current_user.username,
            "status": "active",
        },
        {
            "$set": {
                "status": "inactive",
                "is_active": False,
                "reminder_enabled": False,
                "deleted_at": deleted_at,
            }
        }
    )

    if result.matched_count == 0:

        raise HTTPException(
            status_code=404,
            detail="Medication schedule not found."
        )

    removed_schedule = patient_schedules_collection.find_one(
        {
            "schedule_id": schedule_id,
            "patient_username": current_user.username,
        },
        {"_id": 0},
    )

    return {
        "status": "success",
        "message": "Medication removed from schedule.",
        "schedule": removed_schedule,
    }


@router.post("/{schedule_id}/taken")
def mark_medication_taken(
    schedule_id: str,
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can update medication schedules.")

    schedule = patient_schedules_collection.find_one({
        "schedule_id": schedule_id,
        "patient_username": current_user.username,
        "status": "active",
    })
    if not schedule:
        raise HTTPException(status_code=404, detail="Medication schedule not found.")

    taken_at = datetime.now(timezone.utc)
    history_id = f"HIS-{uuid4().hex[:8].upper()}"
    medication_history_collection.insert_one({
        "history_id": history_id,
        "status": "TAKEN",
        "schedule_id": schedule_id,
        "patient_username": current_user.username,
        "patient_id": schedule.get("patient_id"),
        "medicine_name": schedule["medicine_name"],
        "dosage": schedule["dosage"],
        "scheduled_time": ", ".join(schedule.get("scheduled_times", [])),
        "taken_at": taken_at,
    })
    patient_schedules_collection.update_one(
        {"schedule_id": schedule_id, "patient_username": current_user.username},
        {"$set": {"last_taken_at": taken_at}},
    )
    return {
        "status": "success",
        "message": "Medication marked as taken.",
        "history_id": history_id,
        "taken_at": taken_at.isoformat(),
    }
