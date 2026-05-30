"""
Pydantic schemas for Patient, PatientAccount, and Medical Background.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.models.patients import BloodType, Gender

from .base_schema import BaseSchema, NameStr, PhoneStr
from .users_schema import PasswordStr


# CATALOG SCHEMAS (Allergies & Diseases)
class CatalogBase(BaseSchema):
    name: NameStr


class AllergyResponse(CatalogBase):
    id: UUID


class ChronicDiseaseResponse(CatalogBase):
    id: UUID


# MEDICAL BACKGROUND SCHEMAS
class MedicalBackgroundBase(BaseSchema):
    blood_type: BloodType | None = None
    notes: str | None = Field(None, max_length=5000)


class MedicalBackgroundResponse(MedicalBackgroundBase):
    id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime


# PATIENT ACCOUNT SCHEMAS (ValCare)
class PatientAccountCreate(BaseSchema):
    """Credentials required to enable patient self-service portal access"""

    email: EmailStr
    password: PasswordStr


class PatientAccountResponse(BaseSchema):
    id: UUID
    email: EmailStr
    is_email_verified: bool
    last_login: datetime | None = None
    created_at: datetime


# CORE PATIENT SCHEMAS
class PatientBase(BaseSchema):
    document_number: str = Field(..., min_length=5, max_length=50, pattern=r"^[A-Za-z0-9\-]+$")
    first_name: NameStr
    last_name: NameStr
    birth_date: date

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Birth date cannot be in the future")
        if v.year < 1900:
            raise ValueError("Birth date cannot be valid")
        return v

    gender: Gender | None = None
    phone: PhoneStr | None = None
    email: EmailStr | None = None


class PatientCreate(PatientBase):
    """Schema used to create a patient with optional nested resources and relationships"""

    account: PatientAccountCreate | None = None
    medical_background: MedicalBackgroundBase | None = None

    allergy_ids: list[UUID] = Field(default_factory=list)
    chronic_disease_ids: list[UUID] = Field(default_factory=list)


class PatientUpdate(BaseSchema):
    """Partial update schema for patient demographic data"""

    first_name: NameStr | None = Field(None, min_length=2, max_length=100)
    last_name: NameStr | None = Field(None, min_length=2, max_length=100)
    birth_date: date | None = None
    gender: Gender | None = None
    phone: PhoneStr | None = None
    email: EmailStr | None = None


class PatientResponse(PatientBase):
    """Comprehensive patient profile returned to the frontend"""

    id: UUID
    created_at: datetime
    updated_at: datetime

    account: PatientAccountResponse | None = None
    medical_background: MedicalBackgroundResponse | None = None
    allergies: list[AllergyResponse] = Field(default_factory=list)
    chronic_diseases: list[ChronicDiseaseResponse] = Field(default_factory=list)
