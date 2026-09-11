import os
import logging
import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile, Query

from backend.app.utils.file_handler import save_uploaded_file

from backend.app.services.voice_search_service import (
    detect_transcript_language,
    find_disease_medicines,
    search_medicine_from_transcript,
    transcribe_audio,
)
from backend.app.services.medicine_service import search_medicine


router = APIRouter()
logger = logging.getLogger(__name__)
VOICE_TRANSCRIPTION_TIMEOUT_SECONDS = 45


def _remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


QUESTION_CUES = {
    "side_effects": (
        "side effect", "side effects", "adverse", "ಬದಿ ಪರಿಣಾಮ", "ಅಡ್ಡ ಪರಿಣಾಮ",
        "ದುಷ್ಪರಿಣಾಮ", "ಸೈಡ್ ಎಫೆಕ್ಟ್",
    ),
    "warnings": (
        "warning", "warnings", "danger", "caution", "ಎಚ್ಚರಿಕೆ", "ಅಪಾಯ",
        "ಜಾಗ್ರತೆ",
    ),
    "contraindications": (
        "can i take", "safe to take", "should i take", "contraindication",
        "allergy", "ತೆಗೆದುಕೊಳ್ಳಬಹುದೇ", "ತಿನ್ನಬಹುದೇ", "ಅಲರ್ಜಿ",
    ),
    "description": (
        "what is", "used for", "use", "tell me", "about", "ಏನು", "ಬಳಕೆ",
        "ಬಗ್ಗೆ", "ಮದ್ದು",
    ),
}


def _is_medication_question(transcript):
    normalized_text = str(transcript or "").casefold()
    return "?" in normalized_text or any(
        cue in normalized_text
        for cues in QUESTION_CUES.values()
        for cue in cues
    )


def _question_response(medicine, transcript, lang):
    normalized_text = str(transcript or "").casefold()
    selected_field = "description"
    for field in ("side_effects", "warnings", "contraindications", "description"):
        if any(cue in normalized_text for cue in QUESTION_CUES[field]):
            selected_field = field
            break

    response_text = medicine.get(selected_field)
    if response_text:
        return response_text, selected_field

    return medicine.get("description") or medicine.get("disease"), "description"


def _clarification_response(lang):
    return {
        "status": "clarification_required",
        "message": "Please provide or select a medicine name, or use the prescription/OCR feature first.",
        "response_text": None,
        "response_language": lang,
        "clarification_required": True,
    }


@router.post("/voice-search")
async def voice_search(
    file: UploadFile = File(...),
    lang: str = Query("auto"),
    medicine_name: str | None = Query(None),
):
    try:
        file_path = save_uploaded_file(file)
    except Exception as err:
        logger.exception("Voice upload failed: %s", err)
        raise HTTPException(status_code=400, detail="The audio file could not be uploaded.") from err

    try:
        logger.info(
            "Voice upload received: filename=%s content_type=%s file_size=%d",
            file.filename,
            file.content_type,
            os.path.getsize(file_path),
        )
        logger.info("Voice processing started")
        transcription_task = asyncio.create_task(
            asyncio.to_thread(transcribe_audio, file_path, lang)
        )
        try:
            transcript_text = await asyncio.wait_for(
                asyncio.shield(transcription_task),
                timeout=VOICE_TRANSCRIPTION_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as err:
            transcription_task.add_done_callback(
                lambda completed_task: _remove_file(file_path)
            )
            raise HTTPException(
                status_code=408,
                detail="Voice processing took too long. Please record a shorter clip and try again.",
            ) from err

        if not transcript_text:
            raise HTTPException(
                status_code=400,
                detail="Unable to transcribe the provided audio file.",
            )

        logger.info("Voice processing completed")

        detected_language = detect_transcript_language(transcript_text, requested_lang=lang)
        is_question = _is_medication_question(transcript_text)

        if medicine_name:
            medicine = search_medicine(medicine_name, lang=detected_language)
            if medicine:
                response_text, response_field = _question_response(
                    medicine,
                    transcript_text,
                    detected_language,
                )
                return {
                    "status": "success",
                    "detected_text": transcript_text,
                    "detected_medicine": medicine.get("drug_name"),
                    "medicine_details": medicine,
                    "response_text": response_text,
                    "response_language": detected_language,
                    "response_field": response_field,
                    "lang": detected_language,
                    "detected_language": detected_language,
                    "question_about_image_medicine": True,
                }

        medicine, cleaned_words = search_medicine_from_transcript(
            transcript_text,
            lang=detected_language,
        )

        if not medicine and not is_question:
            category_medicines = [
                medicine for medicine in find_disease_medicines(
                    transcript_text,
                    lang=detected_language,
                )
                if medicine
            ]
            if category_medicines:
                disease = category_medicines[0].get("disease", "")
                names = [medicine.get("drug_name") for medicine in category_medicines]
                return {
                    "status": "category_match",
                    "detected_text": transcript_text,
                    "detected_medicine": None,
                    "medicine_details": None,
                    "matching_medicines": category_medicines,
                    "response_text": f"{disease}: {', '.join(names)}",
                    "response_language": detected_language,
                    "lang": detected_language,
                    "detected_language": detected_language,
                }

        if medicine:
            detected_medicine = medicine.get("drug_name") or " ".join(cleaned_words).strip() or transcript_text
            response_text, response_field = _question_response(
                medicine,
                transcript_text,
                detected_language,
            )

            return {
                "status": "success",
                "detected_text": transcript_text,
                "detected_medicine": detected_medicine,
                "medicine_details": medicine,
                "lang": detected_language,
                "detected_language": detected_language,
                "response_text": response_text,
                "response_language": detected_language,
                "response_field": response_field,
            }

        clarification = _clarification_response(detected_language)
        return {
            "status": clarification["status"],
            "detected_text": transcript_text,
            "message": clarification["message"],
            "lang": detected_language,
            "detected_language": detected_language,
            "response_text": clarification["response_text"],
            "response_language": detected_language,
            "clarification_required": clarification["clarification_required"],
        }

    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Voice processing failed: %s", err)
        raise HTTPException(
            status_code=400,
            detail="Unable to process this audio recording. Please record again and try.",
        ) from err
    finally:
        if "transcription_task" not in locals() or transcription_task.done():
            _remove_file(file_path)