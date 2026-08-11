import easyocr

from app.utils.text_cleaner import clean_detected_text
from app.services.medicine_service import search_medicine

# EasyOCR does not support Tulu; 'te' is Telugu and can raise compatibility errors.
# Initialize reader with supported languages only (English + Kannada).
reader = easyocr.Reader(["en", "kn"])


def extract_text(file_path):
    """Run OCR, clean detected text, and return the first matching medicine record."""

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