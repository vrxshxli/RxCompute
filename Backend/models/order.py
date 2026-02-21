from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    verified = "verified"
    picking = "picking"
    packed = "packed"
    dispatched = "dispatched"
    delivered = "delivered"
    cancelled = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_uid = Column(String(30), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.pending)
    total = Column(Float, default=0.0)
    pharmacy = Column(String(50), nullable=True)
    payment_method = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    name = Column(String(200), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
