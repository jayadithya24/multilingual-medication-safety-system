import pandas as pd
import difflib
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pathlib import Path
from app.db import PATIENT_DB
from app.services.ocr_service import extract_text_from_prescription

router = APIRouter(prefix="/medicine", tags=["Medicine Info"])

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "datasets"

def load_shreyas_dataset(lang: str) -> pd.DataFrame:
    dataset_files = {
        "en": "english_master_dataset.csv",
        "kn": "kannada_master_dataset.csv",
        "tlu": "tulu_master_dataset.csv"
    }
    file_name = dataset_files.get(lang.lower(), "english_master_dataset.csv")
    file_path = DATASETS_DIR / file_name

    if not file_path.exists():
        file_path = DATASETS_DIR / "english_master_dataset.csv"

    return pd.read_csv(file_path)

def extract_column_value(record: dict, search_keywords: list[str]) -> str:
    for key, value in record.items():
        if any(keyword in str(key).lower() for keyword in search_keywords):
            if pd.notna(value):
                return str(value).strip()
    return "N/A"

@router.post("/upload-prescription")
async def upload_prescription(
    patient_id: str = Form(..., description="Unique Patient ID"),
    caretaker_phone: str = Form("+919876543210", description="Caretaker Phone Number"),
    file: UploadFile = File(...)
):
    """
    Dynamically processes prescription images via OCR and saves the schedule directly to PATIENT_DB.
    """
    image_bytes = await file.read()
    
    # Extract text/medications using OCR Service
    extracted_meds = extract_text_from_prescription(image_bytes)
    
    # Save to dynamic storage
    PATIENT_DB[patient_id] = {
        "caretaker_phone": caretaker_phone,
        "medications": extracted_meds
    }

    return {
        "status": "success",
        "message": f"Prescription processed and saved for Patient {patient_id}",
        "data": PATIENT_DB[patient_id]
    }

@router.get("/lookup")
async def lookup_medicine(
    name: str = Query(..., description="Medicine name to search in CSV"), 
    lang: str = Query("en", description="Language: 'en', 'kn', or 'tlu'")
):
    df = load_shreyas_dataset(lang)
    
    name_col = next((col for col in df.columns if "name" in col.lower() or "drug" in col.lower()), df.columns[0])
    all_names = df[name_col].astype(str).tolist()
    
    match = df[df[name_col].astype(str).str.contains(name, case=False, na=False)]
    
    if match.empty:
        close_matches = difflib.get_close_matches(name, all_names, n=1, cutoff=0.4)
        if close_matches:
            match = df[df[name_col].astype(str) == close_matches[0]]
        else:
            raise HTTPException(status_code=404, detail=f"Medicine '{name}' not found in {lang} dataset")

    row_dict = match.iloc[0].to_dict()

    extracted_medicine_name = extract_column_value(row_dict, ["name", "drug"])
    extracted_indication = extract_column_value(row_dict, ["indication", "disease", "use", "condition"])
    extracted_dosage = extract_column_value(row_dict, ["dosage", "dose", "mg"])
    extracted_timing = extract_column_value(row_dict, ["timing", "frequency", "schedule", "time"])

    return {
        "status": "success",
        "language": lang,
        "extracted_data": {
            "medicine_name": extracted_medicine_name,
            "indication": extracted_indication,
            "dosage": extracted_dosage,
            "timing": extracted_timing,
            "raw_csv_row": row_dict
        }
    }