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

patient_schedules_collection = db["patient_schedules"]
medication_history_collection = db["medication_history"]

# Useful indexes
patient_schedules_collection.create_index(
    [("patient_username", 1), ("scheduled_time", 1)]
)

medication_history_collection.create_index(
    [("patient_username", 1), ("date", -1)]
)