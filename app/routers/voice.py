# app/routers/voice.py

from fastapi import APIRouter, Response, Query
from pydantic import BaseModel
from app.services.voice_service import generate_conversational_response, text_to_speech_bytes

router = APIRouter(prefix="/voice", tags=["Voice Services"])

class VoiceQueryRequest(BaseModel):
    medicine_name: str
    user_query: str
    lang: str = "kn"

@router.post("/query-text")
def query_voice_text(payload: VoiceQueryRequest):
    """Query medicine details by voice transcript and get text response."""
    response_text = generate_conversational_response(
        medicine_name=payload.medicine_name,
        user_query=payload.user_query,
        lang=payload.lang
    )
    return {
        "status": "success",
        "medicine_name": payload.medicine_name,
        "user_query": payload.user_query,
        "response_text": response_text,
        "language": payload.lang
    }

@router.post("/query-audio")
def query_voice_audio(payload: VoiceQueryRequest):
    """Query medicine details and return spoken MP3 audio response directly."""
    response_text = generate_conversational_response(
        medicine_name=payload.medicine_name,
        user_query=payload.user_query,
        lang=payload.lang
    )
    audio_bytes = text_to_speech_bytes(text=response_text, lang=payload.lang)
    
    return Response(content=audio_bytes, media_type="audio/mpeg")