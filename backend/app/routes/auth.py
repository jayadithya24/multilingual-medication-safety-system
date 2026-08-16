from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from backend.app.database import users_collection
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

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)
    confirm_password: str = Field(..., min_length=4)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
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
async def register_patient(payload: RegisterRequest):

    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    username = payload.email.strip().lower()

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
    patient_count = users_collection.count_documents({
        "role": "patient"
    })

    patient_id = f"P{patient_count + 1:03d}"

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
    users_collection.insert_one(patient_document)

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
@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user