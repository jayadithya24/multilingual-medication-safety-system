from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.upload import router as upload_router
from app.routes.medicine import router as medicine_router
from app.routes.interaction import router as interaction_router
from app.routes.voice import router as voice_router

app = FastAPI(
    title="Medication Safety System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(medicine_router)
app.include_router(interaction_router)
app.include_router(voice_router)


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