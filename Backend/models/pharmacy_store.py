from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from database import Base


class PharmacyStore(Base):
    __tablename__ = "pharmacy_stores"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    location = Column(String(180), nullable=False)
    active = Column(Boolean, default=True)
    load = Column(Integer, default=0)
    stock_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
