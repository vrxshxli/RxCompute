import math
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.medicine import Medicine
from models.order import Order, OrderStatus
from models.user_medication import UserMedication
from schemas.medication import HomeSummaryOut, UserMedicationOut

router = APIRouter(prefix="/home", tags=["Home"])


def _to_out(record: UserMedication, med: Medicine | None) -> UserMedicationOut:
    units_per_day = max(record.frequency_per_day, 1)
    days_left = int(math.ceil(record.quantity_units / units_per_day))
    return UserMedicationOut(
        id=record.id,
        medicine_id=record.medicine_id,
        name=med.name if med else (record.custom_name or "Medication"),
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
    meds = (
        db.query(UserMedication, Medicine)
        .outerjoin(Medicine, Medicine.id == UserMedication.medicine_id)
        .filter(UserMedication.user_id == current_user.id)
        .all()
    )
    med_out = [_to_out(record, med) for record, med in meds]
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
