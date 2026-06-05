from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

__all__ = ["AsyncSessionLocal", "engine"]

# Create the async engine
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True, connect_args={"statement_cache_size": 0})

# Create the async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
