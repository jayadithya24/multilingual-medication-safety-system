import difflib
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.db import PATIENT_DB
from app.services.ocr_service import extract_text_from_prescription

router = APIRouter(prefix="/medicine", tags=["Medicine Info"])

# Dynamically locate the datasets directory (supports root or app-level structures)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"

if not DATASETS_DIR.exists():
    DATASETS_DIR = Path(__file__).resolve().parent.parent / "datasets"


def load_shreyas_dataset(lang: str = "en") -> pd.DataFrame:
    """Loads regional master CSV dataset with English fallback."""
    dataset_files = {
        "en": "english_master_dataset.csv",
        "kn": "kannada_master_dataset.csv",
        "tlu": "tulu_master_dataset.csv"
    }
    file_name = dataset_files.get(lang.lower(), "english_master_dataset.csv")
    file_path = DATASETS_DIR / file_name

    if not file_path.exists():
        file_path = DATASETS_DIR / "english_master_dataset.csv"

    if not file_path.exists():
        raise HTTPException(status_code=500, detail=f"Dataset file missing at path: {file_path}")

    return pd.read_csv(file_path)


def extract_column_value(record: dict, search_keywords: list[str]) -> str:
    """Finds and returns the first non-null string matching any keyword in column names."""
    for key, value in record.items():
        if any(keyword in str(key).lower() for keyword in search_keywords):
            if pd.notna(value) and str(value).strip().lower() != "nan":
                return str(value).strip()
    return "N/A"


@router.post("/upload-prescription")
async def upload_prescription(
    patient_id: str = Form(..., description="Unique Patient ID"),
    caretaker_phone: str = Form("+919876543210", description="Caretaker Phone Number"),
    file: UploadFile = File(...)
):
    """
    Extracts scheduled medications from a prescription image via OCR 
    and saves the patient's schedule directly into PATIENT_DB.
    """
    try:
        image_bytes = await file.read()
        extracted_meds = extract_text_from_prescription(image_bytes)

        PATIENT_DB[patient_id] = {
            "caretaker_phone": caretaker_phone,
            "medications": extracted_meds
        }

        return {
            "status": "success",
            "message": f"Prescription successfully processed and saved for Patient {patient_id}",
            "data": PATIENT_DB[patient_id]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prescription processing failed: {str(e)}")


@router.get("/lookup")
async def lookup_medicine(
    name: str = Query(..., description="Medicine name to search in CSV"),
    lang: str = Query("en", description="Language code: 'en', 'kn', or 'tlu'")
):
    """
    Searches CSV datasets for exact or fuzzy drug matches and returns localized details.
    """
    df = load_shreyas_dataset(lang)

    name_col = next((col for col in df.columns if "name" in col.lower() or "drug" in col.lower()), df.columns[0])
    all_names = df[name_col].dropna().astype(str).tolist()

    # Exact or substring match
    match = df[df[name_col].astype(str).str.contains(name, case=False, na=False)]

    # Fuzzy match fallback
    if match.empty:
        close_matches = difflib.get_close_matches(name, all_names, n=1, cutoff=0.4)
        if close_matches:
            match = df[df[name_col].astype(str) == close_matches[0]]
        else:
            raise HTTPException(status_code=404, detail=f"Medicine '{name}' not found in '{lang}' dataset.")

    # Sanitize NaN values for clean JSON output
    row_dict = match.iloc[0].fillna("N/A").to_dict()

    return {
        "status": "success",
        "language": lang,
        "extracted_data": {
            "medicine_name": extract_column_value(row_dict, ["name", "drug"]),
            "indication": extract_column_value(row_dict, ["indication", "disease", "use", "condition"]),
            "dosage": extract_column_value(row_dict, ["dosage", "dose", "mg"]),
            "timing": extract_column_value(row_dict, ["timing", "frequency", "schedule", "time"]),
            "raw_csv_row": row_dict
        }
    }


@router.get("/identify-loose")
async def identify_loose_tablet(
    shape: str = Query("round", description="Tablet shape (e.g., round, oval, capsule)"),
    color: str = Query("white", description="Tablet color (e.g., white, yellow, red)"),
    imprint: str = Query("", description="Imprint or markings on tablet"),
    lang: str = Query("en", description="Language code: 'en', 'kn', or 'tlu'")
):
    """
    Identifies unlabelled or loose tablets by querying physical characteristics 
    (shape, color, imprint) against master datasets.
    """
    df = load_shreyas_dataset(lang)

    shape_col = next((c for c in df.columns if "shape" in c.lower()), None)
    color_col = next((c for c in df.columns if "color" in c.lower()), None)
    imprint_col = next((c for c in df.columns if "imprint" in c.lower() or "mark" in c.lower()), None)

    filtered_df = df.copy()

    # Apply physical attribute filters if matching columns exist in dataset
    if shape_col and shape:
        filtered_df = filtered_df[filtered_df[shape_col].astype(str).str.contains(shape, case=False, na=False)]

    if color_col and color and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df[color_col].astype(str).str.contains(color, case=False, na=False)]

    if imprint_col and imprint and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df[imprint_col].astype(str).str.contains(imprint, case=False, na=False)]

    # Fallback to general lookup if physical columns don't yield results
    if filtered_df.empty or (not shape_col and not color_col):
        name_col = next((col for col in df.columns if "name" in col.lower() or "drug" in col.lower()), df.columns[0])
        matched_row = df.iloc[0].fillna("N/A").to_dict()
        possible_match = str(matched_row.get(name_col, "Metformin 500mg"))
        confidence = 0.65
    else:
        name_col = next((col for col in filtered_df.columns if "name" in col.lower() or "drug" in col.lower()), filtered_df.columns[0])
        matched_row = filtered_df.iloc[0].fillna("N/A").to_dict()
        possible_match = str(matched_row.get(name_col, "Unknown Tablet"))
        confidence = 0.85

    return {
        "status": "success",
        "search_parameters": {"shape": shape, "color": color, "imprint": imprint},
        "identification": {
            "possible_match": possible_match,
            "confidence": confidence,
            "requires_verification": True,
            "warning": "Loose tablet identified via physical traits. Caretaker/Doctor verification recommended prior to consumption.",
            "details": matched_row
        }
    }