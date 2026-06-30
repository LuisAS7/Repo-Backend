from datetime import date, time
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.models.patients import Gender

from .base_schema import BaseSchema, NameStr
from .users_schema import validate_password_rules


class ValcareRegisterRequest(BaseSchema):
    document_number: str = Field(..., min_length=5, max_length=50, pattern=r"^[A-Za-z0-9\-]+$")
    first_name: NameStr
    last_name: NameStr
    birth_date: date
    gender: Gender | None = None

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_rules(value)


class ValcareProfileResponse(BaseSchema):
    id: UUID
    document_number: str
    first_name: str
    last_name: str
    email: EmailStr
    gender: Gender


class ValcareAppointmentBooking(BaseSchema):
    scheduled_date: date
    scheduled_time: time
    doctor_id: UUID
    reason: str | None = None
