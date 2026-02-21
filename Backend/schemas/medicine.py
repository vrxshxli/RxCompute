from pydantic import BaseModel
from datetime import datetime


class MedicineCreate(BaseModel):
    name: str
    pzn: str
    price: float
    package: str | None = None
    stock: int = 0
    rx_required: bool = False
    description: str | None = None


class MedicineUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    package: str | None = None
    stock: int | None = None
    rx_required: bool | None = None
    description: str | None = None


class MedicineOut(BaseModel):
    id: int
    name: str
    pzn: str
    price: float
    package: str | None
    stock: int
    rx_required: bool
    description: str | None
    created_at: datetime | None

    class Config:
        from_attributes = True
