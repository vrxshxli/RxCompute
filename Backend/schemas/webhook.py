from datetime import datetime

from pydantic import BaseModel


class WebhookLogOut(BaseModel):
    id: int
    event_type: str
    target_url: str
    payload: str
    response_status: int | None
    response_body: str | None
    error_message: str | None
    created_at: datetime | None

    class Config:
        from_attributes = True
