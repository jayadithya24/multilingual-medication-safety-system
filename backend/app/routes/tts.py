from fastapi import APIRouter, Response, Query, HTTPException
from backend.app.services.tts_service import generate_tts_audio

router = APIRouter()


@router.get("/tts")
def get_tts_audio(text: str = Query(..., min_length=1, max_length=5000), lang: str = Query("en")):
    """Return MP3 audio stream for specified text and language."""
    audio_bytes = generate_tts_audio(text, lang)
    if audio_bytes:
        return Response(content=audio_bytes, media_type="audio/mpeg")
    raise HTTPException(503, "The female voice service is unavailable. Please retry; the text remains available.")
