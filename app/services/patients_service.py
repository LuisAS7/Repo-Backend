"""
Business logic and CRUD operations for Patients
Handles demographic data, nested ValCare account creation, medical background, and catalog associations
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BaseBusinessException,
    DocumentNumberAlreadyExistsError,
    EmailAlreadyExistsError,
    InvalidCatalogReferenceError,
    PatientNotFoundError,
)
from app.core.security import hash_password
from app.models.patients import Allergy, ChronicDisease, MedicalBackground, Patient, PatientAccount
from app.schemas.patients_schema import PatientCreate


async def get_patient_by_document(session: AsyncSession, document_number: str) -> Patient | None:
    """Retrieves a patient by their unique document number"""
    stmt = select(Patient).where(Patient.document_number == document_number)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_patient_by_id(session: AsyncSession, patient_id: UUID) -> Patient:
    """
    Retrieves a patient by ID, eagerly loading all related nested data
    Raises PatientNotFoundError if not found
    """
    stmt = (
        select(Patient)
        .options(
            selectinload(Patient.account),
            selectinload(Patient.medical_background),
            selectinload(Patient.allergies),
            selectinload(Patient.chronic_diseases),
        )
        .where(Patient.id == patient_id)
    )
    result = await session.execute(stmt)
    patient = result.scalar_one_or_none()

    if not patient:
        raise PatientNotFoundError(identifier=str(patient_id))

    return patient


async def create_patient(session: AsyncSession, patient_create: PatientCreate) -> Patient:
    """
    Creates a new patient along with their optional nested records (Account, Background)
    Uses a strict transaction block to guarantee database integrity
    """
    # Validate Business Rules
    existing_patient = await get_patient_by_document(session, patient_create.document_number)
    if existing_patient:
        raise DocumentNumberAlreadyExistsError(document=patient_create.document_number)

    # If creating a ValCare account, ensure email is unique globally in PatientAccount
    if patient_create.account:
        stmt = select(PatientAccount).where(PatientAccount.email == patient_create.account.email)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise EmailAlreadyExistsError(email=patient_create.account.email)

    # Extract core data
    patient_data = patient_create.model_dump(
        exclude={"account", "medical_background", "allergy_ids", "chronic_disease_ids"}
    )

    # Use a transaction block to ensure all-or-nothing behavior
    try:
        # Handle Many-to-Many Catalogs (Allergies)
        found_allergies = []
        if patient_create.allergy_ids:
            stmt_allergies = select(Allergy).where(Allergy.id.in_(patient_create.allergy_ids))
            allergies_result = await session.execute(stmt_allergies)
            found_allergies = list(allergies_result.scalars().all())

            if len(found_allergies) != len(set(patient_create.allergy_ids)):
                raise InvalidCatalogReferenceError("Allergies")

        # Handle Many-to-Many Catalogs (Chronic Diseases)
        found_chronic_diseases = []
        if patient_create.chronic_disease_ids:
            stmt_diseases = select(ChronicDisease).where(ChronicDisease.id.in_(patient_create.chronic_disease_ids))
            diseases_result = await session.execute(stmt_diseases)
            found_chronic_diseases = list(diseases_result.scalars().all())

            if len(found_chronic_diseases) != len(set(patient_create.chronic_disease_ids)):
                raise InvalidCatalogReferenceError("Chronic Diseases")

        new_patient = Patient(**patient_data, allergies=found_allergies, chronic_diseases=found_chronic_diseases)

        session.add(new_patient)
        await session.flush()  # Flush to generate new_patient.id for related records

        # Handle ValCare Account Creation
        if patient_create.account:
            account_data = patient_create.account.model_dump(exclude={"password"})
            account_data["password_hash"] = hash_password(patient_create.account.password)
            new_account = PatientAccount(patient_id=new_patient.id, **account_data)
            session.add(new_account)

        # Handle Medical Background Creation
        if patient_create.medical_background:
            background_data = patient_create.medical_background.model_dump()
            new_background = MedicalBackground(patient_id=new_patient.id, **background_data)
            session.add(new_background)

        await session.commit()  # Commit the transaction if everything is fine
    except Exception as e:
        await session.rollback()  # Rollback on any error to maintain data integrity
        if isinstance(e, BaseBusinessException):
            raise
        raise

    # Fetch the fully loaded object using the dedicated query
    return await get_patient_by_id(session, new_patient.id)


async def get_all_patients(session: AsyncSession, skip: int = 0, limit: int = 50) -> list[Patient]:
    """
    Retrieves a paginated list of patients, sorted by creation date
    Protects against massive queries using a hard limit
    """
    # Cap the limit to prevent performance degradation
    safe_limit = min(limit, 100)

    stmt = (
        select(Patient)
        .options(
            selectinload(Patient.account),
            selectinload(Patient.medical_background),
            selectinload(Patient.allergies),
            selectinload(Patient.chronic_diseases),
        )
        .order_by(Patient.created_at.desc())
        .offset(skip)
        .limit(safe_limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
