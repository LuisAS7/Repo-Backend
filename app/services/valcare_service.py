import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.appointments import Appointment
from app.models.patients import Patient, PatientAccount
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


async def get_appointments_by_patient(session: AsyncSession, patient_id: UUID) -> list[Appointment]:
    """
    Fetches all appointments for a specific patient from the database,
    sorting them from newest to oldest
    """
    stmt = (
        select(Appointment)
        .where(Appointment.patient_id == patient_id)
        .order_by(Appointment.scheduled_date.desc(), Appointment.scheduled_time.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
