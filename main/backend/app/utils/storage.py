import os
import shutil
from typing import Optional
from uuid import uuid4
from fastapi import UploadFile
from app.config import settings


async def save_upload_file(upload_file: UploadFile) -> Optional[str]:
    """Persist an UploadFile to disk and return filename, or None."""
    if not upload_file:
        return None

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    extension = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid4().hex}{extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return filename
