from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, oauth2_scheme
from app.api.errors import setup_exception_handlers
from app.api.v1.api_router import api_router
from app.core.config import settings

app = FastAPI(title="ValSync API", version="1.0.0")

# Configure CORS to allow requests from frontend clients (React dev and Vercel)
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Initialize global exception handlers
setup_exception_handlers(app)

# Register system routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to the ValSync API!"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Verify the overall API health status"""
    return {"status": "healthy", "service": "ValSync API", "version": "1.0.0"}


@app.get("/health/db", tags=["Health"])
async def database_health(db: AsyncSession = Depends(get_db)):
    """Verify real-time connectivity with PostgreSQL"""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}") from e


@app.get("/api/v1/protected-test", tags=["Testing"])
async def protected_test(token: str = Depends(oauth2_scheme)):
    """Temporary endpoint to verify if the JWT lock works perfectly"""
    return {"status": "success", "message": "Access granted! Your JWT token is valid.", "received_token": token}
