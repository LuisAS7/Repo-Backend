import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk, str_100, str_255, created_at_dt

class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    RECEPTIONIST = "RECEPTIONIST"

class Specialty(Base):
    """Catalog table for medical specialties"""
    __tablename__ = "specialty"

    id: Mapped[uuid_pk]
    name: Mapped[str_100] = mapped_column(unique=True, nullable=False)
    description: Mapped[str | None]
    created_at: Mapped[created_at_dt]

    # Enable back_populates to navigate from Specialty to DoctorProfile
    doctors: Mapped[list["DoctorProfile"]] = relationship(back_populates="specialty")

class Staff(Base, TimestampMixin):
    """Core user table for clinic employees"""
    __tablename__ = "staff"

    id: Mapped[uuid_pk]
    first_name: Mapped[str_100] = mapped_column(nullable=False)
    last_name: Mapped[str_100] = mapped_column(nullable=False)
    email: Mapped[str_255] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str_255] = mapped_column(nullable=False)
    role: Mapped[StaffRole] = mapped_column(Enum(StaffRole, name="staff_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Enable back_populates to navigate from Staff to DoctorProfile
    doctor_profile: Mapped["DoctorProfile"] = relationship(back_populates="staff", uselist=False, cascade="all, delete-orphan")

class DoctorProfile(Base):
    """Specific medical data for staff members with the DOCTOR role"""
    __tablename__ = "doctor_profile"

    id: Mapped[uuid_pk]
    staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialty_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("specialty.id"))
    medical_license: Mapped[str | None] = mapped_column(String(50))
    
    created_at: Mapped[created_at_dt]

    # Declare relationships to enable navigation between DoctorProfile, Staff, and Specialty
    staff: Mapped["Staff"] = relationship(back_populates="doctor_profile")
    specialty: Mapped["Specialty"] = relationship(back_populates="doctors")