import asyncio
import hashlib
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from backend.app.database import (
    fcm_tokens_collection, patient_schedules_collection, reminder_deliveries_collection,
)

logger = logging.getLogger(__name__)
_firebase_app = None
_firebase_lock = threading.Lock()


def _firebase():
    global _firebase_app
    with _firebase_lock:
        if _firebase_app is not None:
            return _firebase_app
        import firebase_admin
        from firebase_admin import credentials
        credentials_file = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE")
        credentials_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        if not credentials_file and not credentials_json:
            raise RuntimeError("Configure Firebase Admin credentials on the backend.")
        certificate = credentials.Certificate(credentials_file or json.loads(credentials_json))
        _firebase_app = firebase_admin.initialize_app(certificate, options={"httpTimeout": 10})
        logger.info("Firebase Admin initialized")
        return _firebase_app


def _send(tokens, title, body, data):
    from firebase_admin import messaging
    if not tokens:
        raise ValueError("No FCM token is registered for this patient")
    app = _firebase()
    accepted, invalid = [], []
    for start in range(0, len(tokens), 500):
        batch = tokens[start:start + 500]
        response = messaging.send_each_for_multicast(messaging.MulticastMessage(
            tokens=batch, notification=messaging.Notification(title=title, body=body), data=data,
            webpush=messaging.WebpushConfig(
                headers={"Urgency": "high", "TTL": "300"},
                notification=messaging.WebpushNotification(
                    tag=data["event_id"], data={"url": "/patient-dashboard?tab=medicines"}),
            ),
        ), app=app)
        for token, result in zip(batch, response.responses):
            if result.success:
                accepted.append(token)
            elif isinstance(result.exception, messaging.UnregisteredError):
                invalid.append(token)
            else:
                logger.warning("FCM rejected delivery: %s", getattr(result.exception, "code", "unknown"))
    if invalid:
        fcm_tokens_collection.delete_many({"token": {"$in": invalid}})
    return accepted, invalid


def send_test_notification(tokens: list[str]) -> int:
    accepted, _ = _send(tokens, "Medication notification test",
        "FCM notifications are enabled for this device.",
        {"type": "test_notification", "event_id": uuid4().hex})
    return len(accepted)


def _current_time():
    return datetime.now(ZoneInfo(os.getenv("REMINDER_TIMEZONE", "Asia/Kolkata")))


def _utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _token_key(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _deliver(schedule, due_at, now):
    key = {"schedule_id": schedule["schedule_id"], "due_at": due_at}
    try:
        reminder_deliveries_collection.update_one(key, {"$setOnInsert": {
            "patient_username": schedule["patient_username"], "status": "pending",
            "completed_tokens": [], "attempts": 0, "expires_at": due_at + timedelta(days=30),
        }}, upsert=True)
    except DuplicateKeyError:
        pass
    owner = uuid4().hex
    claim = reminder_deliveries_collection.find_one_and_update({
        **key, "status": {"$nin": ["sent", "cancelled"]},
        "$and": [
            {"$or": [{"lease_until": {"$exists": False}}, {"lease_until": {"$lte": now}}]},
            {"$or": [{"retry_at": {"$exists": False}}, {"retry_at": {"$lte": now}}]},
        ],
    }, {"$set": {"owner": owner, "lease_until": now + timedelta(minutes=2)},
        "$inc": {"attempts": 1}}, return_document=ReturnDocument.AFTER)
    if not claim:
        return 0
    owned = {**key, "owner": owner}
    try:
        if not patient_schedules_collection.find_one({
            "_id": schedule["_id"], "status": "active",
            "is_active": {"$ne": False}, "reminder_enabled": {"$ne": False},
        }):
            reminder_deliveries_collection.update_one(owned, {"$set": {"status": "cancelled"}})
            return 0
        tokens = list(dict.fromkeys(item["token"] for item in fcm_tokens_collection.find(
            {"patient_username": schedule["patient_username"]}, {"token": 1},
        )))
        completed = set(claim.get("completed_tokens", []))
        pending = [token for token in tokens if _token_key(token) not in completed]
        if not tokens:
            raise ValueError("no_registered_device")
        accepted, invalid = ([], [])
        if pending:
            accepted, invalid = _send(pending, "Medication reminder",
                f"Time to take {schedule['medicine_name']} {schedule['dosage']}",
                {"type": "medication_reminder", "event_id": str(claim["_id"])})
        completed.update(_token_key(token) for token in accepted + invalid)
        success_count = claim.get("accepted_count", 0) + len(accepted)
        done = all(_token_key(token) in completed for token in tokens) and success_count > 0
        reminder_deliveries_collection.update_one(owned, {
            "$set": {"status": "sent" if done else "retry", "completed_tokens": list(completed),
                     "accepted_count": success_count, "attempted_at": now,
                     "retry_at": now + timedelta(seconds=15),
                     "last_error": None if done else "device_delivery_failed"},
            "$unset": {"lease_until": "", "owner": ""},
        })
        if done:
            patient_schedules_collection.update_one({"_id": schedule["_id"]}, {"$set": {
                "last_reminder_key": due_at.isoformat(), "last_reminder_sent_at": now,
            }})
        return int(done)
    except Exception as error:
        reminder_deliveries_collection.update_one(owned, {
            "$set": {"status": "retry", "last_error": type(error).__name__,
                     "attempted_at": now, "retry_at": now + timedelta(seconds=15)},
            "$unset": {"lease_until": "", "owner": ""},
        })
        logger.warning("Reminder attempt failed (%s)", type(error).__name__)
        return 0


def process_due_reminders(now=None) -> int:
    now = now or _current_time()
    local_now = now.astimezone(ZoneInfo(os.getenv("REMINDER_TIMEZONE", "Asia/Kolkata")))
    utc_now = _utc(now)
    window = max(1, min(15, int(os.getenv("REMINDER_CATCHUP_MINUTES", "5"))))
    occurrences = []
    for offset in range(window + 1):
        due = local_now.replace(second=0, microsecond=0) - timedelta(minutes=offset)
        if utc_now - _utc(due) <= timedelta(minutes=window):
            occurrences.append(due)
    jobs = []
    for schedule in patient_schedules_collection.find({
        "status": "active", "is_active": {"$ne": False}, "reminder_enabled": {"$ne": False},
        "scheduled_times": {"$in": [due.strftime("%H:%M") for due in occurrences]},
    }):
        for due in occurrences:
            if due.strftime("%H:%M") not in schedule.get("scheduled_times", []):
                continue
            due_at = _utc(due)
            if schedule.get("last_reminder_key") in {due.strftime("%Y-%m-%d:%H:%M"), due_at.isoformat()}:
                continue
            if schedule.get("created_at") and _utc(schedule["created_at"]) > due_at:
                continue
            if schedule.get("last_taken_at") and _utc(schedule["last_taken_at"]) >= due_at:
                continue
            jobs.append((schedule, due_at, utc_now))
    if not jobs:
        return 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        return sum(pool.map(lambda args: _deliver(*args), jobs))


async def reminder_loop(stop_event: asyncio.Event):
    interval = max(1, int(os.getenv("REMINDER_POLL_SECONDS", "2")))
    while not stop_event.is_set():
        started = time.monotonic()
        try:
            await asyncio.to_thread(process_due_reminders)
        except Exception as error:
            logger.warning("Medication reminder poll failed (%s)", type(error).__name__)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=max(0.1, interval - (time.monotonic() - started)))
        except asyncio.TimeoutError:
            pass
