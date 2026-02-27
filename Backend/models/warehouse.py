import enum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class TransferDirection(str, enum.Enum):
    admin_to_warehouse = "admin_to_warehouse"
    warehouse_to_pharmacy = "warehouse_to_pharmacy"


class TransferStatus(str, enum.Enum):
    received = "received"
    requested = "requested"
    picking = "picking"
    packed = "packed"
    dispatched = "dispatched"


class WarehouseStock(Base):
    __tablename__ = "warehouse_stock"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False, unique=True, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    medicine = relationship("Medicine")


class WarehouseTransfer(Base):
    __tablename__ = "warehouse_transfers"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    direction = Column(SAEnum(TransferDirection), nullable=False, index=True)
    status = Column(SAEnum(TransferStatus), nullable=False, index=True)
    pharmacy_store_id = Column(Integer, ForeignKey("pharmacy_stores.id"), nullable=True, index=True)
    note = Column(String(300), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    medicine = relationship("Medicine")
    pharmacy_store = relationship("PharmacyStore")


class PharmacyStock(Base):
    __tablename__ = "pharmacy_stock"
    __table_args__ = (UniqueConstraint("pharmacy_store_id", "medicine_id", name="uq_pharmacy_store_medicine"),)

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_store_id = Column(Integer, ForeignKey("pharmacy_stores.id"), nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    pharmacy_store = relationship("PharmacyStore")
    medicine = relationship("Medicine")
