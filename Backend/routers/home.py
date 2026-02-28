from datetime import datetime, timedelta
import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.medicine import Medicine
from models.order import Order, OrderItem, OrderStatus
from models.user_medication import UserMedication
from schemas.medication import HomeSummaryOut, UserMedicationOut
from services.refill_reminders import calculate_days_left, trigger_daily_refill_notifications_for_user
from prediction_agent.prediction_agent import run_prediction_for_user

router = APIRouter(prefix="/home", tags=["Home"])


def _to_naive_utc(dt: datetime | None) -> datetime:
    if not dt:
        return datetime.utcnow()
    if dt.tzinfo is None:
        return dt
    return dt.replace(tzinfo=None)


def _extract_units_per_pack(package: str | None) -> int:
    txt = (package or "").lower().strip()
    if not txt:
        return 1
    m = re.search(r"(\d+)\s*(st|tabs?|tablets?|caps?(?:ules?)?)\b", txt)
    if m:
        return max(int(m.group(1)), 1)
    n = re.search(r"(\d+)", txt)
    return max(int(n.group(1)), 1) if n else 1


def _estimate_frequency_per_day(dosage_instruction: str | None) -> int | None:
    raw = (dosage_instruction or "").strip().lower()
    if not raw:
        return None
    tri = re.search(r"\b(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\b", raw)
    if tri:
        return max(int(tri.group(1)) + int(tri.group(2)) + int(tri.group(3)), 1)
    xday = re.search(r"\b(\d+)\s*(x|times?)\s*(/|per)?\s*day\b", raw)
    if xday:
        return max(int(xday.group(1)), 1)
    if "once daily" in raw:
        return 1
    if "twice" in raw:
        return 2
    if "thrice" in raw:
        return 3
    return None


def _reconcile_tracking_from_delivered_orders(db: Session, user_id: int) -> None:
    """
    Repair stale user-medication clocks from already delivered orders.
    This fixes older accounts where refill delivery happened but tracking wasn't reset.
    """
    rows = (
        db.query(Order, OrderItem, Medicine)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .outerjoin(Medicine, Medicine.id == OrderItem.medicine_id)
        .filter(
            Order.user_id == user_id,
            Order.status == OrderStatus.delivered,
            OrderItem.medicine_id.isnot(None),
        )
        .order_by(Order.created_at.desc())
        .limit(120)
        .all()
    )
    latest_by_medicine: dict[int, tuple[Order, OrderItem, Medicine | None]] = {}
    for order, item, med in rows:
        if item.medicine_id and item.medicine_id not in latest_by_medicine:
            latest_by_medicine[item.medicine_id] = (order, item, med)

    changed = False
    for medicine_id, (order, item, med) in latest_by_medicine.items():
        delivered_at = _to_naive_utc(order.updated_at or order.created_at)
        track = (
            db.query(UserMedication)
            .filter(UserMedication.user_id == user_id, UserMedication.medicine_id == medicine_id)
            .first()
        )
        existing_at = _to_naive_utc(track.created_at) if track and track.created_at else None
        if existing_at and existing_at >= delivered_at:
            continue
        pack_count = max(int(item.strips_count or item.quantity or 1), 1)
        units = max(pack_count * _extract_units_per_pack(med.package if med else None), pack_count)
        freq = _estimate_frequency_per_day(item.dosage_instruction)
        if track:
            track.quantity_units = max(int(track.quantity_units or 0), units)
            track.created_at = delivered_at
            if (item.dosage_instruction or "").strip():
                track.dosage_instruction = item.dosage_instruction
            if freq:
                track.frequency_per_day = freq
            changed = True
        else:
            db.add(
                UserMedication(
                    user_id=user_id,
                    medicine_id=medicine_id,
                    custom_name=item.name,
                    dosage_instruction=item.dosage_instruction or "As prescribed",
                    frequency_per_day=freq or 1,
                    quantity_units=max(units, 1),
                    created_at=delivered_at,
                )
            )
            changed = True
    if changed:
        db.commit()


def _best_name(db: Session, med: Medicine | None, custom_name: str | None) -> str:
    if med:
        return med.name
    raw = (custom_name or "").strip()
    if not raw:
        return "Medication"
    guess = db.query(Medicine).filter(Medicine.name.ilike(raw)).first()
    if not guess:
        key = raw[:4].strip()
        if key:
            guess = (
                db.query(Medicine)
                .filter(Medicine.name.ilike(f"{key}%"))
                .order_by(Medicine.name.asc())
                .first()
            )
    if not guess:
        guess = (
            db.query(Medicine)
            .filter(Medicine.name.ilike(f"%{raw}%"))
            .order_by(Medicine.name.asc())
            .first()
        )
    return guess.name if guess else raw


def _to_out(db: Session, record: UserMedication, med: Medicine | None) -> UserMedicationOut:
    days_left = calculate_days_left(record)
    return UserMedicationOut(
        id=record.id,
        medicine_id=record.medicine_id,
        name=_best_name(db, med, record.custom_name),
        dosage_instruction=record.dosage_instruction,
        frequency_per_day=record.frequency_per_day,
        quantity_units=record.quantity_units,
        days_left=days_left,
        rx_required=med.rx_required if med else False,
        created_at=record.created_at,
    )


@router.get("/summary", response_model=HomeSummaryOut)
def get_home_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _reconcile_tracking_from_delivered_orders(db, current_user.id)
    # Trigger refill reminder check when app home is opened.
    run_prediction_for_user(
        current_user.id,
        create_alerts=True,
        once_per_day=True,
        trigger_reason="app_open_home_summary",
        publish_trace=True,
    )
    trigger_daily_refill_notifications_for_user(db, current_user)
    meds = (
        db.query(UserMedication, Medicine)
        .outerjoin(Medicine, Medicine.id == UserMedication.medicine_id)
        .filter(UserMedication.user_id == current_user.id)
        .all()
    )
    med_out = [_to_out(db, record, med) for record, med in meds]
    refill_alert = min(med_out, key=lambda m: m.days_left) if med_out else None

    month_start = datetime.utcnow() - timedelta(days=30)
    monthly_orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id, Order.created_at >= month_start)
        .all()
    )
    monthly_total_spend = float(sum(order.total for order in monthly_orders))
    active_order_count = (
        db.query(Order)
        .filter(
            Order.user_id == current_user.id,
            Order.status.notin_([OrderStatus.delivered, OrderStatus.cancelled]),
        )
        .count()
    )

    return HomeSummaryOut(
        todays_medications=len(med_out),
        refill_alert=refill_alert,
        monthly_total_spend=round(monthly_total_spend, 2),
        monthly_order_count=len(monthly_orders),
        active_order_count=active_order_count,
    )
