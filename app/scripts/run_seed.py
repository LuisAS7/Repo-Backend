"""
Master script to orchestrate database seeding
Run with `--dummy` flag to also insert fake data for development
Usage:
    python -m app.scripts.run_seed          (Only inserts real catalogs)
    python -m app.scripts.run_seed --dummy  (Inserts catalogs + fake patients/staff)
"""

import asyncio
import logging
import sys

# Importamos las funciones de nuestros sub-módulos (los crearemos en el siguiente paso)
from app.scripts.seeders.core_seeder import seed_catalogs
from app.scripts.seeders.dummy_seeder import seed_dummy_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting database seeding process...")

    # Always seed the core catalogs first
    await seed_catalogs()

    # Check for the --dummy flag to decide whether to insert fake data
    if "--dummy" in sys.argv:
        logger.warning("Dummy flag detected! Inserting fake development data...")
        await seed_dummy_data()
    else:
        logger.info("Skipping dummy data. Run with '--dummy' to include fake data")

    logger.info("Seeding process finished successfully")


if __name__ == "__main__":
    asyncio.run(main())
