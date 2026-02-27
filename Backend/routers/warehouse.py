from fastapi import APIRouter, Depends, HTTPException, Query
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
