import asyncio
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.env_loader import load_project_env

load_project_env()

from backend.app.routes.upload import router as upload_router
from backend.app.routes.mongo_loader_route import router as mongo_loader_router
from backend.app.routes.auth import router as auth_router
from backend.app.routes.neo4j import router as neo4j_router
from backend.app.routes.interaction import router as interaction_router
from backend.app.routes.medicine import router as medicine_router
from backend.app.routes.voice import router as voice_router
from backend.app.routes.tts import router as tts_router
from backend.app.routes.patient_schedule import router as patient_schedule_router
from backend.app.routes.patient_drugs import router as patient_drugs_router
from backend.app.routes.patient import router as patient_router
from backend.app.routes.access_requests import router as access_requests_router
from backend.app.routes.doctor_requests import router as doctor_requests_router
from backend.app.services.ocr_service import warm_up_reader
from backend.app.routes.fcm import router as fcm_router
from backend.app.services.fcm_service import reminder_loop

app = FastAPI(
    title="Medication Safety System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(upload_router)
app.include_router(auth_router)
app.include_router(mongo_loader_router)
app.include_router(neo4j_router)
app.include_router(interaction_router)
app.include_router(medicine_router)
app.include_router(voice_router)
app.include_router(tts_router)
app.include_router(patient_schedule_router)
app.include_router(patient_drugs_router)
app.include_router(patient_router)
app.include_router(access_requests_router)
app.include_router(doctor_requests_router)
app.include_router(fcm_router)

reminder_stop_event = asyncio.Event()
reminder_task = None


@app.on_event("startup")
def warm_up_ocr():
    # PaddleOCR loads native model libraries; defer that work for Uvicorn reload.
    if os.getenv("WARM_UP_OCR", "false").lower() == "true":
        warm_up_reader()


@app.on_event("startup")
async def start_medication_reminder_worker():
    global reminder_task
    reminder_stop_event.clear()
    reminder_task = asyncio.create_task(reminder_loop(reminder_stop_event))


@app.on_event("shutdown")
async def stop_medication_reminder_worker():
    reminder_stop_event.set()
    if reminder_task:
        await reminder_task


@app.get("/")
def root():
    return {
        "message": "Medication Safety System Backend Running"
    }


@app.get("/health")
def health():
    return {
        "status": "running",
        "project": "Multilingual Medication Safety System"
    }