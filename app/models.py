from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("HealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    scans = relationship("ScanHistory", back_populates="user", cascade="all, delete-orphan")


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    diabetes = Column(Boolean, default=False, nullable=False)
    hypertension = Column(Boolean, default=False, nullable=False)
    lactose_intolerant = Column(Boolean, default=False, nullable=False)
    gluten_allergy = Column(Boolean, default=False, nullable=False)
    nut_allergy = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="profile")


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_name = Column(String(255), nullable=True)
    detected_ingredients = Column(Text, nullable=False, default="")
    safety_score = Column(Float, nullable=False)
    risk_message = Column(Text, nullable=False)
    scanned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="scans")
