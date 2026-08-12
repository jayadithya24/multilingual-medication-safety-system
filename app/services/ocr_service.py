import io
import re
import cv2
import os
import pandas as pd
import numpy as np
from PIL import Image
from pathlib import Path
from paddleocr import PaddleOCR

# Initialize PaddleOCR engine once globally
ocr = PaddleOCR(use_angle_cls=True, lang='en')

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "datasets"

def get_known_medicines() -> list[str]:
    """Dynamically extracts all drug names present across all CSV datasets."""
    known_meds = set()
    for dataset_file in ["english_master_dataset.csv", "kannada_master_dataset.csv", "tulu_master_dataset.csv"]:
        file_path = DATASETS_DIR / dataset_file
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                name_col = next((c for c in df.columns if "name" in c.lower() or "drug" in c.lower()), df.columns[0])
                for val in df[name_col].dropna().astype(str):
                    if len(val.strip()) > 2:
                        known_meds.add(val.strip().lower())
            except Exception:
                pass
    return list(known_meds)

def parse_time_slot(line_text: str) -> str:
    """Dynamically converts timing text or medical shorthand (e.g., '1-0-1', 'BD', 'morning') into slots."""
    text = line_text.lower()
    
    if any(k in text for k in ["morning", "1-0-0", "breakfast", "am", "ಬೆಳಿಗ್ಗೆ", "ಕಾಂಡೆ"]):
        return "morning"
    elif any(k in text for k in ["afternoon", "0-1-0", "lunch", "pm", "ಮಧ್ಯಾಹ್ನ", "ಮದ್ಯಾನ"]):
        return "afternoon"
    elif any(k in text for k in ["night", "evening", "0-0-1", "dinner", "hs", "ರಾತ್ರಿ", "ರಾತ್ರಿ"]):
        return "night"
    
    return "morning"  # Default fallback slot

def extract_text_from_prescription(image_bytes: bytes) -> list[dict]:
    """
    Extracts raw OCR lines, matches recognized medicine names against CSV datasets,
    and returns dynamic structured prescription schedules.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    np_img = np.array(image)
    cv_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)

    results = ocr.ocr(cv_img, cls=True)
    extracted_lines = []

    if results and results[0]:
        for line in results[0]:
            text, confidence = line[1]
            if confidence > 0.4:
                extracted_lines.append(text.strip())

    full_text = " ".join(extracted_lines)
    known_meds = get_known_medicines()

    parsed_schedule = []
    
    # 1. Match detected text words against known medicine names in dataset
    for line in extracted_lines:
        line_clean = line.lower()
        matched_med = None
        
        for med in known_meds:
            if med in line_clean or line_clean in med:
                matched_med = med.title()
                break

        if matched_med:
            # Dynamic Dosage Extraction (e.g., 500mg, 5ml, 1 tablet)
            dose_match = re.search(r'\b\d+\s*(mg|g|ml)\b', line_clean)
            dose = dose_match.group(0) if dose_match else "1 tablet"

            slot = parse_time_slot(line_clean)

            parsed_schedule.append({
                "medicine_name": matched_med,
                "scheduled_slot": slot,
                "dose": dose,
                "is_taken": False
            })

    # Fallback: If no dataset drug name matched directly, extract capitalised text blocks
    if not parsed_schedule and extracted_lines:
        for line in extracted_lines:
            words = [w for w in line.split() if w.isalpha() and len(w) > 3]
            if words:
                parsed_schedule.append({
                    "medicine_name": words[0].title(),
                    "scheduled_slot": parse_time_slot(line),
                    "dose": "1 tablet",
                    "is_taken": False
                })

    return parsed_schedule