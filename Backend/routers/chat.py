import os
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/upload-prescription")
async def upload_prescription(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del db
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    allowed_ext = {".jpg", ".jpeg", ".png", ".pdf", ".webp"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads", "prescriptions")
    uploads_dir = os.path.abspath(uploads_dir)
    os.makedirs(uploads_dir, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}{ext}"
    final_path = os.path.join(uploads_dir, safe_name)
    content = await file.read()
    with open(final_path, "wb") as out:
        out.write(content)

    return {
        "message": "Prescription uploaded",
        "file_url": f"/uploads/prescriptions/{safe_name}",
        "original_name": file.filename,
    }
