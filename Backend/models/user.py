from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    email = Column(String(150), nullable=True)
    allergies = Column(Text, nullable=True)       # comma-separated
    conditions = Column(Text, nullable=True)       # comma-separated
    is_verified = Column(Boolean, default=False)
    is_registered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), nullable=False, index=True)
    otp = Column(String(6), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
