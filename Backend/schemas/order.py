from pydantic import BaseModel
from datetime import datetime


class OrderItemCreate(BaseModel):
    medicine_id: int
    name: str
    quantity: int = 1
    price: float
    dosage_instruction: str | None = None
    strips_count: int = 1
    prescription_file: str | None = None


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]
    pharmacy: str | None = None
    payment_method: str | None = None


class OrderItemOut(BaseModel):
    id: int
    medicine_id: int
    name: str
    quantity: int
    price: float
    dosage_instruction: str | None = None
    strips_count: int
    rx_required: bool
    prescription_file: str | None = None

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    order_uid: str
    user_id: int
    status: str
    total: float
    pharmacy: str | None
    payment_method: str | None
    items: list[OrderItemOut] = []
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str
