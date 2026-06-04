"""
Pydantic schemas for Staff, Speciality, and Doctor Profiles
"""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.models.users import StaffRole

from .base_schema import BaseSchema, NameStr, Annotated

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 72


# Password validation function to enforce complexity rules on both create and update operations
def validate_password_rules(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters")

    if not any(c.isalpha() for c in password):
        raise ValueError("Password must contain at least one letter")

    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one number")

    if not any(not c.isalnum() for c in password):
        raise ValueError("Password must contain at least one special character")

    return password
# REUSABLE TYPES
PasswordStr = Annotated[str, Field(min_length=8, max_length=128)]


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

    password: str
    doctor_profile: DoctorProfileBase | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_rules(value)


class StaffUpdate(BaseSchema):
    """Schema for partial updates to staff member"""

    first_name: NameStr | None = Field(None, min_length=2, max_length=50)
    last_name: NameStr | None = Field(None, min_length=2, max_length=50)
    email: EmailStr | None = None
    role: StaffRole | None = None
    is_active: bool | None = None
    password: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None:
            return value

        return validate_password_rules(value)


class StaffResponse(StaffBase):
    """Schema used when returning staff data to the frontend. Excludes password"""

    id: UUID
    created_at: datetime
    updated_at: datetime
    doctor_profile: DoctorProfileResponse | None = None

# AUTH SCHEMAS
class LoginRequest(BaseSchema):
    """Schema for login credentials"""
    email: EmailStr
    password: str


class TokenResponse(BaseSchema):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"