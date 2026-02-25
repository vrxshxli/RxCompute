from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.webhook_log import WebhookLog
from schemas.webhook import WebhookLogOut
from services.webhooks import dispatch_webhook

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _ensure_staff(current_user: User):
    if current_user.role not in {"admin", "pharmacy_store", "warehouse"}:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/logs", response_model=list[WebhookLogOut])
def list_webhook_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_staff(current_user)
    return db.query(WebhookLog).order_by(WebhookLog.created_at.desc()).limit(200).all()


@router.post("/test")
def send_test_webhook(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_staff(current_user)
    log = dispatch_webhook(
        db,
        event_type="webhook_test",
        payload={
            "by_user_id": current_user.id,
            "by_role": current_user.role,
            "message": "Webhook test from RxCompute API",
        },
    )
    if not log:
        return {"ok": False, "detail": "WEBHOOK_TARGET_URL not configured"}
    return {"ok": True, "log_id": log.id, "status": log.response_status, "error": log.error_message}
