"""
API Router for read-only system catalogs.
Used by the frontend to populate dropdown menus and selection lists.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.patients_schema import AllergyResponse, ChronicDiseaseResponse
from app.schemas.users_schema import SpecialtyResponse
from app.schemas.appointments_schema import DiagnosisCatalogResponse
from app.services import catalogs_service

router = APIRouter(prefix="/catalogs", tags=["Catalogs & References"])

@router.get("/allergies", response_model=list[AllergyResponse], status_code=status.HTTP_200_OK)
async def get_allergies(session: AsyncSession = Depends(get_db)):
    return await catalogs_service.get_all_allergies(session)

@router.get("/chronic-diseases", response_model=list[ChronicDiseaseResponse], status_code=status.HTTP_200_OK)
async def get_chronic_diseases(session: AsyncSession = Depends(get_db)):
    return await catalogs_service.get_all_chronic_diseases(session)

@router.get("/specialties", response_model=list[SpecialtyResponse], status_code=status.HTTP_200_OK)
async def get_specialties(session: AsyncSession = Depends(get_db)):
    return await catalogs_service.get_all_specialties(session)

@router.get("/diagnoses", response_model=list[DiagnosisCatalogResponse], status_code=status.HTTP_200_OK)
async def get_diagnoses(session: AsyncSession = Depends(get_db)):
    return await catalogs_service.get_all_diagnoses(session)