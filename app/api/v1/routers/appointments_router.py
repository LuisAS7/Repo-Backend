"""
API Router for Clinical Flow Management
Exposes RESTful endpoints for the appointments_service to manage
appointments scheduling and retrieval
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker, get_current_user, get_db
from app.models.users import Staff, StaffRole
from app.schemas.appointments_schema import AppointmentCreate, AppointmentResponse
from app.services import appointments_service

# Create a router instance for appointment-related endpoints
router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a new appointment",
)
async def create_appointment(
    appointment_in: AppointmentCreate, 
    session: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(RoleChecker([StaffRole.ADMIN, StaffRole.NURSE]))
):
    """
    Schedules a new appointment for a patient with a doctor
    Validates scheduling rules and prevents double booking
    """
    return await appointments_service.create_appointment(session, appointment_in)


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an appointment by ID",
)
async def get_appointment(appointment_id: UUID, 
    session: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user)):
    """
    Retrieves a full clinical appointment including Triage and Consultation records
    """
    return await appointments_service.get_appointment_by_id(session, appointment_id)


@router.get(
    "/",
    response_model=list[AppointmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all appointments with pagination",
)
async def get_all_appointments(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    session: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """
    Retrieves a paginated list of all appointments ordered by date
    """
    return await appointments_service.get_all_appointments(session, skip, limit)