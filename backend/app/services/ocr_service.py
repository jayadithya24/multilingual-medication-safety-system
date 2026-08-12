import os
from functools import lru_cache

import easyocr

from backend.app.services.medicine_service import search_medicine
from backend.app.utils.text_cleaner import clean_detected_text


@lru_cache(maxsize=1)
def _get_reader():
    try:
        return easyocr.Reader(["en", "kn"])
    except Exception:
        return None


def extract_text(file_path):
    """Run OCR, clean detected text, and return the first matching medicine record."""
    if not file_path or not os.path.exists(file_path):
        return {
            "status": "not_found",
            "message": "OCR input file not found.",
        }

    reader = _get_reader()
    if reader is None:
        return {
            "status": "not_found",
            "message": "OCR reader could not be initialized.",
        }

    try:
        result = reader.readtext(file_path)
        detected_text = []
        for item in result:
            detected_text.append(item[1])

        cleaned_text = clean_detected_text(detected_text)
        for medicine_name in cleaned_text:
            medicine = search_medicine(medicine_name)
            if medicine:
                return {
                    "status": "success",
                    "detected_medicine": medicine_name,
                    "medicine_details": medicine,
                }

        return {
            "status": "not_found",
            "message": "Medicine not found in database.",
        }
    except Exception:
        return {
            "status": "not_found",
            "message": "Medicine not found in database.",
        }


def extract_text_from_image(file=None, file_path=None):
    """Compatibility wrapper for older call sites expecting a file upload object."""
    if file is not None:
        if hasattr(file, "file"):
            file_path = file.file.name
        elif hasattr(file, "filename"):
            file_path = getattr(file, "filename")
    if not file_path or not os.path.exists(file_path):
        return {
            "status": "not_found",
            "message": "OCR input file not found.",
        }
    return extract_text(file_path)
