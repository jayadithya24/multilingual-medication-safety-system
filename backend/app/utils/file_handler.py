import os
import shutil
from uuid import uuid4


UPLOAD_FOLDER = "app/uploads"


def save_uploaded_file(upload_file):

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    extension = upload_file.filename.split(".")[-1]

    unique_filename = f"{uuid4()}.{extension}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return file_path