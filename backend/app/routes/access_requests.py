from datetime import datetime, timezone, timedelta
from hashlib import sha256
import secrets
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Literal
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel, Field

from backend.app.auth import User, get_current_active_user
from backend.app.database import (
    access_requests_collection,
    patient_schedules_collection,
    users_collection,
    share_codes_collection, access_log_collection, medication_history_collection, consent_attempts_collection,
)


router = APIRouter(tags=["medication access"])


class AccessRequestCreate(BaseModel):
    share_code: str = Field(..., min_length=16, max_length=64)


def require_role(current_user: User, role: str) -> None:
    if not current_user or not getattr(current_user, "role", None):
        raise HTTPException(status_code=401, detail="Authentication required.")
    if current_user.role != role:
        raise HTTPException(status_code=403, detail=f"Only {role} accounts can access this endpoint.")


def public_request(request: dict) -> dict:
    request.pop("_id", None)
    for key, value in request.items():
        if isinstance(value, datetime) and value.tzinfo is None:
            request[key] = value.replace(tzinfo=timezone.utc)
    expiry = request.get("expiresAt")
    if request["status"] in ("PENDING", "ACCEPTED") and (not expiry or expiry.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc)):
        request["status"] = "EXPIRED"
    return request


def get_patient_by_id(patient_id: str) -> dict:
    patient = users_collection.find_one({"patient_id": patient_id, "role": "patient"})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return patient


def has_accepted_access(doctor_id: str, patient_id: str) -> bool:
    return access_requests_collection.find_one({
        "doctorId": doctor_id,
        "patientId": patient_id,
        "status": "ACCEPTED",
        "expiresAt": {"$gt": datetime.now(timezone.utc)},
    }) is not None


def log_access(doctor_id, patient_id, action):
    now = datetime.now(timezone.utc)
    reading = action.startswith('VIEW_')
    record = {"doctorId": doctor_id, "patientId": patient_id, "action": action,
              "createdAt": now, 'category': 'read' if reading else 'security'}
    if reading or action.startswith('DENIED_'):
        key = f'{doctor_id}|{patient_id}|{action}|{int(now.timestamp()) // 300}'
        record['_id'] = ObjectId(sha256(key.encode()).hexdigest()[:24])
        access_log_collection.update_one({'_id': record['_id']}, {'$setOnInsert': record}, upsert=True)
    else:
        access_log_collection.insert_one(record)


def authorize_access(doctor_id, patient_id, action):
    grant = access_requests_collection.find_one({"doctorId": doctor_id, "patientId": patient_id,
        "status": "ACCEPTED", "expiresAt": {"$gt": datetime.now(timezone.utc)}})
    if not grant:
        if users_collection.find_one({"patient_id": patient_id, "role": "patient"}):
            log_access(doctor_id, patient_id, "DENIED_" + action)
        raise HTTPException(403, "Patient access is not authorized.")
    log_access(doctor_id, patient_id, action)
    return grant


def own_patient(user):
    require_role(user, "patient")
    patient = users_collection.find_one({"username": user.username, "role": "patient"})
    if not patient or not patient.get("patient_id"):
        raise HTTPException(404, "Patient not found.")
    return patient


@router.post("/patient/share-code")
def create_share_code(current_user: User = Depends(get_current_active_user)):
    patient = own_patient(current_user)
    code = secrets.token_hex(8).upper()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    share_codes_collection.delete_many({"patientId": patient["patient_id"]})
    share_codes_collection.insert_one({"patientId": patient["patient_id"],
        "code_hash": sha256(code.encode()).hexdigest(), "expiresAt": expiry})
    return {"share_code": code, "expires_at": expiry}


@router.get("/patient/access-log")
def get_access_log(current_user: User = Depends(get_current_active_user),
                   category: Literal['all', 'security', 'read'] = 'all',
                   cursor: str | None = None, limit: int = Query(50, ge=1, le=200)):
    patient = own_patient(current_user)
    query = {"patientId": patient["patient_id"]}
    if category != 'all':
        query['action'] = {'$regex': '^VIEW_'} if category == 'read' else {'$not': {'$regex': '^VIEW_'}}
    if cursor:
        try:
            stamp, identifier = cursor.rsplit('|', 1)
            before = datetime.fromisoformat(stamp)
            query['$or'] = [{'createdAt': {'$lt': before}}, {'createdAt': before, '_id': {'$lt': ObjectId(identifier)}}]
        except (ValueError, TypeError, InvalidId):
            raise HTTPException(400, 'Invalid access-log cursor.')
    events = list(access_log_collection.find(query).sort([('createdAt', -1), ('_id', -1)]).limit(limit + 1))
    more = len(events) > limit
    events = events[:limit]
    next_cursor = f"{events[-1]['createdAt'].isoformat()}|{events[-1]['_id']}" if more else None
    for event in events:
        event.pop('_id', None)
        event["createdAt"] = event["createdAt"].replace(tzinfo=timezone.utc)
    return {"events": events, 'next_cursor': next_cursor}


@router.put("/patient/access-request/{request_id}/renew")
def renew_access(request_id: str, current_user: User = Depends(get_current_active_user)):
    patient = own_patient(current_user)
    current = datetime.now(timezone.utc)
    record = access_requests_collection.find_one_and_update({"requestId": request_id,
        "patientId": patient["patient_id"], "status": "ACCEPTED", "scope": "medicines_and_history"},
        {"$set": {"respondedAt": current, "expiresAt": current + timedelta(days=7)}}, return_document=ReturnDocument.AFTER)
    if not record:
        raise HTTPException(409, "Only an existing approved grant can be renewed. Otherwise create a new sharing code.")
    log_access(record["doctorId"], patient["patient_id"], "RENEWED")
    return {"request": public_request(record)}


@router.post("/doctor/access-request")
async def create_access_request(
    payload: AccessRequestCreate,
    current_user: User = Depends(get_current_active_user),
):
    require_role(current_user, "doctor")
    current = datetime.now(timezone.utc)
    key = {"doctorId": current_user.username, "window": int(current.timestamp()) // 60}
    update = {"$inc": {"count": 1}, "$setOnInsert": {"expiresAt": current + timedelta(minutes=2)}}
    try:
        attempts = consent_attempts_collection.find_one_and_update(key, update, upsert=True, return_document=ReturnDocument.AFTER)
    except DuplicateKeyError:
        attempts = consent_attempts_collection.find_one_and_update(key, {"$inc": {"count": 1}}, return_document=ReturnDocument.AFTER)
    if attempts["count"] > 10:
        raise HTTPException(429, "Too many sharing-code attempts. Retry after one minute.", headers={"Retry-After": "60"})
    code = share_codes_collection.find_one_and_delete({
        "code_hash": sha256(payload.share_code.strip().upper().encode()).hexdigest(),
        "expiresAt": {"$gt": datetime.now(timezone.utc)}})
    if not code:
        raise HTTPException(404, "Share code is invalid, expired or already used.")
    patient = get_patient_by_id(code["patientId"])
    patient_id = patient["patient_id"]

    existing = access_requests_collection.find_one({
        "doctorId": current_user.username,
        "patientId": patient_id,
        "status": "PENDING",
        "expiresAt": {"$gt": datetime.now(timezone.utc)},
    })
    if existing:
        return {"status": "success", "request": public_request(existing)}

    request = {
        "requestId": f"AR-{uuid4().hex[:12].upper()}",
        "doctorId": current_user.username,
        "patientId": patient_id,
        "doctorName": current_user.full_name or current_user.username,
        "status": "PENDING",
        "createdAt": datetime.now(timezone.utc),
        "respondedAt": None,
        "expiresAt": datetime.now(timezone.utc) + timedelta(hours=24),
        "scope": "medicines_and_history",
    }
    access_requests_collection.insert_one(request)
    log_access(current_user.username, patient_id, "REQUESTED")
    return {"status": "success", "request": public_request(request)}


@router.get("/patient/access-requests")
async def get_patient_access_requests(current_user: User = Depends(get_current_active_user)):
    require_role(current_user, "patient")
    patient = users_collection.find_one({"username": current_user.username, "role": "patient"})
    requests = list(access_requests_collection.find(
        {"patientId": patient.get("patient_id") if patient else None}
    ).sort("createdAt", -1))
    return {"status": "success", "requests": [public_request(item) for item in requests]}


async def respond_to_request(request_id: str, decision: str, current_user: User):
    require_role(current_user, "patient")
    patient = users_collection.find_one({"username": current_user.username, "role": "patient"})
    request = access_requests_collection.find_one({
        "requestId": request_id,
        "patientId": patient.get("patient_id") if patient else None,
    })
    if not request:
        raise HTTPException(status_code=404, detail="Access request not found.")
    expected = "ACCEPTED" if decision == "REVOKED" else "PENDING"
    if public_request(dict(request))["status"] != expected:
        raise HTTPException(status_code=409, detail="Access request has already been answered.")

    changes = {"status": decision, "respondedAt": datetime.now(timezone.utc)}
    if decision == "ACCEPTED":
        changes["expiresAt"] = datetime.now(timezone.utc) + timedelta(days=7)
    result = access_requests_collection.update_one(
        {"requestId": request_id, "patientId": patient["patient_id"], "status": expected,
         "expiresAt": {"$gt": datetime.now(timezone.utc)}},
        {"$set": changes},
    )
    if not result.modified_count:
        raise HTTPException(409, "Request expired or already answered.")
    if decision == "REVOKED":
        access_requests_collection.update_many({"doctorId": request["doctorId"],
            "patientId": patient["patient_id"], "status": {"$in": ["PENDING", "ACCEPTED"]}}, {"$set": changes})
    log_access(request["doctorId"], patient["patient_id"], decision)
    updated = access_requests_collection.find_one({"requestId": request_id})
    return {"status": "success", "request": public_request(updated)}


@router.put("/patient/access-request/{request_id}/accept")
async def accept_access_request(request_id: str, current_user: User = Depends(get_current_active_user)):
    return await respond_to_request(request_id, "ACCEPTED", current_user)


@router.put("/patient/access-request/{request_id}/reject")
async def reject_access_request(request_id: str, current_user: User = Depends(get_current_active_user)):
    return await respond_to_request(request_id, "REJECTED", current_user)


@router.get("/doctor/access-requests")
async def get_doctor_access_requests(current_user: User = Depends(get_current_active_user)):
    require_role(current_user, "doctor")
    requests = list(access_requests_collection.find({"doctorId": current_user.username}).sort("createdAt", -1))
    return {"status": "success", "requests": [{key: public_request(item).get(key)
        for key in ("requestId", "status", "expiresAt")} for item in requests]}


@router.put("/patient/access-request/{request_id}/revoke")
async def revoke_access_request(request_id: str, current_user: User = Depends(get_current_active_user)):
    return await respond_to_request(request_id, "REVOKED", current_user)


@router.get("/doctor/patients/{patient_id}/medications")
async def get_patient_medications(
    patient_id: str,
    current_user: User = Depends(get_current_active_user),
):
    require_role(current_user, "doctor")
    
    authorize_access(current_user.username, patient_id, "VIEW_MEDICATIONS_AND_HISTORY")
    patient = get_patient_by_id(patient_id)

    medications = list(patient_schedules_collection.find(
        {"patient_username": patient["username"]}
    ).sort("scheduled_time", 1))
    for medication in medications:
        medication.pop("_id", None)
    history = list(medication_history_collection.find({"patient_username": patient["username"]}, {"_id": 0}).sort("taken_at", -1))
    return {"status": "success", "patient_id": patient["patient_id"], "medications": medications, "history": history}


__all__ = ["has_accepted_access"]
