from datetime import datetime

from pydantic import BaseModel, Field


class PharmacyStoreCreate(BaseModel):
    node_id: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=180)
    active: bool = True
    load: int = Field(default=0, ge=0, le=100)
    stock_count: int = Field(default=0, ge=0)


class PharmacyStoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    location: str | None = Field(default=None, min_length=2, max_length=180)
    active: bool | None = None
    load: int | None = Field(default=None, ge=0, le=100)
    stock_count: int | None = Field(default=None, ge=0)


class PharmacyStoreOut(BaseModel):
    id: int
    node_id: str
    name: str
    location: str
    active: bool
    load: int
    stock_count: int
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True
