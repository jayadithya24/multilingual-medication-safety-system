# app/db.py

# Stores uploaded patient prescriptions dynamically in memory
# Format:
# {
#    "PATIENT_ID": {
#        "caretaker_phone": "+91...",
#        "medications": [
#            {"medicine_name": "...", "scheduled_slot": "morning", "dose": "...", "is_taken": False}
#        ]
#    }
# }
PATIENT_DB = {}