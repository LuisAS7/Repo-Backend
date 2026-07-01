import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, verify_password
from app.models.appointments import Appointment
from app.models.patients import Patient, PatientAccount
from app.models.users import DoctorProfile, Specialty, Staff, StaffRole
from app.schemas.valcare_schema import ValcareRegisterRequest

logger = logging.getLogger(__name__)


async def register_patient_from_valcare(session: AsyncSession, patient_in: ValcareRegisterRequest) -> Patient:
    """
    Registers a new patient directly from the ValCare public portal
    Requires the 'account' payload to create login credentials
    """

    # Verify if the DNI already exists
    stmt = select(Patient).where(Patient.document_number == patient_in.document_number)
    existing_patient = (await session.execute(stmt)).scalar_one_or_none()
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A patient with this document number is already registered"
        )

    # Verify if the email alreaady exists
    stmt_email = select(PatientAccount).where(PatientAccount.email == patient_in.email)
    existing_email = (await session.execute(stmt_email)).scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email address is already in use")

    try:
        # Create profile
        new_patient = Patient(
            document_number=patient_in.document_number,
            first_name=patient_in.first_name,
            last_name=patient_in.last_name,
            birth_date=patient_in.birth_date,
            gender=patient_in.gender,
            email=patient_in.email,
        )
        session.add(new_patient)
        await session.flush()  # Flush for obtain the new_patient.id

        # Create credentials
        new_account = PatientAccount(
            patient_id=new_patient.id,
            email=patient_in.email,
            password_hash=hash_password(patient_in.password),
            is_email_verified=False,
        )
        session.add(new_account)

        await session.commit()
        await session.refresh(new_patient)
        logger.info(f"New ValCare patient registered: {new_patient.id}")

        return new_patient

    except Exception as e:
        await session.rollback()
        logger.error(f"Error registering ValCare patient: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while creating the account"
        ) from e


async def authenticate_patient(session: AsyncSession, email: str, password: str) -> UUID:
    """
    Verifies a patient's credentials. Returns the Patient ID if valid
    """
    # Search the account for email
    stmt = select(PatientAccount).where(PatientAccount.email == email)
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()

    # Verify the password using the security function
    if not account or not verify_password(password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify that the main profile remains active
    patient_stmt = select(Patient).where(Patient.id == account.patient_id)
    patient = (await session.execute(patient_stmt)).scalar_one_or_none()

    if not patient or not patient.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This patient account has been deactivated")

    return patient.id


async def get_available_specialties(session: AsyncSession) -> list[dict]:
    """Returns the catalog of medical specialties for the portal."""
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
    """Returns active doctors, optionally filtered by specialty."""
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
            "first_name": doctor.first_name,
            "last_name": doctor.last_name,
            "full_name": f"{doctor.first_name} {doctor.last_name}".strip(),
            "specialty_id": str(doctor.doctor_profile.specialty_id) if doctor.doctor_profile else None,
            "specialty_name": (
                doctor.doctor_profile.specialty.name
                if doctor.doctor_profile and doctor.doctor_profile.specialty
                else None
            ),
            "medical_license": doctor.doctor_profile.medical_license if doctor.doctor_profile else None,
        }
        for doctor in doctors
    ]


async def get_appointments_by_patient(session: AsyncSession, patient_id: UUID) -> list[dict]:
    """
    Fetches all appointments for a specific patient from the database,
    sorting them from newest to oldest and shaping the payload for the portal.
    """
    stmt = (
        select(Appointment)
        .options(
            selectinload(Appointment.doctor).selectinload(Staff.doctor_profile).selectinload(DoctorProfile.specialty)
        )
        .where(Appointment.patient_id == patient_id)
        .order_by(Appointment.scheduled_date.desc(), Appointment.scheduled_time.desc())
    )
    result = await session.execute(stmt)
    appointments = result.scalars().all()

    status_map = {
        "SCHEDULED": "pendiente",
        "WAITING": "pendiente",
        "READY": "pendiente",
        "COMPLETED": "confirmada",
        "CANCELED": "cancelada",
    }

    return [
        {
            "id": str(appointment.id),
            "scheduled_date": appointment.scheduled_date.isoformat(),
            "scheduled_time": appointment.scheduled_time.isoformat(),
            "reason": appointment.reason,
            "status": status_map.get(appointment.status.value, appointment.status.value.lower()),
            "doctor_id": str(appointment.doctor_id) if appointment.doctor_id else None,
            "doctor": (
                f"{appointment.doctor.first_name} {appointment.doctor.last_name}".strip()
                if appointment.doctor
                else "Médico por asignar"
            ),
            "specialty": (
                appointment.doctor.doctor_profile.specialty.name
                if appointment.doctor and appointment.doctor.doctor_profile and appointment.doctor.doctor_profile.specialty
                else None
            ),
            "created_at": appointment.created_at.isoformat() if appointment.created_at else None,
        }
        for appointment in appointments
    ]
