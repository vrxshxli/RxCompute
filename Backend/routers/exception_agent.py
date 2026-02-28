"""
Exception Agent API — Escalation Handler

  POST /exceptions/handle      → Process safety blocks/warnings into actionable exceptions
  POST /exceptions/resolve     → Mark exception as resolved (pharmacist/admin action)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from exception_agent.exception_agent import handle_order_exceptions

router = APIRouter(prefix="/exceptions", tags=["Exception Agent"])
STAFF = {"admin", "pharmacy_store", "warehouse"}


class ExceptionRequest(BaseModel):
    safety_results: list[dict]
    matched_medicines: list[dict] = []


@router.post("/handle")
def handle_exceptions(
    data: ExceptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Process safety blocks/warnings into classified exceptions.

    Called AFTER safety agent blocks/warns. Returns:
    - Exception type + escalation level per medicine
    - Patient instructions (what they can do to fix it)
    - Staff actions (what pharmacist/admin needs to review)
    - Alternative medicines (when stock is exhausted)
    - Full audit trail

    Langfuse trace shows every classification and escalation decision.

    Request:
    {
      "safety_results": [
        {"medicine_id": 11, "medicine_name": "Mucosolvan", "status": "blocked", "rule": "prescription_required", "message": "..."}
      ],
      "matched_medicines": [
        {"medicine_id": 11, "name": "Mucosolvan", "quantity": 1}
      ]
    }
    """
    if not data.safety_results:
        raise HTTPException(400, "No safety results to process")

    return handle_order_exceptions(
        user_id=current_user.id,
        safety_results=data.safety_results,
        matched_medicines=data.matched_medicines,
    )


@router.post("/resolve/{medicine_id}")
def resolve_exception(
    medicine_id: int,
    action: str = "approved",
    notes: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Pharmacist/admin resolves an escalated exception.

    action: "approved" | "rejected" | "alternative_offered"
    notes: pharmacist's review notes
    """
    if current_user.role not in STAFF:
        raise HTTPException(403, "Staff only")

    from models.notification import NotificationType
    from services.notifications import create_notification

    # Find patient who ordered this medicine (from recent safety notifications)
    from models.notification import Notification
    notif = (
        db.query(Notification)
        .filter(
            Notification.type == NotificationType.safety,
            Notification.title.contains(str(medicine_id)),
        )
        .order_by(Notification.created_at.desc())
        .first()
    )

    resolution_msg = f"Exception for medicine #{medicine_id}: {action}. {notes}".strip()

    if notif:
        create_notification(
            db, notif.user_id, NotificationType.order,
            f"Exception Resolved",
            resolution_msg,
            has_action=True,
        )

    # Admin audit
    create_notification(
        db, current_user.id, NotificationType.system,
        f"Exception Resolved by {current_user.role}",
        resolution_msg,
        has_action=False,
    )
    db.commit()

    return {
        "resolved": True,
        "medicine_id": medicine_id,
        "action": action,
        "resolved_by": current_user.name or current_user.email,
        "resolved_by_role": current_user.role,
        "notes": notes,
    }