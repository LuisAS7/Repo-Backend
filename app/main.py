from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy import text
from app.api.deps import get_db, AsyncSession
from app.api.errors import setup_exception_handlers
from app.api.v1.api_router import api_router
from app.api.auth_router import router as auth_router  # Import JWT authentication router
from app.core.config import settings

app = FastAPI(title="ValSync API", version="1.0.0")

# Initialize the security scheme to enable the global "Authorize" lock in Swagger
security_scheme = HTTPBearer()

# Configure CORS to allow requests from frontend clients (React dev and Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global exception handlers
setup_exception_handlers(app)

# Register system routers
app.include_router(auth_router, prefix="/api/v1")  # Include authentication under v1 prefix
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
        raise HTTPException(
            status_code=500, 
            detail=f"Database connection failed: {str(e)}"
        )
    
@app.get("/api/v1/protected-test", tags=["Testing"])
async def protected_test(token: str = Depends(security_scheme)):
    """Temporary endpoint to verify if the JWT lock works perfectly"""
    return {
        "status": "success",
        "message": "Access granted! Your JWT token is valid.",
        "received_token": token.credentials
    }
