"""
API Router for Patient Management
Exposes RESTful endpoints for the patients_service to manage patient records,
medical backgrounds, and catalog associations
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.patients_schema import PatientCreate, PatientResponse
from app.services import patients_service

# Create a router instance for patient-related endpoints
router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
)
async def create_patient(patient_in: PatientCreate, session: AsyncSession = Depends(get_db)):
    """
    Registers a new patient with optional nested resources:
    ValCare account, medical background, allergies, and chronic diseases
    """
    return await patients_service.create_patient(session, patient_in)


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a patient by ID",
)
async def get_patient(patient_id: UUID, session: AsyncSession = Depends(get_db)):
    """
    Retrieves a specific patient by their UUID including all nested data
    """
    return await patients_service.get_patient_by_id(session, patient_id)


@router.get(
    "/",
    response_model=list[PatientResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all patients with pagination",
)
async def get_all_patients(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieves a paginated list of all registered patients
    """
    return await patients_service.get_all_patients(session, skip, limit)