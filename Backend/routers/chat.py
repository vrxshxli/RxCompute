import os
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
import requests
from sqlalchemy.orm import Session

from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_FOLDER, CLOUDINARY_UPLOAD_PRESET
from database import get_db
from dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/chat", tags=["Chat"])


def _upload_to_cloudinary(content: bytes, filename: str) -> str:
    if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_UPLOAD_PRESET:
        raise RuntimeError("Cloudinary is not configured")
    url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/auto/upload"
    files = {"file": (filename, content)}
    data = {"upload_preset": CLOUDINARY_UPLOAD_PRESET}
    if CLOUDINARY_FOLDER:
        data["folder"] = CLOUDINARY_FOLDER
    resp = requests.post(url, files=files, data=data, timeout=20)
    if resp.status_code < 200 or resp.status_code >= 300:
        raise RuntimeError(f"Cloudinary upload failed: {resp.status_code} {resp.text}")
    payload = resp.json()
    secure_url = payload.get("secure_url")
    if not secure_url:
        raise RuntimeError("Cloudinary upload response missing secure_url")
    return secure_url


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

    content = await file.read()
    safe_name = f"{uuid.uuid4().hex}{ext}"

    # Prefer Cloudinary for persistent/public fetch from pharmacy dashboard.
    if CLOUDINARY_CLOUD_NAME and CLOUDINARY_UPLOAD_PRESET:
        try:
            cloud_url = _upload_to_cloudinary(content, safe_name)
            return {
                "message": "Prescription uploaded to Cloudinary",
                "file_url": cloud_url,
                "original_name": file.filename,
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {exc}")

    # Local fallback only when Cloudinary env vars are not configured.
    uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads", "prescriptions")
    uploads_dir = os.path.abspath(uploads_dir)
    os.makedirs(uploads_dir, exist_ok=True)
    final_path = os.path.join(uploads_dir, safe_name)
    with open(final_path, "wb") as out:
        out.write(content)

    return {
        "message": "Prescription uploaded",
        "file_url": f"/uploads/prescriptions/{safe_name}",
        "original_name": file.filename,
    }
