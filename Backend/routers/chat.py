import json
import os
import re
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel, Field
import requests
from sqlalchemy.orm import Session

from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_FOLDER, CLOUDINARY_UPLOAD_PRESET
from config import GEMINI_API_KEY, GEMINI_MODEL
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


_ASSIST_INTENTS = {
    "change_medicine",
    "new_chat",
    "cancel_chat",
    "end_chat",
    "cancel_order",
    "select_option",
    "provide_medicine",
    "provide_dosage",
    "provide_quantity",
    "provide_payment",
    "upload_prescription",
    "unknown",
}


class ChatAssistRequest(BaseModel):
    message: str = Field(min_length=1, max_length=600)
    language_code: str = Field(default="hi")
    stage: str = Field(default="idle")
    current_medicine: str | None = None
    candidate_medicines: list[str] = Field(default_factory=list)


class ChatAssistResponse(BaseModel):
    intent: str = "unknown"
    medicine_query: str | None = None
    response_text: str | None = None
    normalized_text: str | None = None
    confidence: float = 0.0
    source: str = "heuristic"


def _extract_json_blob(raw: str) -> dict:
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        loaded = json.loads(text)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return {}
    try:
        loaded = json.loads(m.group(0))
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        return {}
    return {}


def _heuristic_intent(message: str) -> ChatAssistResponse:
    t = (message or "").strip().lower()
    if not t:
        return ChatAssistResponse()

    change_markers = [
        "change medicine",
        "change the medicine",
        "i wish to change medicine",
        "replace medicine",
        "switch medicine",
        "दवा बदल",
        "medicine change",
        "औषध बदला",
        "औषध बदल",
        "medicine badlo",
    ]
    if any(k in t for k in change_markers):
        return ChatAssistResponse(
            intent="change_medicine",
            confidence=0.85,
            normalized_text=t,
            response_text="Sure, I can help you change medicine. Please share the new medicine name.",
            source="heuristic",
        )

    new_chat_markers = ["new chat", "start new chat", "clear chat", "नई चैट", "नया चैट", "new conversation"]
    if any(k in t for k in new_chat_markers):
        return ChatAssistResponse(intent="new_chat", confidence=0.95, normalized_text=t, source="heuristic")

    cancel_chat_markers = ["cancel chat", "chat cancel", "बात बंद", "chat radd", "cancel conversation"]
    if any(k in t for k in cancel_chat_markers):
        return ChatAssistResponse(intent="cancel_chat", confidence=0.9, normalized_text=t, source="heuristic")

    end_chat_markers = ["end chat", "stop chat", "finish chat", "end conversation", "chat end", "चैट बंद"]
    if any(k in t for k in end_chat_markers):
        return ChatAssistResponse(intent="end_chat", confidence=0.9, normalized_text=t, source="heuristic")

    cancel_order_markers = ["cancel order", "order cancel", "ऑर्डर कैंसल", "order radd"]
    if any(k in t for k in cancel_order_markers):
        return ChatAssistResponse(intent="cancel_order", confidence=0.9, normalized_text=t, source="heuristic")

    if any(k in t for k in ["cod", "cash on delivery", "online", "upi", "card", "gpay", "pay"]):
        return ChatAssistResponse(intent="provide_payment", confidence=0.75, normalized_text=t, source="heuristic")

    if re.search(r"\b\d+\b", t):
        return ChatAssistResponse(intent="provide_quantity", confidence=0.55, normalized_text=t, source="heuristic")

    return ChatAssistResponse(
        intent="provide_medicine",
        confidence=0.4,
        normalized_text=t,
        source="heuristic",
    )


def _call_gemini_for_chat_assist(payload: ChatAssistRequest) -> ChatAssistResponse | None:
    if not GEMINI_API_KEY:
        return None
    system_prompt = (
        "You are an intent parser for a pharmacy conversational agent. "
        "Classify the user message and output STRICT JSON only with keys: "
        "intent, medicine_query, response_text, normalized_text, confidence. "
        "Allowed intents: change_medicine,new_chat,cancel_chat,end_chat,cancel_order,"
        "select_option,provide_medicine,provide_dosage,provide_quantity,provide_payment,"
        "upload_prescription,unknown. "
        "If user asks to change medicine, set intent=change_medicine and extract medicine_query when present. "
        "Keep response_text short and helpful in the user's language if possible."
    )
    user_prompt = (
        f"language_code: {payload.language_code}\n"
        f"stage: {payload.stage}\n"
        f"current_medicine: {payload.current_medicine or ''}\n"
        f"candidate_medicines: {', '.join(payload.candidate_medicines[:8])}\n"
        f"user_message: {payload.message}"
    )
    body = {
        "contents": [
            {"role": "user", "parts": [{"text": system_prompt}]},
            {"role": "user", "parts": [{"text": user_prompt}]},
        ],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 220},
    }
    models_to_try: list[str] = []
    if GEMINI_MODEL:
        models_to_try.append(GEMINI_MODEL)
    if "gemini-1.5-flash" not in models_to_try:
        models_to_try.append("gemini-1.5-flash")
    if "gemini-1.5-pro" not in models_to_try:
        models_to_try.append("gemini-1.5-pro")

    for model in models_to_try:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            resp = requests.post(endpoint, json=body, timeout=8)
        except Exception:
            continue
        if resp.status_code < 200 or resp.status_code >= 300:
            continue
        data = resp.json()
        cands = data.get("candidates") or []
        if not cands:
            continue
        parts = ((cands[0].get("content") or {}).get("parts") or [])
        text = ""
        for p in parts:
            if isinstance(p, dict) and isinstance(p.get("text"), str):
                text += p["text"]
        parsed = _extract_json_blob(text)
        intent = str(parsed.get("intent") or "").strip().lower()
        if intent not in _ASSIST_INTENTS:
            intent = "unknown"
        conf_raw = parsed.get("confidence")
        try:
            confidence = float(conf_raw)
        except Exception:
            confidence = 0.0
        confidence = max(0.0, min(confidence, 1.0))
        med_q = parsed.get("medicine_query")
        if med_q is not None:
            med_q = str(med_q).strip() or None
        response_text = parsed.get("response_text")
        if response_text is not None:
            response_text = str(response_text).strip() or None
        normalized_text = parsed.get("normalized_text")
        if normalized_text is not None:
            normalized_text = str(normalized_text).strip() or None
        return ChatAssistResponse(
            intent=intent,
            medicine_query=med_q,
            response_text=response_text,
            normalized_text=normalized_text,
            confidence=confidence,
            source="gemini",
        )
    return None


@router.post("/assistant", response_model=ChatAssistResponse)
def chat_assistant(
    payload: ChatAssistRequest,
    _: User = Depends(get_current_user),
):
    heur = _heuristic_intent(payload.message)
    gem = None
    try:
        gem = _call_gemini_for_chat_assist(payload)
    except Exception:
        gem = None
    if gem and (gem.intent in _ASSIST_INTENTS) and (gem.confidence >= 0.45 or gem.intent in {"change_medicine", "end_chat", "cancel_chat", "new_chat", "cancel_order"}):
        return gem
    return heur


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
