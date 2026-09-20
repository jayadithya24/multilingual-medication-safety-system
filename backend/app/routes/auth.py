from datetime import datetime, timedelta, timezone
import os
from uuid import uuid4
from typing import Literal, Optional
from backend.app.services.google_auth_service import verify_google_credential
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from backend.app.database import doctor_requests_collection, users_collection
from backend.app.auth import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user,
    fake_users_db,
    get_password_hash,
    User,
    Token,
)
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

router = APIRouter(prefix="/auth", tags=["authentication"])


class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., min_length=20, max_length=10000)
    mode: Literal["login", "register"] = "login"
    password: str | None = Field(default=None, max_length=200)


@router.get("/providers")
def auth_providers():
    return {"google_client_id": os.getenv("GOOGLE_CLIENT_ID", "").strip()}


@router.post("/google", response_model=Token)
def login_with_google(payload: GoogleLoginRequest):
    claims = verify_google_credential(payload.credential)
    subject = claims["sub"]
    user = users_collection.find_one({"google_sub": subject})
    if not user:
        existing = users_collection.find_one({"username": claims["email"].strip().lower()})
        if existing:
            if existing.get("role") != "patient" or existing.get("disabled") or existing.get("google_sub"):
                raise HTTPException(403, "This account cannot be linked to this Google identity.")
            if not payload.password:
                raise HTTPException(409, detail={"code": "google_link_required", "message": "Your account is already registered with a password. Confirm that password once to enable Google sign-in."})
            authenticated = authenticate_user({}, existing["username"], payload.password)
            if not authenticated:
                raise HTTPException(401, "Incorrect password. Enter your existing account password to link Google.")
            try:
                result = users_collection.update_one(
                    {"_id": existing["_id"], "google_sub": {"$exists": False}},
                    {"$set": {"google_sub": subject}},
                )
            except DuplicateKeyError as error:
                raise HTTPException(409, "This Google identity is already linked. Please sign in again.") from error
            if result.modified_count != 1:
                raise HTTPException(409, "Account changed while linking. Please sign in again.")
            user = existing
    if not user:
        if payload.mode != "register":
            raise HTTPException(401, "Please register your Google account before signing in.")
        username = claims["email"].strip().lower()
        if users_collection.find_one({"username": username}) or username in fake_users_db:
            raise HTTPException(409, "This email already has an account. Sign in with your existing password.")
        user = {
            "username": username, "email": username,
            "full_name": claims.get("name") or username.split("@")[0],
            "role": "patient", "google_sub": subject, "auth_provider": "google",
            "patient_id": "P-" + uuid4().hex[:12].upper(),
            "age": None, "gender": None, "medical_condition": None,
        }
        try:
            users_collection.insert_one(user)
        except DuplicateKeyError as error:
            user = users_collection.find_one({"google_sub": subject})
            if not user:
                raise HTTPException(409, "This account already exists. Use your existing sign-in method.") from error
    if user.get("role") != "patient" or user.get("disabled"):
        raise HTTPException(403, "This account cannot access the patient portal.")
    token = create_access_token(
        {"sub": user["username"], "role": "patient"},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer", "role": "patient"}


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8, max_length=72)
    confirm_password: str = Field(..., min_length=8, max_length=72)


@router.post("/patient-token", response_model=Token)
def patient_login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user({}, form_data.username, form_data.password)
    if not user or user.disabled or user.role != "patient":
        raise HTTPException(401, "Sign in with your registered patient email and password. New here? Register first.")
    token = create_access_token({"sub": user.username, "role": "patient"}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer", "role": "patient"}


class DoctorRegisterRequest(RegisterRequest):
    doctor_id: str = Field(..., min_length=2)
    specialization: str = Field(..., min_length=2)
    phone: Optional[str] = None
    hospital: Optional[str] = None


def create_doctor_request(payload: DoctorRegisterRequest) -> dict:
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    username = payload.email.strip().lower()
    registration_number = payload.doctor_id.strip()

    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=409, detail="An account already exists for this email.")
    if users_collection.find_one({"license_number": registration_number}):
        raise HTTPException(status_code=409, detail="A doctor account already uses this registration number.")
    if doctor_requests_collection.find_one({"email": username, "status": "pending"}):
        raise HTTPException(status_code=409, detail="A doctor request is already pending for this email.")
    if doctor_requests_collection.find_one({"medical_registration_no": registration_number, "status": "pending"}):
        raise HTTPException(status_code=409, detail="A doctor request is already pending for this registration number.")

    request = {
        "request_id": f"DRQ-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "full_name": payload.name.strip(),
        "email": username,
        "phone": payload.phone.strip() if payload.phone else None,
        "medical_registration_no": registration_number,
        "specialization": payload.specialization.strip(),
        "hospital": payload.hospital.strip() if payload.hospital else None,
        "hashed_password": get_password_hash(payload.password),
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
    }
    try:
        doctor_requests_collection.insert_one(request)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="A doctor request is already pending.")
    return {"status": "pending", "request_id": request["request_id"]}


@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user or user.disabled:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


@router.post("/register", response_model=Token)
def register_patient(payload: RegisterRequest):

    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    username = payload.email.strip().lower()
    if not payload.name.strip() or "@" not in username or len(payload.password.encode("utf-8")) > 72:
        raise HTTPException(400, "Enter a name, valid email, and password no longer than 72 bytes.")

    # Check MongoDB for existing patient
    existing_user = users_collection.find_one({
        "username": username
    })

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    # Generate patient ID
    patient_id = "P-" + uuid4().hex[:12].upper()

    # Create patient document
    patient_document = {
        "username": username,
        "full_name": payload.name.strip(),
        "email": username,
        "role": "patient",

        "hashed_password": get_password_hash(
            payload.password
        ),

        # Patient profile information
        "patient_id": patient_id,
        "age": None,
        "gender": None,
        "medical_condition": None,
    }

    # Save patient to MongoDB
    try:
        users_collection.insert_one(patient_document)
    except DuplicateKeyError as error:
        raise HTTPException(409, "An account with this email already exists.") from error

    # Create login token
    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = create_access_token(
        data={
            "sub": username,
            "role": "patient"
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "patient"
    }


@router.post("/doctor-request")
@router.post("/register-doctor")
def register_doctor(payload: DoctorRegisterRequest):
    """Submit a doctor account for administrator approval."""
    return create_doctor_request(payload)
@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
