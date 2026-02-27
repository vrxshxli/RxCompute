import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.medicine import Medicine
from models.pharmacy_store import PharmacyStore
from models.user import User
from models.warehouse import (
    TransferDirection,
    TransferStatus,
    WarehouseStock,
    WarehouseTransfer,
)
from schemas.warehouse import (
    AdminToWarehouseCreate,
    WarehouseMedicineBulkCreate,
    WarehouseMedicineCreate,
    WarehouseMedicineUpdate,
    WarehouseStockOut,
    WarehouseToPharmacyCreate,
    WarehouseTransferOut,
    WarehouseTransferStatusUpdate,
)

router = APIRouter(prefix="/warehouse", tags=["Warehouse"])


def _ensure_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can perform this action")


def _ensure_warehouse_or_admin(user: User):
    if user.role not in {"warehouse", "admin"}:
        raise HTTPException(status_code=403, detail="Only warehouse or admin can perform this action")


def _ensure_transfer_viewer(user: User):
    if user.role not in {"warehouse", "admin", "pharmacy_store"}:
        raise HTTPException(status_code=403, detail="Access denied")


def _get_or_create_stock(db: Session, medicine_id: int) -> WarehouseStock:
    row = db.query(WarehouseStock).filter(WarehouseStock.medicine_id == medicine_id).first()
    if row:
        return row
    row = WarehouseStock(medicine_id=medicine_id, quantity=0)
    db.add(row)
    db.flush()
    return row


def _upsert_warehouse_medicine(db: Session, med_data: WarehouseMedicineCreate) -> tuple[Medicine, WarehouseStock]:
    med = db.query(Medicine).filter(Medicine.pzn == med_data.pzn.strip()).first()
    if med:
        med.name = med_data.name.strip()
        med.price = float(med_data.price)
        med.package = med_data.package.strip() if med_data.package else None
        med.rx_required = bool(med_data.rx_required)
        med.description = med_data.description.strip() if med_data.description else None
        med.image_url = med_data.image_url.strip() if med_data.image_url else None
    else:
        med = Medicine(
            name=med_data.name.strip(),
            pzn=med_data.pzn.strip(),
            price=float(med_data.price),
            package=med_data.package.strip() if med_data.package else None,
            stock=0,
            rx_required=bool(med_data.rx_required),
            description=med_data.description.strip() if med_data.description else None,
            image_url=med_data.image_url.strip() if med_data.image_url else None,
        )
        db.add(med)
        db.flush()
    stock = _get_or_create_stock(db, med.id)
    if med_data.initial_stock > 0:
        stock.quantity = (stock.quantity or 0) + int(med_data.initial_stock)
    return med, stock


@router.get("/stock", response_model=list[WarehouseStockOut])
def list_warehouse_stock(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    rows = (
        db.query(WarehouseStock, Medicine)
        .join(Medicine, Medicine.id == WarehouseStock.medicine_id)
        .order_by(Medicine.name.asc())
        .all()
    )
    return [
        WarehouseStockOut(
            medicine_id=med.id,
            medicine_name=med.name,
            pzn=med.pzn,
            price=med.price,
            quantity=stock.quantity,
            updated_at=stock.updated_at,
        )
        for stock, med in rows
    ]


@router.get("/stock-breakdown")
def stock_breakdown(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    meds = db.query(Medicine).order_by(Medicine.name.asc()).all()
    warehouse_rows = db.query(WarehouseStock).all()
    warehouse_map = {r.medicine_id: r.quantity for r in warehouse_rows}
    dispatched = (
        db.query(WarehouseTransfer)
        .filter(
            WarehouseTransfer.direction == TransferDirection.warehouse_to_pharmacy,
            WarehouseTransfer.status == TransferStatus.dispatched,
        )
        .all()
    )
    pharmacy_totals: dict[int, int] = {}
    for row in dispatched:
        pharmacy_totals[row.medicine_id] = pharmacy_totals.get(row.medicine_id, 0) + (row.quantity or 0)
    return [
        {
            "medicine_id": m.id,
            "name": m.name,
            "pzn": m.pzn,
            "admin_stock": m.stock or 0,
            "warehouse_stock": warehouse_map.get(m.id, 0),
            "pharmacy_stock_dispatched": pharmacy_totals.get(m.id, 0),
        }
        for m in meds
    ]


@router.get("/pharmacy-options")
def list_pharmacy_options(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    # Pharmacy dashboard users are the source of truth for selectable pharmacies.
    pharmacy_users = db.query(User).filter(User.role == "pharmacy_store").order_by(User.id.asc()).all()
    synced_store_ids: list[int] = []
    for u in pharmacy_users:
        node_id = f"PH-U{u.id:03d}"
        store = db.query(PharmacyStore).filter(PharmacyStore.node_id == node_id).first()
        display_name = (u.name or "").strip() or (u.email or f"Pharmacy User {u.id}")
        if not store:
            store = PharmacyStore(
                node_id=node_id,
                name=display_name,
                location="Dashboard Linked",
                active=True,
                load=0,
                stock_count=0,
            )
            db.add(store)
            db.flush()
        else:
            store.name = display_name
            if not store.location:
                store.location = "Dashboard Linked"
            if store.active is None:
                store.active = True
        synced_store_ids.append(store.id)
    db.commit()

    if synced_store_ids:
        stores = (
            db.query(PharmacyStore)
            .filter(PharmacyStore.id.in_(synced_store_ids))
            .order_by(PharmacyStore.node_id.asc())
            .all()
        )
    else:
        stores = db.query(PharmacyStore).order_by(PharmacyStore.node_id.asc()).all()
    return [
        {"id": s.id, "node_id": s.node_id, "name": s.name, "location": s.location, "active": s.active}
        for s in stores
    ]


@router.get("/medicines/csv-template")
def warehouse_medicine_csv_template(
    current_user: User = Depends(get_current_user),
):
    _ensure_warehouse_or_admin(current_user)
    template = (
        "name,pzn,price,package,rx_required,description,image_url,initial_stock\n"
        "Paracetamol 500mg,13400000,45.5,10 tablets,false,Pain relief,,120\n"
    )
    return PlainTextResponse(template, media_type="text/csv")


@router.post("/medicines")
def add_warehouse_medicine(
    data: WarehouseMedicineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    if data.initial_stock < 0:
        raise HTTPException(status_code=400, detail="Initial stock cannot be negative")
    med, stock = _upsert_warehouse_medicine(db, data)
    db.commit()
    db.refresh(med)
    db.refresh(stock)
    return {
        "medicine_id": med.id,
        "name": med.name,
        "pzn": med.pzn,
        "warehouse_stock": stock.quantity,
        "message": "Medicine added/updated in warehouse",
    }


@router.post("/medicines/bulk")
def add_warehouse_medicines_bulk(
    payload: WarehouseMedicineBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    if not payload.medicines:
        raise HTTPException(status_code=400, detail="No medicines provided")
    created_or_updated = 0
    for med_data in payload.medicines:
        if med_data.initial_stock < 0:
            raise HTTPException(status_code=400, detail=f"Initial stock cannot be negative for {med_data.name}")
        _upsert_warehouse_medicine(db, med_data)
        created_or_updated += 1
    db.commit()
    return {"message": "Bulk upload completed", "processed": created_or_updated}


@router.put("/medicines/{medicine_id}")
def update_warehouse_medicine(
    medicine_id: int,
    data: WarehouseMedicineUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    update_data = data.model_dump(exclude_unset=True)
    warehouse_stock = update_data.pop("warehouse_stock", None)
    if "pzn" in update_data and update_data["pzn"]:
        existing = db.query(Medicine).filter(Medicine.pzn == update_data["pzn"], Medicine.id != medicine_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="PZN already exists")
    for key, value in update_data.items():
        setattr(med, key, value)
    stock = _get_or_create_stock(db, medicine_id)
    if warehouse_stock is not None:
        if warehouse_stock < 0:
            raise HTTPException(status_code=400, detail="Warehouse stock cannot be negative")
        stock.quantity = int(warehouse_stock)
    db.commit()
    db.refresh(med)
    db.refresh(stock)
    return {
        "medicine_id": med.id,
        "name": med.name,
        "pzn": med.pzn,
        "warehouse_stock": stock.quantity,
        "message": "Warehouse medicine updated",
    }


@router.delete("/medicines/{medicine_id}")
def delete_warehouse_medicine(
    medicine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    stock = db.query(WarehouseStock).filter(WarehouseStock.medicine_id == medicine_id).first()
    if stock:
        db.delete(stock)
    # Delete medicine only when there is no admin stock left.
    if (med.stock or 0) <= 0:
        has_transfers = db.query(WarehouseTransfer).filter(WarehouseTransfer.medicine_id == medicine_id).first()
        if not has_transfers:
            db.delete(med)
    db.commit()
    return {"message": "Medicine removed from warehouse stock"}


@router.post("/medicines/import-csv")
async def add_warehouse_medicines_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid CSV file")
    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    required = ["name", "pzn", "price", "package", "rx_required", "description", "image_url", "initial_stock"]
    headers = reader.fieldnames or []
    if headers != required:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format. Expected headers exactly: {','.join(required)}")

    processed = 0
    skipped = 0
    for row in reader:
        try:
            med_data = WarehouseMedicineCreate(
                name=(row.get("name") or "").strip(),
                pzn=(row.get("pzn") or "").strip(),
                price=float((row.get("price") or "0").strip()),
                package=(row.get("package") or "").strip() or None,
                rx_required=(row.get("rx_required") or "").strip().lower() in {"true", "1", "yes"},
                description=(row.get("description") or "").strip() or None,
                image_url=(row.get("image_url") or "").strip() or None,
                initial_stock=int((row.get("initial_stock") or "0").strip()),
            )
            if not med_data.name or not med_data.pzn:
                skipped += 1
                continue
            if med_data.initial_stock < 0:
                skipped += 1
                continue
            _upsert_warehouse_medicine(db, med_data)
            processed += 1
        except Exception:
            skipped += 1
    db.commit()
    return {"message": "CSV upload completed", "processed": processed, "skipped": skipped}


@router.get("/transfers", response_model=list[WarehouseTransferOut])
def list_transfers(
    direction: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_transfer_viewer(current_user)
    q = db.query(WarehouseTransfer)
    if direction:
        try:
            q = q.filter(WarehouseTransfer.direction == TransferDirection(direction))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid transfer direction")
    if current_user.role == "pharmacy_store":
        q = q.filter(WarehouseTransfer.direction == TransferDirection.warehouse_to_pharmacy)
    rows = q.order_by(WarehouseTransfer.created_at.desc()).limit(500).all()
    out: list[WarehouseTransferOut] = []
    for row in rows:
        out.append(
            WarehouseTransferOut(
                id=row.id,
                medicine_id=row.medicine_id,
                medicine_name=row.medicine.name if row.medicine else f"Medicine #{row.medicine_id}",
                quantity=row.quantity,
                direction=row.direction.value,
                status=row.status.value,
                pharmacy_store_id=row.pharmacy_store_id,
                pharmacy_store_name=row.pharmacy_store.name if row.pharmacy_store else None,
                note=row.note,
                created_by_user_id=row.created_by_user_id,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        )
    return out


@router.post("/transfers/admin-to-warehouse", response_model=WarehouseTransferOut)
def admin_send_to_warehouse(
    data: AdminToWarehouseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_admin(current_user)
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    med = db.query(Medicine).filter(Medicine.id == data.medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    if (med.stock or 0) < data.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient admin stock for {med.name}")
    med.stock = (med.stock or 0) - data.quantity
    stock = _get_or_create_stock(db, med.id)
    stock.quantity = (stock.quantity or 0) + data.quantity
    tx = WarehouseTransfer(
        medicine_id=med.id,
        quantity=data.quantity,
        direction=TransferDirection.admin_to_warehouse,
        status=TransferStatus.received,
        note=data.note,
        created_by_user_id=current_user.id,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return WarehouseTransferOut(
        id=tx.id,
        medicine_id=tx.medicine_id,
        medicine_name=med.name,
        quantity=tx.quantity,
        direction=tx.direction.value,
        status=tx.status.value,
        pharmacy_store_id=tx.pharmacy_store_id,
        pharmacy_store_name=None,
        note=tx.note,
        created_by_user_id=tx.created_by_user_id,
        created_at=tx.created_at,
        updated_at=tx.updated_at,
    )


@router.post("/transfers/warehouse-to-admin")
def warehouse_send_to_admin(
    data: AdminToWarehouseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    med = db.query(Medicine).filter(Medicine.id == data.medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    stock = db.query(WarehouseStock).filter(WarehouseStock.medicine_id == med.id).first()
    available = stock.quantity if stock else 0
    if available < data.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient warehouse stock for {med.name}")
    stock.quantity = available - data.quantity
    med.stock = (med.stock or 0) + data.quantity
    db.commit()
    return {
        "message": "Sent to admin inventory",
        "medicine_id": med.id,
        "medicine_name": med.name,
        "quantity": data.quantity,
        "admin_stock": med.stock,
        "warehouse_stock": stock.quantity,
    }


@router.post("/transfers/warehouse-to-pharmacy", response_model=WarehouseTransferOut)
def warehouse_send_to_pharmacy(
    data: WarehouseToPharmacyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    med = db.query(Medicine).filter(Medicine.id == data.medicine_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    store = db.query(PharmacyStore).filter(PharmacyStore.id == data.pharmacy_store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Pharmacy store not found")
    stock = db.query(WarehouseStock).filter(WarehouseStock.medicine_id == med.id).first()
    available = stock.quantity if stock else 0
    if available < data.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient warehouse stock for {med.name}")
    stock.quantity = available - data.quantity
    tx = WarehouseTransfer(
        medicine_id=med.id,
        quantity=data.quantity,
        direction=TransferDirection.warehouse_to_pharmacy,
        status=TransferStatus.requested,
        pharmacy_store_id=store.id,
        note=data.note,
        created_by_user_id=current_user.id,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return WarehouseTransferOut(
        id=tx.id,
        medicine_id=tx.medicine_id,
        medicine_name=med.name,
        quantity=tx.quantity,
        direction=tx.direction.value,
        status=tx.status.value,
        pharmacy_store_id=tx.pharmacy_store_id,
        pharmacy_store_name=store.name,
        note=tx.note,
        created_by_user_id=tx.created_by_user_id,
        created_at=tx.created_at,
        updated_at=tx.updated_at,
    )


@router.put("/transfers/{transfer_id}/status", response_model=WarehouseTransferOut)
def update_transfer_status(
    transfer_id: int,
    data: WarehouseTransferStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_warehouse_or_admin(current_user)
    row = db.query(WarehouseTransfer).filter(WarehouseTransfer.id == transfer_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Transfer not found")
    if row.direction != TransferDirection.warehouse_to_pharmacy:
        raise HTTPException(status_code=400, detail="Only warehouse to pharmacy transfers can be updated")
    try:
        next_status = TransferStatus(data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transfer status")
    allowed = {
        TransferStatus.requested: {TransferStatus.picking},
        TransferStatus.picking: {TransferStatus.packed},
        TransferStatus.packed: {TransferStatus.dispatched},
        TransferStatus.dispatched: set(),
        TransferStatus.received: set(),
    }
    if next_status == row.status:
        pass
    elif next_status not in allowed.get(row.status, set()):
        raise HTTPException(status_code=400, detail=f"Invalid transition from {row.status.value} to {next_status.value}")
    else:
        row.status = next_status
        if next_status == TransferStatus.dispatched and row.pharmacy_store:
            row.pharmacy_store.stock_count = (row.pharmacy_store.stock_count or 0) + row.quantity
    db.commit()
    db.refresh(row)
    return WarehouseTransferOut(
        id=row.id,
        medicine_id=row.medicine_id,
        medicine_name=row.medicine.name if row.medicine else f"Medicine #{row.medicine_id}",
        quantity=row.quantity,
        direction=row.direction.value,
        status=row.status.value,
        pharmacy_store_id=row.pharmacy_store_id,
        pharmacy_store_name=row.pharmacy_store.name if row.pharmacy_store else None,
        note=row.note,
        created_by_user_id=row.created_by_user_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
