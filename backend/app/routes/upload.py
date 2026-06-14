from fastapi import APIRouter, UploadFile, File
from app.services.ocr_service import extract_text_from_image

router = APIRouter()

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    
    result = extract_text_from_image()

    return {
        "filename": file.filename,
        "ocr_result": result
    }