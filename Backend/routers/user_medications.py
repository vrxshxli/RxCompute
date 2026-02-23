import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.medicine import Medicine
from models.user_medication import UserMedication
from schemas.medication import (
    UserMedicationCreate,
    UserMedicationOut,
    UserMedicationUpdate,
)

router = APIRouter(prefix="/user-medications", tags=["User Medications"])


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


@router.get("/", response_model=list[UserMedicationOut])
def list_user_medications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(UserMedication, Medicine)
        .outerjoin(Medicine, Medicine.id == UserMedication.medicine_id)
        .filter(UserMedication.user_id == current_user.id)
        .order_by(UserMedication.created_at.desc())
        .all()
    )
    return [_to_out(record, med) for record, med in rows]


@router.post("/", response_model=UserMedicationOut)
def create_user_medication(
    data: UserMedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    med = None
    if data.medicine_id is not None:
        med = db.query(Medicine).filter(Medicine.id == data.medicine_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medicine not found")

    row = UserMedication(
        user_id=current_user.id,
        medicine_id=data.medicine_id,
        custom_name=data.custom_name,
        dosage_instruction=data.dosage_instruction,
        frequency_per_day=data.frequency_per_day,
        quantity_units=data.quantity_units,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row, med)


@router.put("/{medication_id}", response_model=UserMedicationOut)
def update_user_medication(
    medication_id: int,
    data: UserMedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(UserMedication)
        .filter(
            UserMedication.id == medication_id,
            UserMedication.user_id == current_user.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Medication entry not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(row, key, value)

    db.commit()
    db.refresh(row)
    med = db.query(Medicine).filter(Medicine.id == row.medicine_id).first() if row.medicine_id else None
    return _to_out(row, med)


@router.delete("/{medication_id}")
def delete_user_medication(
    medication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(UserMedication)
        .filter(
            UserMedication.id == medication_id,
            UserMedication.user_id == current_user.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Medication entry not found")
    db.delete(row)
    db.commit()
    return {"message": "Medication removed"}
