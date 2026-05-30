"""
Business logic and CRUD operations for the Clinical Flow
Handles validation of scheduling rules, double booking prevention, and nested data retrieval
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppointmentNotFoundError, DoubleBookingError, PastAppointmentError
from app.models.appointments import Appointment, AppointmentStatus, Consultation
from app.schemas.appointments_schema import AppointmentCreate


async def get_appointment_by_id(session: AsyncSession, appointment_id: UUID) -> Appointment:
    """
    Retrieves a full clinical appointment including its Triage and complete Consultation records
    """
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.triage),
            # Nested loading: Load consultation, and within it, load prescriptions and diagnoses
            selectinload(Appointment.consultation).selectinload(Consultation.prescriptions),
            selectinload(Appointment.consultation).selectinload(Consultation.diagnoses),
        )
        .where(Appointment.id == appointment_id)
    )
    result = await session.execute(stmt)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise AppointmentNotFoundError(identifier=str(appointment_id))

    return appointment


async def create_appointment(session: AsyncSession, appointment_create: AppointmentCreate) -> Appointment:
    """
    Schedules a new appointment
    Validates logical dates and ensures the doctor is not double-booked
    """
    # Temporal Logic Validation
    now = datetime.now()
    if appointment_create.scheduled_date < now.date():
        raise PastAppointmentError()

    if appointment_create.scheduled_date == now.date() and appointment_create.scheduled_time < now.time():
        raise PastAppointmentError()

    # Prevent Double Booking
    # Search for an active appointment with the same doctor, date, and time
    stmt = select(Appointment).where(
        and_(
            Appointment.doctor_id == appointment_create.doctor_id,
            Appointment.scheduled_date == appointment_create.scheduled_date,
            Appointment.scheduled_time == appointment_create.scheduled_time,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.WAITING, AppointmentStatus.READY]),
        )
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise DoubleBookingError()

    # Data preparation and insertion
    appointment_data = appointment_create.model_dump()
    new_appointment = Appointment(**appointment_data)

    async with session.begin():
        session.add(new_appointment)
        await session.flush()  # Ensure new_appointment.id is generated before commit

    return await get_appointment_by_id(session, new_appointment.id)


async def get_all_appointments(session: AsyncSession, skip: int = 0, limit: int = 50) -> list[Appointment]:
    """
    Retrieves a paginated list of appointments ordered by date and time
    """
    safe_limit = min(limit, 100)

    stmt = (
        select(Appointment)
        .options(selectinload(Appointment.triage))
        .order_by(Appointment.scheduled_date.desc(), Appointment.scheduled_time.desc())
        .offset(skip)
        .limit(safe_limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
