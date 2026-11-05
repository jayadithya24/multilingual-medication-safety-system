import os
import tempfile
import asyncio


from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from backend.app.image_validation import validate_image

from backend.app.services.ocr_service import (
    extract_text,
    extract_prescription_details,
)

router = APIRouter()


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), lang: str = Query("en")):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    content = await file.read()
    suffix = await asyncio.to_thread(validate_image, file.filename, content)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await asyncio.to_thread(extract_text, tmp_path, lang)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="OCR processing failed. Please try a clearer image.") from exc
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {
        "filename": file.filename,
        "ocr_result": result,
        "lang": lang,
    }

@router.post("/prescription-ocr")
async def prescription_ocr(
    file: UploadFile = File(...),
    lang: str = Query("en")
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is required"
        )

    content = await file.read()
    suffix = await asyncio.to_thread(validate_image, file.filename, content)

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as tmp:

        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await asyncio.to_thread(
            extract_prescription_details,
            tmp_path,
            lang,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Prescription OCR processing failed. Please try a clearer image."
        ) from exc

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {
        "filename": file.filename,
        "ocr_result": result,
        "lang": lang,
    }
