"""
Pydantic schemas for the Clinical Flow: Appointments, Triage (Vital Signs), and Consultations (SOAP notes).
"""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import Field, model_validator

from app.models.appointments import AppointmentOrigin, AppointmentStatus

from .base_schema import BaseSchema, ClinicalNoteStr, ShortReasonStr


# DIAGNOSIS CATALOG SCHEMAS
class DiagnosisCatalogResponse(BaseSchema):
    """Schema for returning official diagnosis codes (e.g., ICD-10)"""

    id: UUID
    code: str
    name: str


# PRESCRIPTION SCHEMAS
class PrescriptionBase(BaseSchema):
    """Schema for creating and returning prescriptions associated with consultations"""

    medication: str = Field(..., min_length=2, max_length=255)
    dose: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration_days: int = Field(..., gt=0, description="Duration in days must be greater than 0")


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionResponse(PrescriptionBase):
    id: UUID
    consultation_id: UUID
    created_at: datetime


# CONSULTATION (SOAP) SCHEMAS
class ConsultationBase(BaseSchema):
    subjective: ClinicalNoteStr | None = None
    objective: ClinicalNoteStr | None = None
    assessment: ClinicalNoteStr | None = None
    plan: ClinicalNoteStr | None = None


class ConsultationCreate(ConsultationBase):
    prescriptions: list[PrescriptionCreate] = Field(default_factory=list)
    diagnosis_ids: list[UUID] = Field(default_factory=list)


class ConsultationUpdate(BaseSchema):
    subjective: ClinicalNoteStr | None = None
    objective: ClinicalNoteStr | None = None
    assessment: ClinicalNoteStr | None = None
    plan: ClinicalNoteStr | None = None


class ConsultationResponse(ConsultationBase):
    id: UUID
    appointment_id: UUID
    created_at: datetime
    updated_at: datetime

    prescriptions: list[PrescriptionResponse] = Field(default_factory=list)
    diagnoses: list[DiagnosisCatalogResponse] = Field(default_factory=list)


# TRIAGE (VITAL SIGNS) SCHEMAS
class TriageBase(BaseSchema):
    weight_kg: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    height_cm: Decimal | None = Field(None, max_digits=5, decimal_places=2)
    bmi: Decimal | None = Field(None, max_digits=4, decimal_places=2)
    blood_pressure: str | None = Field(None, max_length=20, pattern=r"^\d{2,3}\/\d{2,3}$")
    temperature_c: Decimal | None = Field(None, max_digits=4, decimal_places=1)
    notes: ClinicalNoteStr | None = None


class TriageCreate(TriageBase):
    nurse_id: UUID | None = None


class TriageUpdate(TriageBase):
    pass


class TriageResponse(TriageBase):
    id: UUID
    appointment_id: UUID
    nurse_id: UUID
    created_at: datetime


# APPOINTMENT SCHEMAS
class AppointmentBase(BaseSchema):
    scheduled_date: date
    scheduled_time: time
    reason: ShortReasonStr | None = None


class AppointmentCreate(AppointmentBase):
    patient_id: UUID
    doctor_id: UUID
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    origin: AppointmentOrigin = AppointmentOrigin.VALSYNC


class AppointmentUpdate(BaseSchema):
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    status: AppointmentStatus | None = None
    cancellation_reason: ShortReasonStr | None = None


class AppointmentResponse(AppointmentBase):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    status: AppointmentStatus
    origin: AppointmentOrigin
    cancellation_reason: ShortReasonStr | None = None
    created_at: datetime
    updated_at: datetime

    triage: TriageResponse | None = None
    consultation: ConsultationResponse | None = None


# DOCTOR AVAILABILITY SCHEMAS
class DoctorAvailabilityBase(BaseSchema):
    day_of_week: int = Field(..., ge=1, le=7)
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(default=30, gt=0)

    @model_validator(mode="after")
    def validate_time_range(self) -> "DoctorAvailabilityBase":
        """Ensure that end_time is later than start_time"""
        if self.start_time >= self.end_time:
            raise ValueError("end_time must be later than start_time")
        return self


class DoctorAvailabilityCreate(DoctorAvailabilityBase):
    doctor_id: UUID


class DoctorAvailabilityResponse(DoctorAvailabilityBase):
    id: UUID
    doctor_id: UUID
