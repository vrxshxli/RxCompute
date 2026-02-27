import socket
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import SMTP_FROM_EMAIL, SMTP_HOST, SMTP_PORT, SMTP_USER
from database import get_db
from dependencies import get_current_user
from models.notification import Notification, NotificationType
from models.order import Order
from models.user import User
from models.warehouse import TransferDirection, TransferStatus, WarehouseStock, WarehouseTransfer
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
    email_target = current_user.email or "rxcompute@35ddfa3956a414ee.maileroo.org"
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


def _smtp_probe(host: str, port: int, timeout_s: float = 2.0) -> dict:
    try:
        infos = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ips = [i[4][0] for i in infos]
    except Exception as exc:
        return {"host": host, "port": port, "ok": False, "error": f"dns_error: {exc}"}
    for ip in ips:
        try:
            with socket.create_connection((ip, port), timeout=timeout_s):
                return {"host": host, "port": port, "ok": True, "ip": ip}
        except Exception:
            continue
    return {"host": host, "port": port, "ok": False, "error": "connect_failed", "ips": ips[:4]}


@router.get("/delivery-health")
def delivery_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view delivery health")
    now = datetime.utcnow()
    since = now - timedelta(hours=24)
    smtp_ports = [SMTP_PORT, 587, 2525, 465]
    dedup_ports = []
    for p in smtp_ports:
        if p not in dedup_ports:
            dedup_ports.append(p)
    smtp_checks = [_smtp_probe(SMTP_HOST, p) for p in dedup_ports]

    users = db.query(User).all()
    push_count = sum(1 for u in users if (u.push_token or "").strip())
    pharmacy_users = [u for u in users if u.role == "pharmacy_store"]
    warehouse_users = [u for u in users if u.role == "warehouse"]
    admin_users = [u for u in users if u.role == "admin"]

    notifications_24h = db.query(Notification).filter(Notification.created_at >= since).count()
    orders_24h = db.query(Order).filter(Order.created_at >= since).count()
    warehouse_stock_count = db.query(WarehouseStock).count()
    transfers_pending = (
        db.query(WarehouseTransfer)
        .filter(
            WarehouseTransfer.direction == TransferDirection.warehouse_to_pharmacy,
            WarehouseTransfer.status.in_([TransferStatus.requested, TransferStatus.picking, TransferStatus.packed]),
        )
        .count()
    )

    return {
        "timestamp_utc": now.isoformat(),
        "smtp": {
            "host": SMTP_HOST,
            "configured_port": SMTP_PORT,
            "from_email": SMTP_FROM_EMAIL,
            "user_hint": f"{SMTP_USER[:4]}...{SMTP_USER[-10:]}" if SMTP_USER else "",
            "reachability": smtp_checks,
        },
        "push": {
            "users_with_push_token": push_count,
            "users_without_push_token": max(len(users) - push_count, 0),
        },
        "roles": {
            "admins": len(admin_users),
            "pharmacy_users": len(pharmacy_users),
            "warehouse_users": len(warehouse_users),
            "total_users": len(users),
        },
        "events_24h": {
            "notifications_created": notifications_24h,
            "orders_created": orders_24h,
        },
        "warehouse": {
            "warehouse_stock_rows": warehouse_stock_count,
            "outbound_transfers_pending": transfers_pending,
        },
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
