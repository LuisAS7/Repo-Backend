"""
API Router for ValCare Patient Portal
Exposes public endpoints for registration/login and secured endpoints
for patients to manage their profiles, medical history, and appointments
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_patient, get_db
from app.core.security import create_access_token
from app.models.appointments import AppointmentOrigin, AppointmentStatus
from app.models.patients import Patient
from app.schemas.appointments_schema import AppointmentCreate, AppointmentResponse
from app.schemas.valcare_schema import ValcareAppointmentBooking, ValcareProfileResponse, ValcareRegisterRequest
from app.services import appointments_service, valcare_service

router = APIRouter(prefix="/valcare", tags=["ValCare Portal (Patients)"])

# ---------------------------------------------------------------------------
# PUBLIC ENDPOINTS
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=ValcareProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient account from the portal",
)
async def register_patient(patient_in: ValcareRegisterRequest, session: AsyncSession = Depends(get_db)):
    """
    Allows a new user to self-register as a patient in the system
    This creates both the demographic profile and the security account credentials
    """
    return await valcare_service.register_patient_from_valcare(session, patient_in)


@router.post("/login", status_code=status.HTTP_200_OK, summary="Authenticate a patient and return an access token")
async def valcare_login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)):
    """
    Authenticates a patient using their email (username) and password
    Returns a specialized JWT token embedded with the 'PATIENT' role
    """
    # Validate the credentials against the service and obtain the patient ID
    patient_id = await valcare_service.authenticate_patient(
        session, email=form_data.username, password=form_data.password
    )

    # Issue the token by strictly injecting the PATIENT role
    access_token = create_access_token(data={"sub": str(patient_id), "role": "PATIENT"})

    return {"access_token": access_token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# PROTECTED ENDPOINTS
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=ValcareProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current logged-in patient profile",
)
async def get_patient_profile(current_patient: Patient = Depends(get_current_patient)):
    """
    Retrieves the complete profile of the currently authenticated patient,
    including an overview of their account and baseline medical background
    """
    return current_patient


@router.get(
    "/my-appointments", status_code=status.HTTP_200_OK, summary="Get appointment history for the logged-in patient"
)
async def get_patient_appointments(
    session: AsyncSession = Depends(get_db), current_patient: Patient = Depends(get_current_patient)
):
    """
    Retrieves a list of all medical appointments associated with the authenticated patient,
    ordered chronologically to show their clinical history
    """
    return await valcare_service.get_appointments_by_patient(session, current_patient.id)


@router.get("/specialties", status_code=status.HTTP_200_OK, summary="List specialties available for patient booking")
async def get_patient_specialties(
    session: AsyncSession = Depends(get_db),
    current_patient: Patient = Depends(get_current_patient),
):
    """Provides the list of medical specialties to the patient portal."""
    return await valcare_service.get_available_specialties(session)


@router.get("/doctors", status_code=status.HTTP_200_OK, summary="List doctors available for patient booking")
async def get_patient_doctors(
    specialty_id: UUID | None = None,
    session: AsyncSession = Depends(get_db),
    current_patient: Patient = Depends(get_current_patient),
):
    """Provides the list of active doctors, optionally filtered by specialty."""
    return await valcare_service.get_available_doctors(session, specialty_id)


@router.post(
    "/book-appointment",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a new medical appointment",
)
async def book_appointment(
    booking_in: ValcareAppointmentBooking,
    session: AsyncSession = Depends(get_db),
    current_patient: Patient = Depends(get_current_patient),
):
    """
    Allows a patient to schedule an appointment.
    Automatically links the appointment to the authenticated patient
    and sets the origin to VALCARE
    """
    # Inject the patient ID from token
    appointment_in = AppointmentCreate(
        patient_id=current_patient.id,
        doctor_id=booking_in.doctor_id,
        scheduled_date=booking_in.scheduled_date,
        scheduled_time=booking_in.scheduled_time,
        reason=booking_in.reason,
        status=AppointmentStatus.SCHEDULED,
        origin=AppointmentOrigin.VALCARE,
    )

    return await appointments_service.create_appointment(session, appointment_in)
