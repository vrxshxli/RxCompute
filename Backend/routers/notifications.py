from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.notification import Notification, NotificationType
from models.user import User
from schemas.notification import NotificationOut
from services.notifications import (
    create_notification,
    send_push_if_available,
    send_test_email,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[NotificationOut])
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all notifications for the current user."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.put("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.put("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


def _run_test_delivery(current_user: User, db: Session):
    title = "RxCompute Test Notification"
    body = "This is a test for push/email delivery channels."
    create_notification(
        db,
        current_user.id,
        NotificationType.general,
        title,
        body,
        has_action=False,
    )
    db.commit()
    send_push_if_available(current_user, title, body)
    email_target = current_user.email or "deepakm7778@gmail.com"
    email_ok = send_test_email(
        recipient_email=email_target,
        subject="RxCompute Test Email",
        body="If you received this, custom SMTP is working.",
    )
    return {
        "push_token_present": bool(current_user.push_token),
        "email_target": email_target,
        "email_sent": email_ok,
        "note": "Check Render logs for push/email send errors if delivery fails.",
    }


@router.post("/test-delivery")
def test_delivery_post(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create one test notification and attempt both push + email delivery."""
    return _run_test_delivery(current_user, db)


@router.get("/test-delivery")
def test_delivery_get(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Browser-friendly test route for push/email delivery."""
    return _run_test_delivery(current_user, db)
