"""
Exception Agent API — Escalation Handler

  POST /exceptions/handle      → Process safety blocks/warnings into actionable exceptions
  POST /exceptions/resolve     → Mark exception as resolved (pharmacist/admin action)
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.notification import Notification, NotificationType
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

    from services.notifications import create_notification

    # Find most recent matching exception notification via metadata.
    notif = (
        db.query(Notification)
        .filter(
            Notification.type == NotificationType.safety,
            Notification.metadata_json.isnot(None),
        )
        .order_by(Notification.created_at.desc())
        .all()
    )
    matched_notif = None
    target_user_id = None
    for n in notif:
        try:
            meta = json.loads(n.metadata_json or "{}")
        except Exception:
            meta = {}
        if str(meta.get("agent_name", "")).strip().lower() != "exception_agent":
            continue
        if int(meta.get("medicine_id") or 0) != medicine_id:
            continue
        matched_notif = n
        target_user_id = int(meta.get("target_user_id") or 0) or None
        break

    resolution_msg = f"Exception for medicine #{medicine_id}: {action}. {notes}".strip()

    if target_user_id:
        create_notification(
            db, target_user_id, NotificationType.order,
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


@router.get("/queue")
def exception_queue(
    limit: int = Query(default=100, ge=1, le=300),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Pharmacy/admin exception queue derived from exception-agent safety notifications.
    """
    if current_user.role not in {"admin", "pharmacy_store"}:
        raise HTTPException(status_code=403, detail="Staff only")
    rows = (
        db.query(Notification)
        .filter(
            Notification.type == NotificationType.safety,
            Notification.metadata_json.isnot(None),
        )
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for n in rows:
        try:
            meta = json.loads(n.metadata_json or "{}")
        except Exception:
            meta = {}
        if str(meta.get("agent_name", "")).strip().lower() != "exception_agent":
            continue
        out.append(
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "created_at": n.created_at,
                "is_read": n.is_read,
                "exception_type": meta.get("exception_type"),
                "escalation_level": meta.get("escalation_level"),
                "severity": meta.get("severity"),
                "medicine_id": meta.get("medicine_id"),
                "medicine_name": meta.get("medicine_name"),
                "reasoning": meta.get("reasoning"),
                "target_user_id": meta.get("target_user_id"),
                "target_user_name": meta.get("target_user_name"),
            }
        )
    return out