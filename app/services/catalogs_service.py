"""
Read-only services for system catalogs (Allergies, Diseases, Specialties, Diagnoses).
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patients import Allergy, ChronicDisease
from app.models.users import Specialty
from app.models.appointments import DiagnosisCatalog

async def get_all_allergies(session: AsyncSession) -> list[Allergy]:    
    """Fetches all allergies from the database, ordered by name."""
    result = await session.execute(select(Allergy).order_by(Allergy.name))
    return list(result.scalars().all())

async def get_all_chronic_diseases(session: AsyncSession) -> list[ChronicDisease]:
    """Fetches all chronic diseases from the database, ordered by name."""
    result = await session.execute(select(ChronicDisease).order_by(ChronicDisease.name))
    return list(result.scalars().all())

async def get_all_specialties(session: AsyncSession) -> list[Specialty]:
    """Fetches all specialties from the database, ordered by name."""
    result = await session.execute(select(Specialty).order_by(Specialty.name))
    return list(result.scalars().all())

async def get_all_diagnoses(session: AsyncSession) -> list[DiagnosisCatalog]:
    """Fetches all diagnoses from the database, ordered by code."""
    result = await session.execute(select(DiagnosisCatalog).order_by(DiagnosisCatalog.code))
    return list(result.scalars().all())