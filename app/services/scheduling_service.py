from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.appointments import Appointment, AppointmentStatus, DoctorAvailability
from app.models.users import DoctorProfile, Specialty, Staff, StaffRole


async def get_available_specialties(session: AsyncSession) -> list[dict]:
    """Return the catalog of active medical specialties"""
    stmt = select(Specialty).order_by(Specialty.name)
    result = await session.execute(stmt)
    specialties = result.scalars().all()
    return [
        {
            "id": str(specialty.id),
            "name": specialty.name,
            "description": specialty.description,
        }
        for specialty in specialties
    ]


async def get_available_doctors(session: AsyncSession, specialty_id: UUID | None = None) -> list[dict]:
    """Retorna los médicos activos, opcionalmente filtrados por especialidad."""
    stmt = (
        select(Staff)
        .join(Staff.doctor_profile)
        .options(selectinload(Staff.doctor_profile).selectinload(DoctorProfile.specialty))
        .where(Staff.role == StaffRole.DOCTOR, Staff.is_active.is_(True))
    )
    if specialty_id:
        stmt = stmt.where(DoctorProfile.specialty_id == specialty_id)

    result = await session.execute(stmt)
    doctors = result.scalars().all()

    return [
        {
            "id": str(doctor.id),
            "full_name": f"{doctor.first_name} {doctor.last_name}".strip(),
            "specialty_id": str(doctor.doctor_profile.specialty_id) if doctor.doctor_profile else None,
            "specialty_name": doctor.doctor_profile.specialty.name
            if doctor.doctor_profile and doctor.doctor_profile.specialty
            else None,
        }
        for doctor in doctors
    ]


async def get_available_schedules(session: AsyncSession, doctor_id: UUID, selected_date: date) -> list[dict]:
    """Generate dynamically the available slots of a doctor for a specific date"""
    day_of_week = selected_date.isoweekday()

    # Consult the base availability of the doctor for the given day of the week
    avail_stmt = select(DoctorAvailability).where(
        and_(DoctorAvailability.doctor_id == doctor_id, DoctorAvailability.day_of_week == day_of_week)
    )
    availability = (await session.execute(avail_stmt)).scalar_one_or_none()

    if not availability:
        return []

    # Consult the occupied appointments
    appt_stmt = select(Appointment.scheduled_time).where(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_date == selected_date,
            Appointment.status != AppointmentStatus.CANCELED,
        )
    )
    busy_slots = {row for row in (await session.execute(appt_stmt)).scalars().all()}

    # Generate the schedule grid based on the doctor's availability and occupied slots
    available_slots = []

    current_dt = datetime.combine(selected_date, availability.start_time)
    end_dt = datetime.combine(selected_date, availability.end_time)
    slot_duration = timedelta(minutes=availability.slot_duration_minutes)

    while current_dt + slot_duration <= end_dt:
        slot_time = current_dt.time()

        if slot_time not in busy_slots:
            available_slots.append(
                {
                    "id": f"{selected_date}_{slot_time.strftime('%H:%M')}",
                    "scheduled_date": selected_date.isoformat(),
                    "scheduled_time": slot_time.strftime("%H:%M"),
                    "is_available": True,
                }
            )
        current_dt += slot_duration

    return available_slots
