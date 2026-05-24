from sqlalchemy import String, Boolean, DateTime, text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum
import uuid

from .base import Base

class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    RECEPTIONIST = "RECEPTIONIST"

class Specialty(Base):
    __tablename__ = "specialty"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Enable back_populates to navigate from Specialty to DoctorProfile
    doctors: Mapped[list["DoctorProfile"]] = relationship(back_populates="specialty")

class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[StaffRole] = mapped_column(Enum(StaffRole, name="staff_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    # Enable back_populates to navigate from Staff to DoctorProfile
    doctor_profile: Mapped["DoctorProfile"] = relationship(back_populates="staff", uselist=False, cascade="all, delete-orphan")

class DoctorProfile(Base):
    __tablename__ = "doctor_profile"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    # ForeignKey connecting to Staff, with cascade delete to ensure that if a Staff member is deleted, the associated DoctorProfile is also deleted
    staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialty_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("specialty.id"))
    medical_license: Mapped[str | None] = mapped_column(String(50))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Declare relationships to enable navigation between DoctorProfile, Staff, and Specialty
    staff: Mapped["Staff"] = relationship(back_populates="doctor_profile")
    specialty: Mapped["Specialty"] = relationship(back_populates="doctors")