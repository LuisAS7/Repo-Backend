from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.main import app
from app.models.base import Base

# Configure an in-memory SQLite database for testing purposes
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncSessionTesting = async_sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    """
    Creates the database schema in an in-memory SQLite database before any tests run
    """
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Session fixture that provides a fresh database session for each test,
    ensuring isolation and rollback after each test.
    """
    async with AsyncSessionTesting() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Inyects a test client that uses the in-memory database session for API requests.
    Overrides the get_db dependency to ensure that all database interactions during tests
    """

    async def _override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()

    # Override the get_db dependency in the FastAPI app to use the test database session
    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clear the dependency overrides after the test to avoid side effects on other tests
    app.dependency_overrides.clear()
