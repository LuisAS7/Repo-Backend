from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.errors import setup_exception_handlers

app = FastAPI(title="ValSync API", version="1.0.0")

setup_exception_handlers(app)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "ValSync API", "version": "1.0.0"}


@app.get("/health/db")
async def database_health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))

    return {"status": "healthy", "database": "connected"}
