import os
from pymongo import MongoClient

from backend.env_loader import load_project_env

load_project_env()

MONGO_URI = os.environ.get("MONGO_URI")
MONGO_DB = os.environ.get("MONGO_DB", "meds")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not configured in the project .env file")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

# Collections used by the patient medication system
users_collection = db["users"]
users_collection.create_index("google_sub", unique=True, sparse=True)
doctor_requests_collection = db["doctor_requests"]

patient_schedules_collection = db["patient_schedules"]
medication_history_collection = db["medication_history"]
access_requests_collection = db["access_requests"]
fcm_tokens_collection = db["fcm_tokens"]
reminder_deliveries_collection = db["reminder_deliveries"]
reminder_deliveries_collection.create_index([("schedule_id", 1), ("due_at", 1)], unique=True)
reminder_deliveries_collection.create_index("expires_at", expireAfterSeconds=0)

# Useful indexes
users_collection.create_index(
    [("username", 1)],
    unique=True,
)
users_collection.create_index(
    [("doctor_id", 1)],
    unique=True,
    sparse=True,
)
doctor_requests_collection.create_index(
    [("email", 1)],
    unique=True,
    partialFilterExpression={"status": "pending"},
)
doctor_requests_collection.create_index([("status", 1), ("created_at", -1)])

patient_schedules_collection.create_index(
    [("patient_username", 1), ("created_at", -1)]
)
patient_schedules_collection.create_index([("status", 1), ("scheduled_times", 1)])

medication_history_collection.create_index(
    [("patient_username", 1), ("taken_at", -1)]
)

access_requests_collection.create_index(
    [("doctorId", 1), ("patientId", 1), ("status", 1)]
)

fcm_tokens_collection.create_index(
    [("patient_username", 1), ("token", 1)],
    unique=True,
)
