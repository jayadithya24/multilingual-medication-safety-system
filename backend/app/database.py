import os
from pymongo import MongoClient

from backend.env_loader import load_project_env

load_project_env()

MONGO_URI = os.environ.get("MONGO_URI") or os.environ.get("MONGODB_URI")
MONGO_DB = os.environ.get("MONGO_DB", "meds")
USE_MONGOMOCK = (
    os.environ.get("USE_MONGOMOCK", "").lower() in {"1", "true", "yes"}
    or "PYTEST_CURRENT_TEST" in os.environ
    or os.environ.get("ENVIRONMENT", "").lower() == "test"
)


def _get_database_client():
    if not MONGO_URI:
        if USE_MONGOMOCK:
            import mongomock

            return mongomock.MongoClient(), MONGO_DB
        raise RuntimeError("MONGO_URI is not configured in the project .env file")

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        return client, MONGO_DB
    except Exception:
        local_uri = MONGO_URI.startswith("mongodb://localhost") or MONGO_URI.startswith("mongodb://127.0.0.1")
        if USE_MONGOMOCK or local_uri:
            import mongomock

            return mongomock.MongoClient(), MONGO_DB
        raise


client, db_name = _get_database_client()
db = client[db_name]

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
