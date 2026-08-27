import os
import logging
import time
from functools import lru_cache

import cv2

from backend.app.services.medicine_service import list_medicine_names, search_medicine


logger = logging.getLogger(__name__)

MAX_OCR_DIMENSION = 1600


@lru_cache(maxsize=1)
def _get_reader():
    try:
        import easyocr
        return easyocr.Reader(["en"], gpu=False)
    except Exception as err:
        logger.exception("EasyOCR initialization failed: %s", err)
        return None


def warm_up_reader():
    """Load the cached OCR reader during application startup."""
    started_at = time.perf_counter()
    reader = _get_reader()
    if reader is None:
        logger.error("EasyOCR reader is unavailable after %.2f seconds", time.perf_counter() - started_at)
    else:
        logger.info("EasyOCR reader ready in %.2f seconds", time.perf_counter() - started_at)
    return reader is not None


def _read_detected_text(reader, file_path):
    """Preprocess an image once and run one bounded EasyOCR pass."""
    started_at = time.perf_counter()
    image = cv2.imread(file_path, cv2.IMREAD_COLOR)
    if image is None:
        logger.error("OCR could not decode image: %s", file_path)
        return []

    original_height, original_width = image.shape[:2]
    logger.info("OCR image dimensions: %sx%s", original_width, original_height)

    largest_dimension = max(original_width, original_height)
    if largest_dimension > MAX_OCR_DIMENSION:
        scale = MAX_OCR_DIMENSION / largest_dimension
        image = cv2.resize(
            image,
            (int(original_width * scale), int(original_height * scale)),
            interpolation=cv2.INTER_AREA,
        )

    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed_image = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    ).apply(grayscale)

    try:
        result = reader.readtext(
            processed_image,
            canvas_size=MAX_OCR_DIMENSION,
            mag_ratio=1.0,
            batch_size=1,
        )
    except Exception as err:
        logger.exception("EasyOCR read failed for %s: %s", file_path, err)
        return []

    detected_text = [item[1] for item in result if len(item) >= 2 and item[1]]
    logger.info(
        "OCR completed in %.2f seconds; detected %d text regions",
        time.perf_counter() - started_at,
        len(detected_text),
    )
    return detected_text


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
        detected_text = _read_detected_text(reader, file_path)

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

    first_med = found_medicines[0] if found_medicines else None
    first_details = found_details[0] if found_details else None

    return {
        "status": "success" if detected_text else "partial",
        "detected_medicine": first_med,
        "medicine_details": first_details,
        "all_detected_medicines": found_medicines,
        "all_detected_details": found_details,
        "raw_text": " ".join(detected_text),
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

    started_at = time.perf_counter()
    logger.info("OCR started: %s", file_path)
    detected_text = []

    try:
        reader = _get_reader()
        if reader is not None:
            detected_text = _read_detected_text(reader, file_path)
    except Exception as err:
        logger.exception("Prescription OCR failed safely for %s: %s", file_path, err)
    finally:
        logger.info(
            "Prescription OCR request completed in %.2f seconds",
            time.perf_counter() - started_at,
        )

    raw_text = " ".join(detected_text).strip()

    if not raw_text:
        return {
            "status": "partial",
            "message": "No prescription text could be detected. Please enter the details manually.",
            "medicine": None,
            "dosage": None,
            "instructions": None,
            "raw_text": "",
            "detected_medicine": None,
            "all_detected_medicines": [],
            "medicine_details": None,
            "all_detected_details": [],
            "lang": lang,
        }

    text_lower = raw_text.lower()

    # ---------------------------------------------------------
    # 1. Detect medicine name using your existing medicine DB
    # ---------------------------------------------------------

    all_medicines = list_medicine_names(lang=lang)
    found_medicines = []
    found_details = []

    for med in all_medicines:
        if med.lower() in text_lower:
            med_info = search_medicine(med, lang=lang)
            if med_info:
                found_medicines.append(med)
                found_details.append(med_info)

    medicine = found_medicines[0] if found_medicines else None

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
        "detected_medicine": medicine,
        "all_detected_medicines": found_medicines,
        "medicine_details": found_details[0] if found_details else None,
        "all_detected_details": found_details,
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