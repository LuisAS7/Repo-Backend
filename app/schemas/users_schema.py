"""
Pydantic schemas for Staff, Speciality, and Doctor Profiles
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import EmailStr, Field

from app.models.users import StaffRole

from .base_schema import BaseSchema, NameStr

# REUSABLE TYPES
PasswordStr = Annotated[str, Field(min_length=8, max_length=128, pattern=r"^(?=.*[A-Za-z])(?=.*\d).+$")]


# SPECIALTY SCHEMAS
class SpecialtyBase(BaseSchema):
    name: NameStr
    description: str | None = None


class SpecialtyCreate(SpecialtyBase):
    """Schema for creating a new specialty"""

    pass


class SpecialtyResponse(SpecialtyBase):
    """Schema for returning specialty data"""

    id: UUID
    created_at: datetime


# DOCTOR PROFILE SCHEMAS
class DoctorProfileBase(BaseSchema):
    medical_license: str | None = None
    specialty_id: UUID | None = None


class DoctorProfileResponse(DoctorProfileBase):
    """Schema for returning doctor profile data"""

    id: UUID
    staff_id: UUID
    specialty: SpecialtyResponse | None = None


# STAFF SCHEMAS
class StaffBase(BaseSchema):
    first_name: NameStr
    last_name: NameStr
    email: EmailStr
    role: StaffRole
    is_active: bool = True


class StaffCreate(StaffBase):
    """Schema for creating a new staff member. Includes password field"""

    password: PasswordStr
    doctor_profile: DoctorProfileBase | None = None


class StaffUpdate(BaseSchema):
    """Schema for partial updates to staff member"""

    first_name: NameStr | None = Field(None, min_length=2, max_length=50)
    last_name: NameStr | None = Field(None, min_length=2, max_length=50)
    email: EmailStr | None = None
    role: StaffRole | None = None
    is_active: bool | None = None
    password: PasswordStr | None = None


class StaffResponse(StaffBase):
    """Schema used when returning staff data to the frontend. Excludes password"""

    id: UUID
    created_at: datetime
    updated_at: datetime
    doctor_profile: DoctorProfileResponse | None = None
