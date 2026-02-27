import socket
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
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


@router.get("/safety-events")
def list_safety_events(
    severity: str = Query(default="all"),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view safety events")
    q = (
        db.query(Notification, User)
        .join(User, User.id == Notification.user_id)
        .filter(Notification.type == NotificationType.safety)
    )
    sev = (severity or "all").strip().lower()
    if sev == "blocked":
        q = q.filter(or_(Notification.title.ilike("%blocked%"), Notification.body.ilike("%blocked%")))
    elif sev == "warning":
        q = q.filter(or_(Notification.title.ilike("%warning%"), Notification.body.ilike("%warning%")))
    elif sev != "all":
        raise HTTPException(status_code=400, detail="Invalid severity filter")

    if search:
        term = f"%{search.strip()}%"
        q = q.filter(
            or_(
                Notification.title.ilike(term),
                Notification.body.ilike(term),
                User.name.ilike(term),
                User.email.ilike(term),
                User.role.ilike(term),
            )
        )

    rows = q.order_by(Notification.created_at.desc()).limit(limit).all()
    out = []
    for notif, user in rows:
        text = f"{notif.title} {notif.body}".lower()
        row_severity = "blocked" if "blocked" in text else ("warning" if "warning" in text else "info")
        metadata = None
        if getattr(notif, "metadata_json", None):
            try:
                metadata = json.loads(notif.metadata_json)
            except Exception:
                metadata = None
        target_user = None
        if isinstance(metadata, dict) and isinstance(metadata.get("target_user_id"), int):
            target_user = db.query(User).filter(User.id == metadata["target_user_id"]).first()
        out.append(
            {
                "id": notif.id,
                "user_id": notif.user_id,
                "user_name": user.name,
                "user_email": user.email,
                "user_role": user.role,
                "title": notif.title,
                "body": notif.body,
                "is_read": notif.is_read,
                "created_at": notif.created_at,
                "severity": row_severity,
                "metadata": metadata,
                "target_user_id": target_user.id if target_user else (metadata.get("target_user_id") if isinstance(metadata, dict) else None),
                "target_user_name": target_user.name if target_user else None,
                "target_user_email": target_user.email if target_user else None,
                "target_user_role": target_user.role if target_user else None,
            }
        )
    return out


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
