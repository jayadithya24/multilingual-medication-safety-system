"""Create MongoDB collections with JSON Schema validators for Phase 1.

This script is idempotent and intended for initial DB setup.
"""
from pymongo import MongoClient
from typing import Dict, Any


INTERACTIONS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["drug1_id", "drug2_id", "severity"],
        "properties": {
            "drug1_id": {"bsonType": "string"},
            "drug2_id": {"bsonType": "string"},
            "severity": {"enum": ["Mild", "Moderate", "Severe"]},
            "drug2_in_scope": {"bsonType": "bool"}
        }
    }
}


def create_validators(uri: str, db_name: str = "meds") -> None:
    client = MongoClient(uri)
    db = client[db_name]

    # Create collections if they do not exist and apply validators where appropriate
    if "drugs" not in db.list_collection_names():
        db.create_collection("drugs")
        db.drugs.create_index([("drug_id", 1)], unique=True)

    if "diseases" not in db.list_collection_names():
        db.create_collection("diseases")
        db.diseases.create_index([("drug_id", 1)])

    if "side_effects" not in db.list_collection_names():
        db.create_collection("side_effects")
        db.side_effects.create_index([("drug_id", 1)])

    if "interactions" not in db.list_collection_names():
        db.create_collection("interactions", validator=INTERACTIONS_VALIDATOR)
        db.interactions.create_index([("drug1_id", 1), ("drug2_id", 1)], unique=True)

    if "validation_stats" not in db.list_collection_names():
        db.create_collection("validation_stats")

    if "users" not in db.list_collection_names():
        db.create_collection("users")


if __name__ == "__main__":
    import os
    uri = os.environ.get("MONGO_URI")
    if not uri:
        raise RuntimeError("Set MONGO_URI to run validators script")
    create_validators(uri, os.environ.get("MONGO_DB", "meds"))
