"""
Core seeder for essential system catalogs
Inserts real, production-ready data like Specialties, Allergies, and Chronic Diseases
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.patients import Allergy, ChronicDisease
from app.models.users import Specialty

logger = logging.getLogger(__name__)

# Base list of medical specialties
INITIAL_SPECIALTIES = [
    {"name": "Cardiology", "description": "Heart and blood vessel diseases"},
    {"name": "Pediatrics", "description": "Medical care of infants, children, and adolescents"},
    {"name": "Neurology", "description": "Disorders of the nervous system"},
    {"name": "General Practice", "description": "Primary care and general medicine"},
    {"name": "Dermatology", "description": "Skin, hair, and nail conditions"},
    {"name": "Psychiatry", "description": "Mental health and behavioral disorders"},
    {"name": "Orthopedics", "description": "Musculoskeletal system issues"},
    {"name": "Gynecology", "description": "Women's reproductive health"},
]

INITIAL_ALLERGIES = [
    {"name": "Penicillin"},
    {"name": "Peanuts"},
    {"name": "Latex"},
    {"name": "Pollen"},
    {"name": "Dust Mites"},
]

INITIAL_DISEASES = [
    {"name": "Type 2 Diabetes"},
    {"name": "Hypertension"},
    {"name": "Asthma"},
    {"name": "Hypothyroidism"},
]


async def seed_allergies(session: AsyncSession) -> None:
    """
    Seeds the allergies table if it's currently empty
    """
    # Verify if allergies already exist to avoid duplicates on multiple runs
    result = await session.execute(select(Allergy).limit(1))
    existing = result.scalar_one_or_none()

    if existing:
        logger.info("✅ Allergies already seeded. Skipping...")
        return

    logger.info("⏳ Seeding Allergies...")

    for allergy_data in INITIAL_ALLERGIES:
        allergy = Allergy(**allergy_data)
        session.add(allergy)

    logger.info(f"✅ Queued {len(INITIAL_ALLERGIES)} allergies for insertion")


async def seed_diseases(session: AsyncSession) -> None:
    """
    Seeds the chronic diseases table if it's currently empty
    """
    # Verify if chronic diseases already exist to avoid duplicates on multiple runs
    result = await session.execute(select(ChronicDisease).limit(1))
    existing = result.scalar_one_or_none()

    if existing:
        logger.info("✅ Chronic diseases already seeded. Skipping...")
        return

    logger.info("⏳ Seeding Chronic Diseases...")
    for disease_data in INITIAL_DISEASES:
        chronic_disease = ChronicDisease(**disease_data)
        session.add(chronic_disease)

    logger.info(f"✅ Queued {len(INITIAL_DISEASES)} chronic diseases for insertion")


async def seed_specialties(session: AsyncSession) -> None:
    """Seeds the specialties table if it's currently empty"""
    # Verify if specialties already exist to avoid duplicates on multiple runs
    result = await session.execute(select(Specialty).limit(1))
    existing = result.scalar_one_or_none()

    if existing:
        logger.info("✅ Specialties already seeded. Skipping...")
        return

    logger.info("⏳ Seeding Specialties...")
    for spec_data in INITIAL_SPECIALTIES:
        specialty = Specialty(**spec_data)
        session.add(specialty)

    logger.info(f"✅ Queued {len(INITIAL_SPECIALTIES)} specialties for insertion")


async def seed_catalogs() -> None:
    """Orchestrates the seeding of all core production catalogs"""
    async with AsyncSessionLocal() as session:
        try:
            # Execute all catalog seeders in sequence (currently only specialties, but we can add more)
            await seed_specialties(session)
            await seed_allergies(session)
            await seed_diseases(session)

            # Only commit after all seeders have run successfully to ensure atomicity
            await session.commit()

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error during core catalog seeding: {str(e)}")
            raise
