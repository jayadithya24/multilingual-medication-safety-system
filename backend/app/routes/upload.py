import os
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.services.ocr_service import extract_text

router = APIRouter()


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    suffix = os.path.splitext(file.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = extract_text(tmp_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(exc)}") from exc
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {
        "filename": file.filename,
        "ocr_result": result,
    }