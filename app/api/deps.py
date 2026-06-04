"""
API dependencies for FastAPI endpoints
Handles database sessions and future security/authentication injections
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an asynchronous database session for a request
    Ensures the session is safely closed after the request is processed
    """
    async with AsyncSessionLocal() as session:
        yield session
