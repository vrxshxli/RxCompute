from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum, Boolean
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
    delivery_address = Column(String(255), nullable=True)
    delivery_lat = Column(Float, nullable=True)
    delivery_lng = Column(Float, nullable=True)
    pharmacy_approved_by_name = Column(String(120), nullable=True)
    pharmacy_approved_at = Column(DateTime(timezone=True), nullable=True)
    last_status_updated_by_role = Column(String(40), nullable=True)
    last_status_updated_by_name = Column(String(120), nullable=True)
    last_status_updated_at = Column(DateTime(timezone=True), nullable=True)
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
    dosage_instruction = Column(String(120), nullable=True)
    strips_count = Column(Integer, default=1)
    rx_required = Column(Boolean, default=False)
    prescription_file = Column(String(300), nullable=True)

    order = relationship("Order", back_populates="items")
