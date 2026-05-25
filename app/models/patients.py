import uuid
import enum
from datetime import date

from sqlalchemy import String, Date, Boolean, ForeignKey, Table, Column, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk, str_100, str_255, created_at_dt

# ENUMS
class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"

class BloodType(str, enum.Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"

# ASSOCIATION TABLES 
patient_allergy = Table(
    "patient_allergy",
    Base.metadata,
    Column("patient_id", ForeignKey("patient.id", ondelete="CASCADE"), primary_key=True),
    Column("allergy_id", ForeignKey("allergy.id", ondelete="CASCADE"), primary_key=True),
)

patient_disease = Table(
    "patient_disease",
    Base.metadata,
    Column("patient_id", ForeignKey("patient.id", ondelete="CASCADE"), primary_key=True),
    Column("disease_id", ForeignKey("chronic_disease.id", ondelete="CASCADE"), primary_key=True),
)

# CATALOG TABLES
class Allergy(Base):
    """Catalog table for known medical allergies"""
    __tablename__ = "allergy"

    id: Mapped[uuid_pk]
    name: Mapped[str_100] = mapped_column(unique=True, nullable=False)

    patients: Mapped[list["Patient"]] = relationship(secondary=patient_allergy, back_populates="allergies")

class ChronicDisease(Base):
    """Catalog table for known chronic diseases"""
    __tablename__ = "chronic_disease"

    id: Mapped[uuid_pk]
    name: Mapped[str_100] = mapped_column(unique=True, nullable=False)

    patients: Mapped[list["Patient"]] = relationship(secondary=patient_disease, back_populates="chronic_diseases")

# CORE PATIENT TABLE
class Patient(Base, TimestampMixin):
    """Core patient demographic data and relationships to medical background"""
    __tablename__ = "patient"

    id: Mapped[uuid_pk]
    document_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[str_100] = mapped_column(nullable=False)
    last_name: Mapped[str_100] = mapped_column(nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender | None] = mapped_column(SQLEnum(Gender, name="gender_enum"))
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str_255 | None]
    
    # Relationships
    account: Mapped["PatientAccount"] = relationship(back_populates="patient", uselist=False, cascade="all, delete-orphan")
    medical_background: Mapped["MedicalBackground"] = relationship(back_populates="patient", uselist=False, cascade="all, delete-orphan")
    
    # Many-to-Many relationships using the association tables
    allergies: Mapped[list["Allergy"]] = relationship(secondary=patient_allergy, back_populates="patients")
    chronic_diseases: Mapped[list["ChronicDisease"]] = relationship(secondary=patient_disease, back_populates="patients")


class PatientAccount(Base):
    """Credentials for patient self-service portal (ValCare)"""
    __tablename__ = "patient_account"

    id: Mapped[uuid_pk]
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.id", ondelete="CASCADE"), unique=True, nullable=False)
    email: Mapped[str_255] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str_255] = mapped_column(nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[created_at_dt | None] = mapped_column(nullable=True)
    created_at: Mapped[created_at_dt]

    patient: Mapped["Patient"] = relationship(back_populates="account")

class MedicalBackground(Base, TimestampMixin):
    """Patient's static medical history (Blood type, general notes)"""
    __tablename__ = "medical_background"

    id: Mapped[uuid_pk]
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.id", ondelete="CASCADE"), unique=True, nullable=False)
    blood_type: Mapped[BloodType | None] = mapped_column(SQLEnum(BloodType, name="blood_type_enum"))
    notes: Mapped[str | None]

    patient: Mapped["Patient"] = relationship(back_populates="medical_background")