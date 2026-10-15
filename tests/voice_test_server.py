"""Isolated voice/medicine API for browser tests; no database startup jobs."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes.voice import router as voice_router
from backend.app.routes.medicine import router as medicine_router

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])
app.include_router(voice_router)
app.include_router(medicine_router)
