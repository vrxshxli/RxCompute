from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func

from database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    pzn = Column(String(20), unique=True, nullable=False, index=True)
    price = Column(Float, nullable=False)
    package = Column(String(50), nullable=True)
    stock = Column(Integer, default=0)
    rx_required = Column(Boolean, default=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
