import os
import logging
import asyncio
from typing import Optional

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


def _medicine_not_found_message(lang):
    messages = {
        "kn": "ಈ ಮಾತ್ರೆ ಈ ವ್ಯವಸ್ಥೆಯಲ್ಲಿ ಇಲ್ಲ. ದಯವಿಟ್ಟು ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        "tulu": "ಈ ಮರ್ದ್ ಈ ವ್ಯವಸ್ಥೆಡ್ ಇಜ್ಜಿ. ದಯೆ ಮಲ್ತ್‌ದ್ ವೈದ್ಯೆರೆನ್ ಸಂಪರ್ಕ ಮಲ್ಪುಲೆ.",
    }
    return messages.get(
        lang,
        "This medicine is not available in this system. Please consult a doctor.",
    )


def _remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def _question_response(medicine, transcript, lang):
    disease = str(medicine.get("disease") or "").strip()
    question = transcript.lower()
    asks_about_use = any(phrase in question for phrase in ["for", "used", "use", "sugar", "bp", "pressure", "diabetes", "ಮಧುಮೇಹ", "ಒತ್ತಡ"])

    if not asks_about_use:
        return medicine.get("description") or disease

    asks_sugar = any(phrase in question for phrase in ["sugar", "diabetes", "ಮಧುಮೇಹ"])
    asks_pressure = any(phrase in question for phrase in ["bp", "blood pressure", "pressure", "ಒತ್ತಡ"])
    disease_is_sugar = any(phrase in disease.lower() for phrase in ["diabetes", "ಮಧುಮೇಹ", "ಸಕ್ಕರೆ ಕಾಯಿಲೆ"])
    disease_is_pressure = any(phrase in disease.lower() for phrase in ["pressure", "hypertension", "ಒತ್ತಡ"])
    is_correct_use = (asks_sugar and disease_is_sugar) or (asks_pressure and disease_is_pressure)

    if lang == "kn":
        answer = "ಹೌದು" if is_correct_use else "ಇಲ್ಲ"
        return f"{answer}, {medicine.get('drug_name')} {disease} ಗೆ ಬಳಸುವ ಔಷಧಿ."
    if lang == "tulu":
        answer = "ಅಂದ್" if is_correct_use else "ಅತ್ತ್"
        return f"{answer}, {medicine.get('drug_name')} {disease}ಗ್ ಬಳಕೆ ಆಪುಂಡು."
    answer = "Yes" if is_correct_use else "No"
    return f"{answer}, {medicine.get('drug_name')} is used for {disease}."


@router.post("/voice-search")
async def voice_search(
    file: UploadFile = File(...),
    lang: str = Query("auto"),
    medicine_name: Optional[str] = Query(None),
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
        if detected_language is None:
            return {
                "status": "language_uncertain",
                "detected_text": transcript_text,
                "detected_language": None,
                "response_language": None,
                "message": "Please say a short sentence with the medicine name, or choose English, Kannada, or Tulu and search again.",
            }

        if medicine_name:
            medicine = search_medicine(medicine_name, lang=detected_language)
            if medicine:
                response_text = _question_response(medicine, transcript_text, detected_language)
                return {
                    "status": "success",
                    "detected_text": transcript_text,
                    "detected_medicine": medicine.get("drug_name"),
                    "medicine_details": medicine,
                    "response_text": response_text,
                    "response_language": detected_language,
                    "lang": detected_language,
                    "detected_language": detected_language,
                    "question_about_image_medicine": True,
                }

        medicine, cleaned_words = search_medicine_from_transcript(
            transcript_text,
            lang=detected_language,
        )

        if not medicine:
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
            response_text = _question_response(medicine, transcript_text, detected_language)

            return {
                "status": "success",
                "detected_text": transcript_text,
                "detected_medicine": detected_medicine,
                "medicine_details": medicine,
                "lang": detected_language,
                "detected_language": detected_language,
                "response_text": response_text,
                "response_language": detected_language,
            }

        not_found_message = _medicine_not_found_message(detected_language)
        return {
            "status": "not_found",
            "detected_text": transcript_text,
            "message": not_found_message,
            "lang": detected_language,
            "detected_language": detected_language,
            "response_text": not_found_message,
            "response_language": detected_language,
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
