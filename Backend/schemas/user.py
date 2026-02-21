from pydantic import BaseModel
from datetime import datetime


class UserRegister(BaseModel):
    name: str
    age: int
    gender: str
    email: str | None = None
    allergies: str | None = None
    conditions: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    email: str | None = None
    allergies: str | None = None
    conditions: str | None = None


class UserOut(BaseModel):
    id: int
    phone: str | None
    google_id: str | None = None
    name: str | None
    age: int | None
    gender: str | None
    email: str | None
    profile_picture: str | None = None
    allergies: str | None
    conditions: str | None
    is_verified: bool
    is_registered: bool
    created_at: datetime | None

    class Config:
        from_attributes = True
