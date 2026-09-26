from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.auth import User, get_current_active_user
from backend.app.database import fcm_tokens_collection
from backend.app.services.fcm_service import send_test_notification
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/patient", tags=["notifications"])


class FCMTokenPayload(BaseModel):
    token: str = Field(..., min_length=20, max_length=4096)
    platform: str = Field(default="browser", max_length=30)


@router.post("/fcm-token")
def register_fcm_token(
    payload: FCMTokenPayload,
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can register notification devices.")

    # A browser subscription belongs only to the patient currently using it.
    fcm_tokens_collection.delete_many({"token": payload.token, "patient_username": {"$ne": current_user.username}})
    result = fcm_tokens_collection.update_one(
        {"patient_username": current_user.username, "token": payload.token},
        {"$set": {"platform": payload.platform}, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    stored = fcm_tokens_collection.find_one({"patient_username": current_user.username, "token": payload.token}, {"_id": 0, "token": 1})
    logger.info("[FCM] Token storage patient=%s matched=%s upserted=%s stored=%s", current_user.username, result.matched_count, result.upserted_id is not None, stored is not None)
    if stored is None:
        raise HTTPException(status_code=500, detail="FCM token could not be stored.")
    return {"status": "success", "message": "Notification device registered."}


@router.post("/fcm-test")
def send_patient_test_notification(current_user: User = Depends(get_current_active_user)):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can send notification tests.")

    tokens = [item["token"] for item in fcm_tokens_collection.find(
        {"patient_username": current_user.username}, {"token": 1, "_id": 0}
    )]
    logger.info("[FCM] Test requested patient=%s stored_tokens=%s", current_user.username, len(tokens))
    try:
        success_count = send_test_notification(tokens)
        if success_count == 0:
            raise RuntimeError("No device accepted the notification. Enable notifications again and retry.")
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        logger.warning("FCM test failed (%s)", type(error).__name__)
        raise HTTPException(503, "Firebase could not accept the notification. Check the backend credentials, project and device registration.") from error
    return {"status": "success", "message": f"Test notification sent to {success_count} device(s)."}


@router.delete("/fcm-token")
def unregister_fcm_token(
    payload: FCMTokenPayload,
    current_user: User = Depends(get_current_active_user),
):
    fcm_tokens_collection.delete_one({"patient_username": current_user.username, "token": payload.token})
    return {"status": "success", "message": "Notification device unregistered."}
