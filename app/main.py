# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import patient, medicine, voice  # Imported voice router

app = FastAPI(
    title="Multilingual Medication Safety System - Backend",
    version="1.0.0",
    description="Backend APIs for Patient Module, CSV Dataset Lookups, PaddleOCR, and Multilingual Voice Services"
)

# Enable CORS for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(patient.router)
app.include_router(medicine.router)
app.include_router(voice.router)  # Registered voice router

@app.get("/")
def read_root():
    return {
        "status": "Online",
        "system": "Multilingual Medication Safety System",
        "module": "Backend & Patient APIs"
    }