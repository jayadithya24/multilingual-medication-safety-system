import os

from fastapi import APIRouter, File, HTTPException, UploadFile, Query

from backend.app.utils.file_handler import save_uploaded_file

from backend.app.services.voice_search_service import (
    search_medicine_from_transcript,
    transcribe_audio,
)


router = APIRouter()


@router.post("/voice-search")
async def voice_search(file: UploadFile = File(...), lang: str = Query("en")):
    file_path = save_uploaded_file(file)

    try:
        transcript_text = transcribe_audio(file_path)

        if not transcript_text:
            raise HTTPException(
                status_code=400,
                detail="Unable to transcribe the provided audio file.",
            )

        medicine, cleaned_words = search_medicine_from_transcript(transcript_text, lang=lang)

        if medicine:
            detected_medicine = medicine.get("drug_name") or " ".join(cleaned_words).strip() or transcript_text

            return {
                "status": "success",
                "detected_text": transcript_text,
                "detected_medicine": detected_medicine,
                "medicine_details": medicine,
                "lang": lang,
            }

        return {
            "status": "not_found",
            "detected_text": transcript_text,
            "message": "Medicine not found.",
            "lang": lang,
        }

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)