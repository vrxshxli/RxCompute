import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from models.medicine import Medicine
from models.notification import Notification, NotificationType
from models.user import User
from models.user_medication import UserMedication
from services.notifications import create_notification, send_push_if_available

IST = ZoneInfo("Asia/Kolkata")


def calculate_days_left(record: UserMedication) -> int:
    created_at = record.created_at or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    units_per_day = max(record.frequency_per_day, 1)
    elapsed_days = max((datetime.now(timezone.utc) - created_at).days, 0)
    consumed_units = elapsed_days * units_per_day
    remaining_units = max(record.quantity_units - consumed_units, 0)
    if remaining_units <= 0:
        return 0
    return int(math.ceil(remaining_units / units_per_day))


def trigger_daily_refill_notifications_for_user(db: Session, current_user: User) -> int:
    rows = (
        db.query(UserMedication, Medicine)
        .outerjoin(Medicine, Medicine.id == UserMedication.medicine_id)
        .filter(UserMedication.user_id == current_user.id)
        .all()
    )
    now_ist = datetime.now(IST)
    day_start_ist = datetime(now_ist.year, now_ist.month, now_ist.day, tzinfo=IST)
    day_start_utc = day_start_ist.astimezone(timezone.utc)
    created_count = 0

    for record, med in rows:
        days_left = calculate_days_left(record)
        if days_left > 4:
            continue
        med_name = med.name if med else (record.custom_name or "Medication")
        title = f"Refill Reminder: {med_name}"
        already = (
            db.query(Notification)
            .filter(
                Notification.user_id == current_user.id,
                Notification.type == NotificationType.refill,
                Notification.title == title,
                Notification.created_at >= day_start_utc,
            )
            .first()
        )
        if already:
            continue

        body = f"{med_name} has {days_left} day(s) left. Refill time has started."
        create_notification(
            db,
            current_user.id,
            NotificationType.refill,
            title,
            body,
            has_action=True,
        )
        send_push_if_available(current_user, title, body)
        created_count += 1

    if created_count > 0:
        db.commit()
    return created_count


def trigger_daily_refill_notifications_for_all_users(db: Session) -> int:
    users = db.query(User).all()
    total = 0
    for user in users:
        total += trigger_daily_refill_notifications_for_user(db, user)
    return total
