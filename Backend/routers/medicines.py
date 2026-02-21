from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.medicine import Medicine
from schemas.medicine import MedicineCreate, MedicineUpdate, MedicineOut

router = APIRouter(prefix="/medicines", tags=["Medicines"])


@router.get("/", response_model=list[MedicineOut])
def list_medicines(
    search: str | None = Query(None, description="Search by name or PZN"),
    skip: int = 0,
    limit: int = 50,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all medicines, optionally filter by search term."""
    q = db.query(Medicine)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            Medicine.name.ilike(pattern) | Medicine.pzn.ilike(pattern)
        )
    return q.offset(skip).limit(limit).all()


@router.get("/{medicine_id}", response_model=MedicineOut)
def get_medicine(
    medicine_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single medicine by ID."""
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return med


@router.post("/", response_model=MedicineOut)
def create_medicine(
    data: MedicineCreate,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new medicine entry."""
    existing = db.query(Medicine).filter(Medicine.pzn == data.pzn).first()
    if existing:
        raise HTTPException(status_code=400, detail="PZN already exists")
    med = Medicine(**data.model_dump())
    db.add(med)
    db.commit()
    db.refresh(med)
    return med


@router.put("/{medicine_id}", response_model=MedicineOut)
def update_medicine(
    medicine_id: int,
    data: MedicineUpdate,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a medicine entry."""
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(med, key, value)
    db.commit()
    db.refresh(med)
    return med
