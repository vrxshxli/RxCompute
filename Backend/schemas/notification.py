from pydantic import BaseModel
from datetime import datetime


class NotificationCreate(BaseModel):
    type: str = "system"
    title: str
    body: str
    has_action: bool = False


class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    body: str
    is_read: bool
    has_action: bool
    created_at: datetime | None

    class Config:
        from_attributes = True
