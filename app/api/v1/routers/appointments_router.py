"""
API Router for Clinical Flow Management
Exposes RESTful endpoints for the appointments_service to manage
appointments scheduling and retrieval
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker, get_current_user, get_db
from app.models.users import Staff, StaffRole
from app.schemas.appointments_schema import AppointmentCreate, AppointmentResponse, TriageCreate, TriageResponse, ConsultationCreate, ConsultationResponse 
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

# ---------------------------------------------------------------------------
# NEW: CLINICAL LIFECYCLE ENDPOINTS
# ---------------------------------------------------------------------------

@router.patch(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel an appointment",
)
async def cancel_appointment(
    appointment_id: UUID,
    cancellation_reason: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(RoleChecker([StaffRole.ADMIN, StaffRole.RECEPTIONIST, StaffRole.DOCTOR]))
):
    """Cancels an appointment logistically and saves the reason."""
    return await appointments_service.cancel_appointment(session, appointment_id, cancellation_reason)


@router.post(
    "/{appointment_id}/triage",
    response_model=TriageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register patient vital signs (Triage)",
)
async def create_triage(
    appointment_id: UUID,
    payload: TriageCreate,
    session: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(RoleChecker([StaffRole.NURSE, StaffRole.DOCTOR]))
):
    """Records vital signs and transitions the appointment to WAITING status."""
    return await appointments_service.create_triage(
        session=session, 
        appointment_id=appointment_id, 
        triage_in=payload, 
        nurse_id=current_user.id
    )


@router.post(
    "/{appointment_id}/consultation",
    response_model=ConsultationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Conclude a clinical encounter",
)
async def create_consultation(
    appointment_id: UUID,
    payload: ConsultationCreate,
    session: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(RoleChecker([StaffRole.DOCTOR]))
):
    """Saves evolution notes, binds diagnoses, and issues prescriptions."""
    return await appointments_service.create_consultation(
        session=session,
        appointment_id=appointment_id,
        consultation_in=payload,
        doctor_id=current_user.id
    )