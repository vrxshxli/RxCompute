from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.pharmacy_store import PharmacyStore
from models.user import User
from schemas.pharmacy_store import PharmacyStoreCreate, PharmacyStoreOut, PharmacyStoreUpdate

router = APIRouter(prefix="/pharmacy-stores", tags=["PharmacyStores"])
STAFF_ROLES = {"admin", "pharmacy_store", "warehouse"}


def _ensure_staff(current_user: User):
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=list[PharmacyStoreOut])
def list_pharmacy_stores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_staff(current_user)
    return db.query(PharmacyStore).order_by(PharmacyStore.node_id.asc()).all()


@router.post("/", response_model=PharmacyStoreOut)
def create_pharmacy_store(
    data: PharmacyStoreCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_staff(current_user)
    existing = db.query(PharmacyStore).filter(PharmacyStore.node_id == data.node_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Store node_id already exists")
    row = PharmacyStore(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{store_id}", response_model=PharmacyStoreOut)
def update_pharmacy_store(
    store_id: int,
    data: PharmacyStoreUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_staff(current_user)
    row = db.query(PharmacyStore).filter(PharmacyStore.id == store_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Pharmacy store not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row
