from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Float,
    DateTime
)

from sqlalchemy.orm import relationship

from datetime import datetime

from app.database import Base


class User(Base):

    __tablename__ = "users"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    name = Column(
        String,
        nullable=False
    )


    email = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )


    password = Column(
        String,
        nullable=False
    )


    profile = relationship(
        "HealthProfile",
        back_populates="user",
        uselist=False
    )


    scans = relationship(
        "ScanHistory",
        back_populates="user"
    )


    medicine_scans = relationship(
        "MedicineScan",
        back_populates="user"
    )


class HealthProfile(Base):

    __tablename__ = "health_profiles"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )


    diabetes = Column(
        Boolean,
        default=False
    )


    hypertension = Column(
        Boolean,
        default=False
    )


    lactose_intolerant = Column(
        Boolean,
        default=False
    )


    gluten_allergy = Column(
        Boolean,
        default=False
    )


    nut_allergy = Column(
        Boolean,
        default=False
    )


    user = relationship(
        "User",
        back_populates="profile"
    )


class ScanHistory(Base):

    __tablename__ = "scan_history"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )


    product_name = Column(
        String
    )


    safety_score = Column(
        Float
    )


    risk_message = Column(
        String
    )


    scanned_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    user = relationship(
        "User",
        back_populates="scans"
    )


class MedicineScan(Base):

    __tablename__ = "medicine_scans"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )


    medicine_name = Column(
        String
    )


    batch_number = Column(
        String
    )


    qr_verified = Column(
        Boolean
    )


    packaging_score = Column(
        Float
    )


    scanned_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    user = relationship(
        "User",
        back_populates="medicine_scans"
    )