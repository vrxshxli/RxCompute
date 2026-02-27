from datetime import datetime

from pydantic import BaseModel


class WarehouseStockOut(BaseModel):
    medicine_id: int
    medicine_name: str
    pzn: str
    price: float
    quantity: int
    updated_at: datetime | None = None


class AdminToWarehouseCreate(BaseModel):
    medicine_id: int
    quantity: int
    note: str | None = None


class WarehouseToPharmacyCreate(BaseModel):
    medicine_id: int
    quantity: int
    pharmacy_store_id: int
    note: str | None = None


class WarehouseTransferOut(BaseModel):
    id: int
    medicine_id: int
    medicine_name: str
    quantity: int
    direction: str
    status: str
    pharmacy_store_id: int | None = None
    pharmacy_store_name: str | None = None
    note: str | None = None
    created_by_user_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WarehouseTransferStatusUpdate(BaseModel):
    status: str


class WarehouseMedicineCreate(BaseModel):
    name: str
    pzn: str
    price: float
    package: str | None = None
    rx_required: bool = False
    description: str | None = None
    image_url: str | None = None
    initial_stock: int = 0


class WarehouseMedicineBulkCreate(BaseModel):
    medicines: list[WarehouseMedicineCreate]
