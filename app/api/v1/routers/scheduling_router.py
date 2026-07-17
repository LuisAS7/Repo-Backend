from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import RoleChecker, get_db
from app.models.appointments import DoctorAvailability
from app.models.users import Staff, StaffRole
from app.schemas.appointments_schema import DoctorAvailabilityCreate
from app.services import scheduling_service

router = APIRouter(prefix="/scheduling", tags=["Scheduling & Catalog"])

# Declarate a dependency to check if the current user
require_clinic_staff = Depends(RoleChecker([StaffRole.ADMIN, StaffRole.RECEPTIONIST]))


@router.get(
    "/specialties",
    status_code=status.HTTP_200_OK,
    summary="List specialties for clinic agendment",
)
async def get_clinic_specialties(
    session: AsyncSession = Depends(get_db),
    current_user: Staff = require_clinic_staff,
):
    """
    Provide the list of active specialties for the clinic.
    This is used in the first step of the scheduling flow.
    """
    return await scheduling_service.get_available_specialties(session)


@router.get(
    "/doctors",
    status_code=status.HTTP_200_OK,
    summary="List active doctors filtered by specialty",
)
async def get_clinic_doctors(
    specialty_id: UUID | None = None,
    session: AsyncSession = Depends(get_db),
    current_user: Staff = require_clinic_staff,
):
    """
    Provide the list of active doctors. Allows optional filtering by specialty
    for the second step of the scheduling flow.
    """
    return await scheduling_service.get_available_doctors(session, specialty_id)


@router.get(
    "/schedules",
    status_code=status.HTTP_200_OK,
    summary="Get dynamic available slots for a doctor",
)
async def get_doctor_schedules(
    doctor_id: UUID,
    date: date,
    session: AsyncSession = Depends(get_db),
    current_user: Staff = require_clinic_staff,
):
    """
    Calculate dynamically the grid of available slots for a doctor based on:
    1. Their weekly availability rules (DoctorAvailability)
    2. Cross-reference with already scheduled appointments
        that are not canceled on that specific date.
    """
    return await scheduling_service.get_available_schedules(session=session, doctor_id=doctor_id, selected_date=date)


@router.post("/doctor-availability", status_code=status.HTTP_201_CREATED)
async def create_doctor_availability(
    availability_in: DoctorAvailabilityCreate,
    session: AsyncSession = Depends(get_db),
    current_staff=require_clinic_staff,
):
    """Create or update the availability of a doctor for a specific day of the week.
    This endpoint is used by clinic staff to manage doctor schedules."""

    # Search for existing availability for the same doctor and day of the week
    stmt = select(DoctorAvailability).where(
        DoctorAvailability.doctor_id == availability_in.doctor_id,
        DoctorAvailability.day_of_week == availability_in.day_of_week,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        await session.delete(existing)

    # Insert the new availability record
    new_avail = DoctorAvailability(**availability_in.model_dump())
    session.add(new_avail)
    await session.commit()

    return {"message": "Availability created successfully"}


@router.get("/doctor-availability/{doctor_id}", status_code=status.HTTP_200_OK)
async def get_doctor_availability(
    doctor_id: UUID, session: AsyncSession = Depends(get_db), current_staff=require_clinic_staff
):
    """Devuelve todos los bloques de disponibilidad configurados para un médico."""
    stmt = (
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == doctor_id)
        .order_by(DoctorAvailability.day_of_week)
    )
    result = await session.execute(stmt)
    return result.scalars().all()
