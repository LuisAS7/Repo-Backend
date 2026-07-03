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
    DoctorNotAvailableError,
)
from app.models.appointments import Appointment, AppointmentStatus, AppointmentOrigin, Consultation, DiagnosisCatalog, Prescription, DoctorAvailability
from app.schemas.appointments_schema import AppointmentCreate, ConsultationCreate, WalkInCreate, DoctorAvailabilityCreate


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
    # Convertimos el día de la semana (ISO: Lunes=1, Domingo=7)
    day_of_week_sql = appointment_create.scheduled_date.isoweekday()
    
    # Buscamos la regla de disponibilidad que calce con el día y la ventana de atención
    avail_stmt = select(DoctorAvailability).where(
        and_(
            DoctorAvailability.doctor_id == appointment_create.doctor_id,
            DoctorAvailability.day_of_week == day_of_week_sql,
            DoctorAvailability.start_time <= appointment_create.scheduled_time,
            DoctorAvailability.end_time > appointment_create.scheduled_time
        )
    )
    avail_result = await session.execute(avail_stmt)
    availability = avail_result.scalar_one_or_none()

    if not availability:
        raise DoctorNotAvailableError(str(appointment_create.doctor_id), day_of_week_sql)

    # 2. Prevent Double Booking (Buscar si ya está ocupado ese slot)
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

    # 3. Data preparation and insertion
    appointment_data = appointment_create.model_dump()
    new_appointment = Appointment(**appointment_data)

    try:
        session.add(new_appointment)
        await session.commit()  # Commit to generate the ID
    except Exception as e:
        await session.rollback()
        if isinstance(e, BaseBusinessException):
            raise
        raise e

    return await get_appointment_by_id(session, new_appointment.id)

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


async def create_walk_in(session: AsyncSession, walk_in_data: WalkInCreate) -> Appointment:
    """
    Creates a walk-in appointment without a doctor assigned.
    """
    new_appointment = Appointment(
        patient_id=walk_in_data.patient_id,
        doctor_id=None,
        scheduled_date=walk_in_data.scheduled_date,
        scheduled_time=datetime.now().time().replace(second=0, microsecond=0),
        status=AppointmentStatus.WAITING,
        origin=AppointmentOrigin.WALK_IN,
        reason=walk_in_data.reason or "Atención de urgencia / Ingreso rápido",
    )

    try:
        session.add(new_appointment)
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e

    return await get_appointment_by_id(session, new_appointment.id)


async def get_doctor_workdays(session: AsyncSession, doctor_id: UUID) -> list[int]:
    """
    Retorna los números de los días de la semana (1-7) en los que el doctor registra atención.
    """
    stmt = (
        select(DoctorAvailability.day_of_week)
        .where(DoctorAvailability.doctor_id == doctor_id)
        .order_by(DoctorAvailability.day_of_week.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def create_availability(session: AsyncSession, availability_in: DoctorAvailabilityCreate) -> DoctorAvailability:
    """
    Guarda o actualiza una regla de disponibilidad semanal para un médico en la base de datos.
    """
    # Verificamos si ya existe una regla para ese doctor el mismo día de la semana
    stmt = select(DoctorAvailability).where(
        and_(
            DoctorAvailability.doctor_id == availability_in.doctor_id,
            DoctorAvailability.day_of_week == availability_in.day_of_week
        )
    )
    result = await session.execute(stmt)
    existing_availability = result.scalar_one_or_none()

    if existing_availability:
        # Si ya existe, actualizamos los rangos de horas
        existing_availability.start_time = availability_in.start_time
        existing_availability.end_time = availability_in.end_time
        existing_availability.slot_duration_minutes = availability_in.slot_duration_minutes
        db_obj = existing_availability
    else:
        # Si es nuevo, instanciamos el modelo ORM
        db_obj = DoctorAvailability(**availability_in.model_dump())
        session.add(db_obj)

    try:
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    except Exception as e:
        await session.rollback()
        raise e
