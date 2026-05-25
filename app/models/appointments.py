import uuid
import enum
from datetime import date, time
from decimal import Decimal

from sqlalchemy import String, Date, Time, Numeric, Text, ForeignKey, Table, Column, Enum, Integer, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk, str_100, str_255, created_at_dt
from .users import Staff
from .patients import Patient

# ENUMS
class AppointmentStatus(str, enum.Enum):
    """Lifecycle states of a clinical appointment"""
    SCHEDULED = "SCHEDULED"
    WAITING = "WAITING"
    READY = "READY"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"

class AppointmentOrigin(str, enum.Enum):
    """Tracks if the appointment was booked by Staff or by the Patient through the ValCare portal"""
    VALSYNC = "VALSYNC"
    VALCARE = "VALCARE"

# ASSOCIATION TABLES 
consultation_diagnosis = Table(
    "consultation_diagnosis",
    Base.metadata,
    Column("consultation_id", ForeignKey("consultation.id", ondelete="CASCADE"), primary_key=True),
    Column("diagnosis_id", ForeignKey("diagnosis_catalog.id", ondelete="CASCADE"), primary_key=True),
)

# CATALOG TABLES
class DiagnosisCatalog(Base):
    """Universal diagnosis catalog (e.g., ICD-10 codes)"""
    __tablename__ = "diagnosis_catalog"

    id: Mapped[uuid_pk]
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

# CORE APPOINTMENT-RELATED TABLES
class DoctorAvailability(Base):
    """Weekly working hours for doctors to enable patient self-scheduling"""
    __tablename__ = "doctor_availability"

    id: Mapped[uuid_pk]
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False) # 1=Monday, 7=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

class Appointment(Base, TimestampMixin):
    """Core appointment entity linking patients with doctors and tracking the clinical encounter lifecycle"""
    __tablename__ = "appointment"

    id: Mapped[uuid_pk]
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.id"), nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff.id"), nullable=False)
    
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus, name="appointment_status"), default=AppointmentStatus.SCHEDULED)
    origin: Mapped[AppointmentOrigin] = mapped_column(Enum(AppointmentOrigin, name="appointment_origin"), default=AppointmentOrigin.VALSYNC)
    
    reason: Mapped[str | None] = mapped_column(Text)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)

    # Relationships
    patient: Mapped["Patient"] = relationship()
    doctor: Mapped["Staff"] = relationship()
    triage: Mapped["Triage"] = relationship(back_populates="appointment", uselist=False)
    consultation: Mapped["Consultation"] = relationship(back_populates="appointment", uselist=False)

class Triage(Base):
    """Vital signs recorded by nursing staff before consultation"""
    __tablename__ = "triage"

    id: Mapped[uuid_pk]
    appointment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("appointment.id", ondelete="CASCADE"), unique=True, nullable=False)
    nurse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff.id"), nullable=False)
    
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    bmi: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    blood_pressure: Mapped[str | None] = mapped_column(String(20))
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    notes: Mapped[str | None] = mapped_column(Text)
    
    created_at: Mapped[created_at_dt]

    appointment: Mapped["Appointment"] = relationship(back_populates="triage")

class Consultation(Base, TimestampMixin):
    """Medical encounter notes written by the doctor (SOAP methodology)"""
    __tablename__ = "consultation"

    id: Mapped[uuid_pk]
    appointment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("appointment.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    subjective: Mapped[str | None] = mapped_column(Text)
    objective: Mapped[str | None] = mapped_column(Text)
    assessment: Mapped[str | None] = mapped_column(Text)
    plan: Mapped[str | None] = mapped_column(Text)

    # Relationships
    appointment: Mapped["Appointment"] = relationship(back_populates="consultation")
    prescriptions: Mapped[list["Prescription"]] = relationship(back_populates="consultation", cascade="all, delete-orphan")
    diagnoses: Mapped[list["DiagnosisCatalog"]] = relationship(secondary=consultation_diagnosis)


class Prescription(Base):
    """Medications prescribed during a specific consultation"""
    __tablename__ = "prescription"

    id: Mapped[uuid_pk]
    consultation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("consultation.id", ondelete="CASCADE"), nullable=False)
    
    medication: Mapped[str] = mapped_column(String(255), nullable=False)
    dose: Mapped[str_100] = mapped_column(nullable=False)
    frequency: Mapped[str_100] = mapped_column(nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at: Mapped[created_at_dt]

    consultation: Mapped["Consultation"] = relationship(back_populates="prescriptions")