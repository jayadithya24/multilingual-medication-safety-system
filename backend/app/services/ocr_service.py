import os
import logging
import time
from difflib import SequenceMatcher
from functools import lru_cache

import cv2

from backend.app.services.medicine_service import list_medicine_names, search_medicine


logger = logging.getLogger(__name__)

MAX_OCR_DIMENSION = 1400

# Common Indian brand names found on medicine strips. These map only to drugs
# already present in the project's supported dataset.
BRAND_ALIASES = {
    "brufen": "Ibuprofen",
    "brufen 400": "Ibuprofen",
    "flexon": "Ibuprofen",
    "amlo": "Amlodipine",
    "amlodac": "Amlodipine",
    "amlong": "Amlodipine",
    "glycomet": "Metformin",
    "glucophage": "Metformin",
    "glim": "Glimepiride",
    "amaryl": "Glimepiride",
    "glipizide": "Glipizide",
    " januvia": "Sitagliptin",
    "jardiance": "Empagliflozin",
    "forxiga": "Dapagliflozin",
    "losar": "Losartan",
    "cozaar": "Losartan",
    "envas": "Enalapril",
    "enalapril": "Enalapril",
    "telma": "Telmisartan",
    "aten": "Atenolol",
    "tenormin": "Atenolol",
    "cardivas": "Carvedilol",
    "naprosyn": "Naproxen",
    "hcqs": "Hydroxychloroquine",
    "plaquenil": "Hydroxychloroquine",
    "folitrax": "Methotrexate",
    "celebrex": "Celecoxib",
    "arava": "Leflunomide",
    "colcrys": "Colchicine",
}


@lru_cache(maxsize=3)
def _get_reader(lang="en"):
    try:
        import site
        import sys

        # Uvicorn reload workers can start with a reduced sys.path on Windows.
        # Re-add the interpreter's site-packages before loading PaddleOCR.
        for package_dir in site.getsitepackages():
            if package_dir not in sys.path:
                sys.path.insert(0, package_dir)

        from paddleocr import PaddleOCR

        return PaddleOCR(
            lang="en",
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="PP-OCRv5_mobile_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
        )
    except Exception as err:
        logger.exception(
            "PaddleOCR initialization failed (%s: %s) using %s",
            type(err).__name__,
            err,
            sys.executable if "sys" in locals() else "unknown interpreter",
        )
        return None


def warm_up_reader():
    """Load the cached OCR reader during application startup."""
    started_at = time.perf_counter()
    reader = _get_reader("en")
    if reader is None:
        logger.error("PaddleOCR reader is unavailable after %.2f seconds", time.perf_counter() - started_at)
    else:
        logger.info("PaddleOCR reader ready in %.2f seconds", time.perf_counter() - started_at)
    return reader is not None


def _extract_paddle_result(result):
    """Normalize PaddleOCR 3.x results into text and confidence pairs."""
    if isinstance(result, dict):
        texts = result.get("rec_texts", [])
        scores = result.get("rec_scores", [])
    else:
        texts = getattr(result, "rec_texts", None)
        scores = getattr(result, "rec_scores", None)
        if texts is None and hasattr(result, "json"):
            try:
                import json

                payload = result.json
                payload = payload() if callable(payload) else payload
                if isinstance(payload, str):
                    payload = json.loads(payload)
                texts = payload.get("rec_texts", [])
                scores = payload.get("rec_scores", [])
            except Exception:
                texts, scores = [], []

    pairs = []
    for index, text in enumerate(texts or []):
        confidence = float(scores[index]) if index < len(scores or []) else 0.0
        if text and confidence >= 0.35:
            pairs.append((str(text).strip(), confidence))
    return pairs


def _read_detected_text(reader, file_path):
    """Run PaddleOCR against original and enhanced image variants."""
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
    # Avoid enlarging small images: it significantly increases PaddleOCR
    # inference time and does not improve clear medicine-pack text reliably.

    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    ).apply(grayscale)
    thresholded = cv2.threshold(
        enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]
    adaptive = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )
    # PaddleOCR inference is expensive. Start with the original image and use
    # one enhanced fallback only when the first pass finds no text.
    variants = [
        image,
        cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR),
    ]
    detected_text = []

    for index, variant in enumerate(variants):
        try:
            results = reader.predict(input=variant)
            for result in results or []:
                detected_text.extend(
                    text for text, _confidence in _extract_paddle_result(result)
                )
            if detected_text:
                break
        except Exception as err:
            logger.warning("PaddleOCR pass failed for %s: %s", file_path, err)

    detected_text = list(dict.fromkeys(detected_text))
    logger.info(
        "PaddleOCR completed in %.2f seconds; detected %d text regions",
        time.perf_counter() - started_at,
        len(detected_text),
    )
    return detected_text


def _find_supported_medicine(raw_text, medicines):
    normalized_text = " ".join(raw_text.lower().split())
    normalized_compact = " ".join(
        "".join(character for character in word if character.isalnum())
        for word in normalized_text.split()
    )

    for alias, medicine in BRAND_ALIASES.items():
        alias_normalized = "".join(character for character in alias if character.isalnum())
        if alias_normalized and alias_normalized in normalized_compact:
            return medicine

    for medicine in medicines:
        medicine_normalized = "".join(
            character for character in medicine.lower() if character.isalnum()
        )
        if medicine_normalized in normalized_compact:
            return medicine

    # Correct only small OCR errors against the known dataset; never invent a name.
    words = [word for word in normalized_text.split() if len(word) >= 4]
    best_medicine = None
    best_score = 0.0
    for medicine in medicines:
        score = max(
            (SequenceMatcher(None, medicine.lower(), word).ratio() for word in words),
            default=0.0,
        )
        if score > best_score:
            best_medicine, best_score = medicine, score
    return best_medicine if best_score >= 0.86 else None


def extract_text(file_path, lang: str = "en"):
    """Run OCR, clean detected text, and return all matching medicine records."""
    if not file_path or not os.path.exists(file_path):
        return {
            "status": "not_found",
            "message": "OCR input file not found.",
        }

    detected_text = []
    requested_lang = (lang or "en").strip().lower()
    reader = _get_reader(requested_lang)

    if reader is not None:
        detected_text = _read_detected_text(reader, file_path)

    filename = os.path.basename(file_path).lower()

    # Extract all matching medicines from detected text or filename
    all_medicines = list_medicine_names(lang=requested_lang)
    found_medicines = []
    found_details = []

    # Check text tokens
    full_text = " ".join(detected_text).lower() + " " + filename

    medicine_match = _find_supported_medicine(full_text, all_medicines)
    if medicine_match:
        med_info = search_medicine(medicine_match, lang=lang)
        if med_info:
            found_medicines.append(medicine_match)
            found_details.append(med_info)
    for med in all_medicines:
        if med.lower() in full_text:
            med_info = search_medicine(med, lang=requested_lang)
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
        "lang": requested_lang,
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
    requested_lang = (lang or "en").strip().lower()

    try:
        reader = _get_reader(requested_lang)
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
            "lang": requested_lang,
        }

    text_lower = raw_text.lower()

    # ---------------------------------------------------------
    # 1. Detect medicine name using your existing medicine DB
    # ---------------------------------------------------------

    all_medicines = list_medicine_names(lang=requested_lang)
    found_medicines = []
    found_details = []

    medicine_match = _find_supported_medicine(raw_text, all_medicines)
    if medicine_match:
        med_info = search_medicine(medicine_match, lang=lang)
        if med_info:
            found_medicines.append(medicine_match)
            found_details.append(med_info)
    for med in all_medicines:
        if med.lower() in text_lower:
            med_info = search_medicine(med, lang=requested_lang)
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
        "lang": requested_lang,
        "message": (
            "Prescription details detected."
            if medicine
            else "Text was detected, but no supported medicine matched this project's 30-medicine dataset. Please verify the name manually."
        ),
    }