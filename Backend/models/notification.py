from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func
import enum

from database import Base


class NotificationType(str, enum.Enum):
    refill = "refill"
    order = "order"
    safety = "safety"
    system = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(SAEnum(NotificationType), default=NotificationType.system)
    title = Column(String(200), nullable=False)
    body = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    has_action = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
