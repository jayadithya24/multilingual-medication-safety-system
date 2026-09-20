import asyncio
import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.app.database import (
    fcm_tokens_collection,
    patient_schedules_collection,
)

logger = logging.getLogger(__name__)
_firebase_app = None


def _firebase():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    import firebase_admin
    from firebase_admin import credentials

    credentials_file = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE")
    credentials_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if credentials_file:
        _firebase_app = firebase_admin.initialize_app(
            credentials.Certificate(credentials_file)
        )
    elif credentials_json:
        _firebase_app = firebase_admin.initialize_app(
            credentials.Certificate(json.loads(credentials_json))
        )
    else:
        logger.error(
            "[FCM] Configure FIREBASE_SERVICE_ACCOUNT_FILE or FIREBASE_SERVICE_ACCOUNT_JSON"
        )
        return None

    logger.info("[FCM] Firebase Admin initialized")
    return _firebase_app


def send_test_notification(tokens: list[str]) -> int:
    app = _firebase()
    if not app:
        raise RuntimeError("Firebase Admin credentials are not configured")
    if not tokens:
        raise ValueError("No FCM token is registered for this patient")

    from firebase_admin import messaging

    response = messaging.send_each_for_multicast(
        messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(
                title="Medication notification test",
                body="FCM notifications are enabled for this device.",
            ),
            data={"type": "test_notification"},
        ),
        app=app,
    )
    logger.info("[FCM] Test notification sent: %s/%s succeeded", response.success_count, response.failure_count)
    return response.success_count


def _current_time():
    timezone_name = os.getenv("REMINDER_TIMEZONE", "UTC")
    return datetime.now(ZoneInfo(timezone_name))


def send_fcm_reminder(tokens: list[str], medicine_name: str, dosage: str) -> None:
    app = _firebase()
    if not app or not tokens:
        raise RuntimeError("Firebase credentials and registered devices are required")

    from firebase_admin import messaging

    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(
            title="Medication reminder",
            body=f"Time to take {medicine_name} {dosage}",
        ),
        data={"type": "medication_reminder", "medicine_name": medicine_name, "dosage": dosage},
    )
    response = messaging.send_each_for_multicast(message, app=app)
    invalid_tokens = []
    for token, result in zip(tokens, response.responses):
        if not result.success and result.exception:
            error_code = getattr(result.exception, "code", "")
            if error_code in {"messaging/registration-token-not-registered", "messaging/invalid-registration-token"}:
                invalid_tokens.append(token)
    if invalid_tokens:
        fcm_tokens_collection.delete_many({"token": {"$in": invalid_tokens}})
    if response.success_count == 0:
        raise RuntimeError("No device accepted the reminder")


def process_due_reminders(now=None) -> int:
    now = now or _current_time()
    time_key = now.strftime("%Y-%m-%d:%H:%M")
    due_time = now.strftime("%H:%M")
    sent_count = 0

    schedules = patient_schedules_collection.find({
        "status": "active",
        "is_active": {"$ne": False},
        "reminder_enabled": {"$ne": False},
        "scheduled_times": due_time,
        "last_reminder_key": {"$ne": time_key},
    })
    for schedule in schedules:
        tokens = [item["token"] for item in fcm_tokens_collection.find(
            {"patient_username": schedule["patient_username"]},
            {"token": 1, "_id": 0},
        )]
        if not tokens:
            continue
        try:
            send_fcm_reminder(tokens, schedule["medicine_name"], schedule["dosage"])
            patient_schedules_collection.update_one(
                {"_id": schedule["_id"], "last_reminder_key": {"$ne": time_key}},
                {"$set": {"last_reminder_key": time_key}},
            )
            sent_count += 1
        except Exception:
            logger.exception("Unable to send medication reminder for %s", schedule.get("schedule_id"))
    return sent_count


async def reminder_loop(stop_event: asyncio.Event):
    interval = max(10, int(os.getenv("REMINDER_POLL_SECONDS", "30")))
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(process_due_reminders)
        except Exception:
            logger.exception("Medication reminder poll failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue
