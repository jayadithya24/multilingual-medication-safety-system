from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import PATIENT_DB
from app.services.notification_service import send_caretaker_alert

scheduler = AsyncIOScheduler()

# Default mapping for timeslots to HH:MM format if specific times are not parsed
SLOT_TIME_MAP = {
    "morning": "09:00",
    "afternoon": "13:00",
    "night": "20:00"
}


async def check_missed_medications():
    """
    Runs automatically in the background every 15 minutes.
    Reads PATIENT_DB dynamically. If a scheduled medication time has passed by 
    more than 30 minutes and is_taken is False, dispatches an alert notification 
    to the caretaker and marks it as alert sent.
    """
    now = datetime.now()

    # Iterate over dynamically stored patients in PATIENT_DB
    for patient_id, patient_data in PATIENT_DB.items():
        caretaker_phone = patient_data.get("caretaker_phone", "+919876543210")
        medications = patient_data.get("medications", [])

        for med in medications:
            # Skip if medication has already been taken or alerted
            if med.get("is_taken", False) or med.get("alert_sent", False):
                continue

            # Determine scheduled HH:MM dynamically
            scheduled_time_str = med.get("scheduled_time")
            if not scheduled_time_str:
                slot = med.get("scheduled_slot", "morning").lower()
                scheduled_time_str = SLOT_TIME_MAP.get(slot, "09:00")

            try:
                sched_hour, sched_min = map(int, scheduled_time_str.split(":"))
                scheduled_datetime = now.replace(
                    hour=sched_hour, minute=sched_min, second=0, microsecond=0
                )

                # Trigger alert if current time exceeds scheduled dose by 30+ minutes
                if now > scheduled_datetime + timedelta(minutes=30):
                    msg_alert = (
                        f"ನೆನಪೋಲೆ / REMINDER: Patient {patient_id} missed taking "
                        f"{med['medicine_name']} scheduled for {scheduled_time_str}."
                    )

                    send_caretaker_alert(
                        patient_id=patient_id,
                        medicine_name=med["medicine_name"],
                        status="RED",
                        message=msg_alert,
                        caretaker_phone=caretaker_phone
                    )

                    # Mark alert_sent = True to prevent spamming duplicate notifications
                    med["alert_sent"] = True
                    med["status"] = "MISSED"
                    print(f"[SCHEDULER] Missed dose alert dispatched for Patient {patient_id} ({med['medicine_name']})")

            except ValueError:
                continue


def mark_tablet_taken(patient_id: str, medicine_name: str):
    """
    Call this function when a patient successfully scans their tablet (GREEN status).
    Dynamically updates PATIENT_DB so missed-dose reminders are canceled.
    """
    patient = PATIENT_DB.get(patient_id)
    if patient:
        for med in patient.get("medications", []):
            if med["medicine_name"].lower() == medicine_name.lower():
                med["is_taken"] = True
                med["status"] = "TAKEN"
                print(f"[SCHEDULER UPDATE] Patient {patient_id} marked {medicine_name} as TAKEN in PATIENT_DB.")


def start_scheduler():
    """Starts the background task runner on FastAPI application startup."""
    scheduler.add_job(check_missed_medications, 'interval', minutes=15)
    scheduler.start()
    print("[SCHEDULER] Background medication monitor started (Interval: 15 mins).")