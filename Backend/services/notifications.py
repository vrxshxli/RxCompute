import smtplib
import traceback
from email.mime.text import MIMEText

import firebase_admin
from firebase_admin import messaging
from sqlalchemy.orm import Session

from config import SMTP_FALLBACK_TO_EMAIL, SMTP_FROM_EMAIL, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER
from models.notification import Notification, NotificationType
from models.order import Order
from models.user import User


def create_notification(
    db: Session,
    user_id: int,
    type_: NotificationType,
    title: str,
    body: str,
    has_action: bool = True,
) -> Notification:
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
    try:
        if not firebase_admin._apps:
            print("Push skipped: Firebase Admin is not initialized")
            return
        msg = messaging.Message(
            token=user.push_token,
            notification=messaging.Notification(title=title, body=body),
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(sound="default"),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default"),
                )
            ),
        )
        messaging.send(msg)
    except Exception:
        print("Push send failed")
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
    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=12) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=12) as server:
        server.ehlo()
        if server.has_extn("starttls"):
            server.starttls()
            server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
