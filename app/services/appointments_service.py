"""
Business logic and CRUD operations for the Clinical Flow
Handles validation of scheduling rules, double booking prevention, and nested data retrieval
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    AppointmentNotFoundError,
    BaseBusinessException,
    DoubleBookingError,
    PastAppointmentError,
)
from fastapi import HTTPException, status
from app.models.appointments import Appointment, AppointmentStatus, Consultation, DiagnosisCatalog, Prescription, Triage
from app.schemas.appointments_schema import AppointmentCreate, TriageCreate, ConsultationCreate


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

# ---------------------------------------------------------------------------
# NEW: CLINICAL STATE TRANSITIONS & CLINICAL FLOW LOGIC
# ---------------------------------------------------------------------------

async def cancel_appointment(session: AsyncSession, appointment_id: UUID, reason: str) -> Appointment:
    """
    Cancels an appointment logistically (Soft Delete) and records the reason.
    """
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await session.execute(stmt)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise AppointmentNotFoundError(identifier=str(appointment_id))
        
    try:
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancellation_reason = reason
        await session.commit()
        return await get_appointment_by_id(session, appointment_id)
    except Exception as e:
        await session.rollback()
        raise e


async def create_triage(session: AsyncSession, appointment_id: UUID, triage_in: TriageCreate, nurse_id: UUID) -> Triage:
    """
    Registers patient vital signs and advances appointment status to WAITING.
    """
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await session.execute(stmt)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise AppointmentNotFoundError(identifier=str(appointment_id))
    
    if appointment.status not in [AppointmentStatus.SCHEDULED, AppointmentStatus.READY]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Appointment is not in a valid state for Triage (Must be SCHEDULED or READY)"
        )

    # Automatic BMI calculation
    bmi_calc = None
    if triage_in.weight_kg and triage_in.height_cm:
        height_m = float(triage_in.height_cm) / 100
        bmi_calc = float(triage_in.weight_kg) / (height_m ** 2)

    db_triage = Triage(
        appointment_id=appointment_id,
        nurse_id=nurse_id,
        weight_kg=triage_in.weight_kg,
        height_cm=triage_in.height_cm,
        bmi=bmi_calc,
        blood_pressure=triage_in.blood_pressure,
        temperature_c=triage_in.temperature_c,
        heart_rate_bpm=triage_in.heart_rate_bpm,
        respiratory_rate_rpm=triage_in.respiratory_rate_rpm,
        notes=triage_in.notes
    )

    try:
        session.add(db_triage)
        # Update status: Move from scheduled to waiting room
        appointment.status = AppointmentStatus.WAITING
        await session.commit()
        await session.refresh(db_triage)
        return db_triage
    except Exception as e:
        await session.rollback()
        raise e


async def create_consultation(
    session: AsyncSession, appointment_id: UUID, consultation_in: ConsultationCreate, doctor_id: UUID
) -> Consultation:
    """
    Creates a full consultation with nested prescriptions and diagnoses.
    Implements the Anti-Greenlet pattern by pre-fetching catalog records.
    """
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await session.execute(stmt)
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise AppointmentNotFoundError(identifier=str(appointment_id))
        
    if appointment.status != AppointmentStatus.WAITING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Patient must pass through Triage first (Appointment status must be WAITING)"
        )

    # 🚀 STEP 1: Early catalog search (Anti-Greenlet / Lazy Loading prevention)
    diag_stmt = select(DiagnosisCatalog).where(DiagnosisCatalog.id.in_(consultation_in.diagnosis_ids))
    diag_result = await session.execute(diag_stmt)
    found_diagnoses = diag_result.scalars().all()
    
    if len(found_diagnoses) != len(consultation_in.diagnosis_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="One or more Diagnosis IDs provided do not exist in the catalog"
        )

    # 🚀 STEP 2: Direct Consultation instantiation with M2M relationships mapped in-memory
    db_consultation = Consultation(
        appointment_id=appointment_id,
        doctor_id=doctor_id,
        subjective=consultation_in.clinical_notes,
        diagnoses=found_diagnoses
    )

    # 🚀 STEP 3: Iteration and nesting of prescriptions within the same unit of work
    for presc in consultation_in.prescriptions:
        # Attempt to extract duration days or use a safe default
        duration_days = 7
        if presc.duration:
            first_word = presc.duration.split()[0]
            if first_word.isdigit():
                duration_days = int(first_word)

        db_prescription = Prescription(
            medication=presc.medication_name,
            dose=presc.dosage,
            frequency=presc.frequency,
            duration_days=duration_days,
            consultation=db_consultation
        )
        session.add(db_prescription)

    try:
        session.add(db_consultation)
        # 🚀 STEP 4: Final clinical lifecycle closure
        appointment.status = AppointmentStatus.COMPLETED
        
        # 🚀 STEP 5: Atomic global try/commit transaction
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