from fastapi import APIRouter, UploadFile, File
from app.utils.file_handler import save_uploaded_file
from app.services.ocr_service import extract_text

router = APIRouter()


@router.post("/upload-image")
async def upload_image(
        file: UploadFile = File(...)
):

    file_path = save_uploaded_file(file)

    result = extract_text(file_path)

    return {

        "filename": file.filename,

        "ocr_result": result

    }