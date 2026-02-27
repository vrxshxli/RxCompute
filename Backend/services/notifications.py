import smtplib
import socket
import traceback
import json
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from email.mime.text import MIMEText

import firebase_admin
from firebase_admin import messaging
from sqlalchemy.orm import Session

from config import (
    MAILEROO_API_KEY,
    MAILEROO_API_URL,
    SMTP_FALLBACK_TO_EMAIL,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)
from models.notification import Notification, NotificationType
from models.order import Order
from models.user import User

_BG_EXECUTOR = ThreadPoolExecutor(max_workers=6)


def run_in_background(fn, *args, **kwargs) -> None:
    try:
        _BG_EXECUTOR.submit(fn, *args, **kwargs)
    except Exception as exc:
        print(f"Background task submit failed: {exc}")


def create_notification(
    db: Session,
    user_id: int,
    type_: NotificationType,
    title: str,
    body: str,
    has_action: bool = True,
    dedupe_window_minutes: int | None = 2,
) -> Notification:
    if dedupe_window_minutes and dedupe_window_minutes > 0:
        cutoff = datetime.utcnow() - timedelta(minutes=dedupe_window_minutes)
        existing = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.type == type_,
                Notification.title == title,
                Notification.body == body,
                Notification.created_at >= cutoff,
            )
            .order_by(Notification.created_at.desc())
            .first()
        )
        if existing:
            return existing
    notif = Notification(
        user_id=user_id,
        type=type_,
        title=title,
        body=body,
        has_action=has_action,
    )
    db.add(notif)
    return notif


def send_push_if_available(user: User | None, title: str, body: str) -> None:
    if not user or not user.push_token:
        print("Push skipped: no user or push token")
        return
    send_push_to_token(user.push_token, title, body, user.id if user else None)


def send_push_to_token(push_token: str | None, title: str, body: str, user_id: int | None = None) -> None:
    if not push_token:
        print("Push skipped: no user or push token")
        return
    try:
        if not firebase_admin._apps:
            print("Push skipped: Firebase Admin is not initialized")
            return
        msg = messaging.Message(
            token=push_token,
            notification=messaging.Notification(title=title, body=body),
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(sound="rx_tune", channel_id="rxcompute_alerts"),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="rx_tune.wav"),
                )
            ),
        )
        messaging.send(msg)
    except Exception as exc:
        print(f"Push send failed for user {user_id if user_id else 'n/a'}: {exc}")
        traceback.print_exc()
        # Push failures should not break business flow.
        return


def send_order_email(user: User | None, order: Order) -> None:
    if not user:
        return
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return
    recipient_email = user.email or SMTP_FALLBACK_TO_EMAIL
    if not recipient_email:
        print("Email skipped: recipient missing")
        return

    status_value = order.status.value if hasattr(order.status, "value") else str(order.status)
    items = "\n".join([f"- {it.name} x{it.quantity} ({it.price:.2f})" for it in order.items]) or "-"
    text = (
        f"Your order has been placed.\n\n"
        f"Order ID: {order.order_uid}\n"
        f"Status: {status_value}\n"
        f"Payment: {order.payment_method or '-'}\n"
        f"Total: {order.total:.2f}\n\n"
        f"Items:\n{items}\n"
    )

    try:
        _send_email(recipient_email, f"RxCompute Order {order.order_uid}", text)
    except Exception as exc:
        print(f"Email send failed for order {order.order_uid} to {recipient_email}: {exc}")
        traceback.print_exc()
        # Email failures should not block order flow.
        return


def send_refill_email(user: User | None, title: str, body: str) -> None:
    if not user:
        return
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return
    recipient_email = user.email or SMTP_FALLBACK_TO_EMAIL
    if not recipient_email:
        print("Refill email skipped: recipient missing")
        return
    text = (
        f"{title}\n\n"
        f"{body}\n\n"
        f"Open RxCompute to review your medicines and place refill order."
    )
    try:
        _send_email(recipient_email, title, text)
    except Exception as exc:
        print(f"Refill email send failed to {recipient_email}: {exc}")
        traceback.print_exc()


def send_staff_order_email(user: User | None, order: Order) -> None:
    if not user:
        return
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return
    recipient_email = user.email or SMTP_FALLBACK_TO_EMAIL
    if not recipient_email:
        print("Staff email skipped: recipient missing")
        return
    status_value = order.status.value if hasattr(order.status, "value") else str(order.status)
    items = "\n".join([f"- {it.name} x{it.quantity} ({it.price:.2f})" for it in order.items]) or "-"
    text = (
        f"New customer order received.\n\n"
        f"Order ID: {order.order_uid}\n"
        f"Status: {status_value}\n"
        f"Assigned pharmacy: {order.pharmacy or '-'}\n"
        f"Payment: {order.payment_method or '-'}\n"
        f"Total: {order.total:.2f}\n\n"
        f"Items:\n{items}\n"
    )
    try:
        _send_email(recipient_email, f"RxCompute New Order {order.order_uid}", text)
    except Exception as exc:
        print(f"Staff order email send failed to {recipient_email}: {exc}")
        traceback.print_exc()


def send_order_email_snapshot(recipient_email: str | None, order_data: dict, subject_prefix: str = "RxCompute Order") -> None:
    if not recipient_email:
        recipient_email = SMTP_FALLBACK_TO_EMAIL
    if not recipient_email:
        print("Email skipped: recipient missing")
        return
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return
    items = order_data.get("items", [])
    items_text = "\n".join([f"- {it.get('name', '-')} x{it.get('quantity', 0)} ({float(it.get('price', 0)):.2f})" for it in items]) or "-"
    text = (
        f"Order ID: {order_data.get('order_uid', '-')}\n"
        f"Status: {order_data.get('status', '-')}\n"
        f"Assigned pharmacy: {order_data.get('pharmacy', '-')}\n"
        f"Payment: {order_data.get('payment_method', '-')}\n"
        f"Total: {float(order_data.get('total', 0)):.2f}\n\n"
        f"Items:\n{items_text}\n"
    )
    try:
        _send_email(recipient_email, f"{subject_prefix} {order_data.get('order_uid', '-')}", text)
    except Exception as exc:
        print(f"Snapshot email send failed to {recipient_email}: {exc}")
        traceback.print_exc()


def send_test_email(recipient_email: str, subject: str, body: str) -> bool:
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return False
    try:
        _send_email(recipient_email, subject, body)
        return True
    except Exception as exc:
        print(f"Test email send failed to {recipient_email}: {exc}")
        traceback.print_exc()
        return False


def _send_email(recipient_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM_EMAIL or SMTP_USER
    msg["To"] = recipient_email
    preferred_ports: list[int] = []
    for p in [SMTP_PORT, 587, 2525, 465]:
        if p not in preferred_ports:
            preferred_ports.append(p)

    last_exc: Exception | None = None
    for port in preferred_ports:
        try:
            _send_email_with_port(msg, port)
            return
        except Exception as exc:
            last_exc = exc
            print(f"Email attempt failed on {SMTP_HOST}:{port} -> {exc}")
            continue
    # SMTP failed on all ports. Try Maileroo HTTP API fallback.
    try:
        _send_email_via_maileroo_api(recipient_email, subject, body)
        print("Email sent via Maileroo API fallback")
        return
    except Exception as api_exc:
        print(f"Maileroo API fallback failed: {api_exc}")
        if last_exc:
            raise last_exc
        raise api_exc


def _send_email_with_port(msg: MIMEText, port: int) -> None:
    # Resolve IPv4 explicitly to avoid IPv6-only route issues on some hosts.
    ipv4_rows = socket.getaddrinfo(SMTP_HOST, port, socket.AF_INET, socket.SOCK_STREAM)
    if not ipv4_rows:
        raise OSError(f"No IPv4 address resolved for {SMTP_HOST}:{port}")
    last_exc: Exception | None = None
    for row in ipv4_rows:
        ip = row[4][0]
        try:
            if port == 465:
                with smtplib.SMTP_SSL(ip, port, timeout=4) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
                return
            with smtplib.SMTP(ip, port, timeout=4) as server:
                server.ehlo()
                if server.has_extn("starttls"):
                    server.starttls()
                    server.ehlo()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            return
        except Exception as exc:
            last_exc = exc
            continue
    if last_exc:
        raise last_exc


def _send_email_via_maileroo_api(recipient_email: str, subject: str, body: str) -> None:
    if not MAILEROO_API_KEY:
        raise RuntimeError("MAILEROO_API_KEY is missing")

    payload = {
        "from": {"address": SMTP_FROM_EMAIL or SMTP_USER},
        "to": [{"address": recipient_email}],
        "subject": subject,
        "text": body,
    }
    raw = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        MAILEROO_API_URL,
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MAILEROO_API_KEY}",
            "X-API-Key": MAILEROO_API_KEY,
        },
    )
    try:
        with urllib_request.urlopen(req, timeout=8) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            if status < 200 or status >= 300:
                body_text = resp.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"Maileroo API non-2xx status {status}: {body_text}")
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Maileroo API HTTPError {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"Maileroo API URLError: {exc}") from exc
