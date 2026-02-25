import hmac

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from config import JOB_RUN_KEY
from database import get_db
from services.refill_reminders import trigger_daily_refill_notifications_for_all_users

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/run-refill-reminders")
def run_refill_reminders(
    key: str = Query(default=""),
    db: Session = Depends(get_db),
):
    """External scheduler hook: triggers daily refill reminders for all users."""
    if not JOB_RUN_KEY:
        raise HTTPException(status_code=503, detail="JOB_RUN_KEY is not configured")
    if not hmac.compare_digest(key, JOB_RUN_KEY):
        raise HTTPException(status_code=401, detail="Invalid job key")
    count = trigger_daily_refill_notifications_for_all_users(db)
    return {"ok": True, "created_notifications": count}
