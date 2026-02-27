import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.medicine import Medicine
from schemas.medicine import MedicineCreate, MedicineUpdate, MedicineOut

router = APIRouter(prefix="/medicines", tags=["Medicines"])
WAREHOUSE_STAFF_ROLES = {"admin", "warehouse"}


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


@router.delete("/{medicine_id}")
def delete_medicine(
    medicine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a medicine entry (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete medicines")
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    db.delete(med)
    db.commit()
    return {"message": "Medicine deleted"}


@router.put("/{medicine_id}/add-stock", response_model=MedicineOut)
def add_medicine_stock(
    medicine_id: int,
    units: int = Query(..., gt=0, description="Number of units to add to warehouse stock"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Increase medicine stock from warehouse intake."""
    if current_user.role not in WAREHOUSE_STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Only warehouse or admin can add stock")
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    med.stock = (med.stock or 0) + units
    db.commit()
    db.refresh(med)
    return med


def _read_row_value(row: dict[str, str], keys: list[str]) -> str | None:
    lower_map = {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
    for key in keys:
        val = lower_map.get(key.lower())
        if val:
            return str(val)
    return None


def _to_bool(raw: str | None) -> bool:
    if not raw:
        return False
    return raw.strip().lower() in {"yes", "true", "1", "required", "rx", "prescription"}


@router.post("/import-csv")
async def import_medicines_csv(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid CSV file")

    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    created = 0
    updated = 0
    skipped = 0

    for row in reader:
        name = _read_row_value(row, ["product name", "name"])
        pzn = _read_row_value(row, ["pzn"])
        price_raw = _read_row_value(row, ["price rec", "price"])
        if not name or not pzn or not price_raw:
            skipped += 1
            continue

        normalized_price = price_raw.replace(",", ".").strip()
        try:
            price = float(normalized_price)
        except ValueError:
            skipped += 1
            continue

        package = _read_row_value(row, ["package size", "package"])
        description = _read_row_value(row, ["descriptions", "description"])
        image_url = _read_row_value(row, ["image", "image_url"])
        rx_required = _to_bool(_read_row_value(row, ["prescription required", "rx_required"]))

        med = db.query(Medicine).filter(Medicine.pzn == pzn).first()
        if med:
            med.name = name
            med.price = price
            med.package = package
            med.description = description
            med.image_url = image_url
            med.rx_required = rx_required
            updated += 1
        else:
            db.add(
                Medicine(
                    name=name,
                    pzn=pzn,
                    price=price,
                    package=package,
                    description=description,
                    image_url=image_url,
                    rx_required=rx_required,
                    stock=50,
                )
            )
            created += 1

    db.commit()
    return {
        "message": "CSV import completed",
        "created": created,
        "updated": updated,
        "skipped": skipped,
    }
