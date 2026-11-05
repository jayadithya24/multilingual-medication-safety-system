import asyncio
import sys
import os
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.app.request_limits import RequestLimits
from backend.env_loader import load_project_env

load_project_env()
from backend.app.log_privacy import configure as configure_log_privacy
configure_log_privacy()

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
from backend.app.services.fcm_service import reminder_loop, _firebase
from backend.app.routes.risk_prediction import router as risk_prediction_router

app = FastAPI(
    title="Medication Safety System",
    version="1.0.0"
)

app.add_middleware(RequestLimits)
from backend.app.browser_sessions import ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
if os.getenv("ENABLE_RESEARCH_ML_API", "false").lower() == "true" and os.getenv('ENVIRONMENT', '').lower() != 'production':
    app.include_router(risk_prediction_router)

# Validation errors must not echo passwords, credentials or share codes.
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def safe_validation_error(request, exc):
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]})

reminder_stop_event = asyncio.Event()
reminder_task = None
graph_check_task = None


@app.on_event("startup")
async def start_graph_verification():
    from backend.app.services.graph_health import check_graph
    global graph_check_task
    app.state.graph_check = {"status": "checking"}
    async def monitor():
        while True:
            result = await asyncio.to_thread(check_graph)
            app.state.graph_check = result
            # Recover promptly when Neo4j is started after the API. Healthy graphs
            # still use the lower-frequency check to avoid unnecessary work.
            await asyncio.sleep(30 if result.get("status") == "unavailable" else 300)
    graph_check_task = asyncio.create_task(monitor())


@app.on_event("shutdown")
async def stop_graph_verification():
    if graph_check_task:
        graph_check_task.cancel()
        try:
            await graph_check_task
        except asyncio.CancelledError:
            pass


@app.on_event("startup")
def warm_up_ocr():
    if os.getenv('ENVIRONMENT', '').strip().lower() != 'production':
        logging.getLogger(__name__).warning('DEVELOPMENT MODE: not a production deployment. Run tools/deploy_preflight.py before public deployment.')
    # PaddleOCR loads native model libraries; defer that work for Uvicorn reload.
    if os.getenv("WARM_UP_OCR", "true").lower() == "true":
        warm_up_reader()


@app.on_event("startup")
async def start_medication_reminder_worker():
    global reminder_task
    try:
        await asyncio.to_thread(_firebase)
        app.state.firebase_admin_ready = True
    except Exception as error:
        app.state.firebase_admin_ready = False
        logging.getLogger(__name__).warning("Firebase Admin unavailable (%s); check backend configuration", type(error).__name__)
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
    return {"status": "running"}


from backend.app.auth import get_current_admin, get_current_active_user


@app.get('/doctor/reference-status')
def reference_status(user=Depends(get_current_active_user)):
    if user.role != 'doctor':
        raise HTTPException(403, 'Doctor access required.')
    return {'graph_check': getattr(app.state, 'graph_check', {'status': 'not_checked'})}


@app.get('/admin/health')
def detailed_health(user=Depends(get_current_admin)):
    return {
        "status": "running",
        "graph_check": getattr(app.state, "graph_check", {"status": "not_checked"}),
        "project": "Multilingual Medication Safety System",
        "firebase_admin_ready": getattr(app.state, "firebase_admin_ready", False),
        "reminder_worker_running": reminder_task is not None and not reminder_task.done(),
        "reminder_timezone": os.getenv("REMINDER_TIMEZONE", "Asia/Kolkata"),
        "reminder_poll_seconds": max(1, int(os.getenv("REMINDER_POLL_SECONDS", "2"))),
    }
