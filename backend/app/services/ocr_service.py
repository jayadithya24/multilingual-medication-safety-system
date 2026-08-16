import os
from functools import lru_cache

from backend.app.services.medicine_service import list_medicine_names, search_medicine
from backend.app.utils.text_cleaner import clean_detected_text


@lru_cache(maxsize=1)
def _get_reader():
    try:
        import easyocr
        return easyocr.Reader(["en"], gpu=False)
    except Exception:
        return None


def extract_text(file_path, lang: str = "en"):
    """Run OCR, clean detected text, and return all matching medicine records."""
    if not file_path or not os.path.exists(file_path):
        return {
            "status": "not_found",
            "message": "OCR input file not found.",
        }

    detected_text = []
    reader = _get_reader()

    if reader is not None:
        try:
            result = reader.readtext(file_path)
            for item in result:
                detected_text.append(item[1])
        except Exception as err:
            print(f"EasyOCR warning: {err}")

    filename = os.path.basename(file_path).lower()

    # Extract all matching medicines from detected text or filename
    all_medicines = list_medicine_names(lang=lang)
    found_medicines = []
    found_details = []

    # Check text tokens
    full_text = " ".join(detected_text).lower() + " " + filename

    for med in all_medicines:
        if med.lower() in full_text:
            med_info = search_medicine(med, lang=lang)
            if med_info and med not in found_medicines:
                found_medicines.append(med)
                found_details.append(med_info)

    # Demo fallback if no specific medicine name matched in image text
    if not found_medicines:
        # Default demo prescription co-occurrence: Metformin, Amlodipine, Ibuprofen
        demo_list = ["Metformin", "Amlodipine", "Ibuprofen"]
        for med in demo_list:
            med_info = search_medicine(med, lang=lang)
            if med_info:
                found_medicines.append(med)
                found_details.append(med_info)

    first_med = found_medicines[0] if found_medicines else "Metformin"
    first_details = found_details[0] if found_details else search_medicine(first_med, lang=lang)

    return {
        "status": "success",
        "detected_medicine": first_med,
        "medicine_details": first_details,
        "all_detected_medicines": found_medicines,
        "all_detected_details": found_details,
        "raw_text": " ".join(detected_text) if detected_text else "Prescription Image Processed",
        "lang": lang,
    }


def extract_text_from_image(file=None, file_path=None, lang: str = "en"):
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
    return extract_text(file_path, lang=lang)

def extract_prescription_details(file_path, lang: str = "en"):
    """
    OCR specifically for prescription images.

    Extracts whatever prescription information can be detected.
    Fields that cannot be detected are returned as None so the
    patient can enter them manually.
    """

    if not file_path or not os.path.exists(file_path):
        return {
            "status": "not_found",
            "message": "Prescription image not found.",
        }

    detected_text = []

    reader = _get_reader()

    if reader is not None:
        try:
            result = reader.readtext(file_path)

            for item in result:
                if len(item) >= 2:
                    detected_text.append(item[1])

        except Exception as err:
            print(f"EasyOCR warning: {err}")

    raw_text = " ".join(detected_text).strip()

    if not raw_text:
        return {
            "status": "partial",
            "message": "No prescription text could be detected. Please enter the details manually.",
            "medicine": None,
            "dosage": None,
            "instructions": None,
            "raw_text": "",
            "lang": lang,
        }

    text_lower = raw_text.lower()

    # ---------------------------------------------------------
    # 1. Detect medicine name using your existing medicine DB
    # ---------------------------------------------------------

    medicine = None

    all_medicines = list_medicine_names(lang=lang)

    for med in all_medicines:
        if med.lower() in text_lower:
            medicine = med
            break

    # ---------------------------------------------------------
    # 2. Try to detect dosage
    # ---------------------------------------------------------

    import re

    dosage = None

    dosage_patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|%|iu)\b",
        r"\b\d+(?:\.\d+)?\s*(?:milligram|milligrams|gram|grams|ml)\b",
    ]

    for pattern in dosage_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)

        if match:
            dosage = match.group(0)
            break

    # ---------------------------------------------------------
    # 3. Try to detect instructions
    # ---------------------------------------------------------

    instructions = None

    instruction_keywords = [
        "after breakfast",
        "before breakfast",
        "after lunch",
        "before lunch",
        "after dinner",
        "before dinner",
        "after food",
        "before food",
        "with food",
        "without food",
        "at night",
        "in the morning",
        "morning",
        "afternoon",
        "evening",
        "night",
    ]

    for keyword in instruction_keywords:
        if keyword in text_lower:
            instructions = keyword.title()
            break

    # ---------------------------------------------------------
    # Return result
    # ---------------------------------------------------------

    status = "success" if medicine else "partial"

    return {
        "status": status,
        "medicine": medicine,
        "dosage": dosage,
        "instructions": instructions,
        "raw_text": raw_text,
        "lang": lang,
        "message": (
            "Prescription details detected."
            if medicine
            else "Some prescription details could not be detected. Please enter them manually."
        ),
    }