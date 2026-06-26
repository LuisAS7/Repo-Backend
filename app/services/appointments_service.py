"""
Business logic and CRUD operations for the Clinical Flow
Handles validation of scheduling rules, double booking prevention, and nested data retrieval
"""

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    AppointmentNotFoundError,
    BaseBusinessException,
    DoubleBookingError,
    PastAppointmentError,
)
from app.models.appointments import Appointment, AppointmentStatus, Consultation, DiagnosisCatalog, Prescription
from app.schemas.appointments_schema import AppointmentCreate, ConsultationCreate


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

    try:
        session.add(new_appointment)
        await session.commit()  # Commit to generate the ID for the new appointment
    except Exception as e:
        await session.rollback()
        if isinstance(e, BaseBusinessException):
            raise
        raise e

    return await get_appointment_by_id(session, new_appointment.id)


async def get_all_appointments(session: AsyncSession, skip: int = 0, limit: int = 50) -> list[Appointment]:
    """
    Retrieves a paginated list of appointments ordered by date and time
    """
    safe_limit = min(limit, 100)

    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.triage),
            selectinload(Appointment.consultation).selectinload(Consultation.prescriptions),
            selectinload(Appointment.consultation).selectinload(Consultation.diagnoses),
        )
        .order_by(Appointment.scheduled_date.desc(), Appointment.scheduled_time.desc())
        .offset(skip)
        .limit(safe_limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def cancel_appointment(session: AsyncSession, appointment_id: UUID, reason: str) -> Appointment:
    """
    Cancels an appointment logistically (Soft Delete) and records the reason
    """
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await session.execute(stmt)
    appointment = result.scalar_one_or_none()

    if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel an appointment that is already {appointment.status.value}",
        )

    if not appointment:
        raise AppointmentNotFoundError(identifier=str(appointment_id))

    try:
        appointment.status = AppointmentStatus.CANCELED
        appointment.cancellation_reason = reason
        await session.commit()
        return await get_appointment_by_id(session, appointment_id)
    except Exception as e:
        await session.rollback()
        raise e


async def create_consultation(
    session: AsyncSession, appointment_id: UUID, consultation_in: ConsultationCreate, doctor_id: UUID
) -> Consultation:
    """
    Creates a full consultation with nested prescriptions and diagnoses
    Implements the Anti-Greenlet pattern by pre-fetching catalog records
    """
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await session.execute(stmt)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise AppointmentNotFoundError(identifier=str(appointment_id))

    if appointment.status != AppointmentStatus.WAITING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient must pass through Triage first (Appointment status must be WAITING)",
        )

    # Early catalog search (Anti-Greenlet / Lazy Loading prevention)
    diag_stmt = select(DiagnosisCatalog).where(DiagnosisCatalog.id.in_(consultation_in.diagnosis_ids))
    diag_result = await session.execute(diag_stmt)
    found_diagnoses = diag_result.scalars().all()

    if len(found_diagnoses) != len(consultation_in.diagnosis_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more Diagnosis IDs provided do not exist in the catalog",
        )

    # Direct Consultation instantiation with M2M relationships mapped in-memory
    db_consultation = Consultation(
        appointment_id=appointment_id,
        doctor_id=doctor_id,
        subjective=consultation_in.subjective,
        objective=consultation_in.objective,
        assessment=consultation_in.assessment,
        plan=consultation_in.plan,
        diagnoses=found_diagnoses,
    )

    for presc in consultation_in.prescriptions:
        db_prescription = Prescription(
            medication=presc.medication,
            dose=presc.dose,
            frequency=presc.frequency,
            duration_days=presc.duration_days,
            consultation=db_consultation,
        )
        session.add(db_prescription)

    try:
        session.add(db_consultation)
        appointment.status = AppointmentStatus.COMPLETED
        await session.commit()

        # Return the consultation safely reloaded using selectinload
        return_stmt = (
            select(Consultation)
            .options(selectinload(Consultation.prescriptions), selectinload(Consultation.diagnoses))
            .where(Consultation.id == db_consultation.id)
        )
        return_res = await session.execute(return_stmt)
        return return_res.scalar_one()
    except Exception as e:
        await session.rollback()
        raise e
