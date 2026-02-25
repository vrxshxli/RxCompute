import smtplib
from email.mime.text import MIMEText

from firebase_admin import messaging
from sqlalchemy.orm import Session

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL
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
        return
    try:
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
        # Push failures should not break business flow.
        return


def send_order_email(user: User | None, order: Order) -> None:
    if not user or not user.email:
        return
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        return

    items = "\n".join([f"- {it.name} x{it.quantity} ({it.price:.2f})" for it in order.items]) or "-"
    text = (
        f"Your order has been placed.\n\n"
        f"Order ID: {order.order_uid}\n"
        f"Status: {order.status.value}\n"
        f"Payment: {order.payment_method or '-'}\n"
        f"Total: {order.total:.2f}\n\n"
        f"Items:\n{items}\n"
    )

    msg = MIMEText(text)
    msg["Subject"] = f"RxCompute Order {order.order_uid}"
    msg["From"] = SMTP_FROM_EMAIL or SMTP_USER
    msg["To"] = user.email

    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
    except Exception:
        # Email failures should not block order flow.
        return
