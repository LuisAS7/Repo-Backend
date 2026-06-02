from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.database import get_db
from app.api.auth_router import router as auth_router

app = FastAPI(title="ValSync API", version="1.0.0")

app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the ValSync API!"}

# Endpoint to test database connection
@app.get("/test-db")
async def test_db_connection(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        return {
            "status": "success",
            "message": "Database connection successful!",
            "database_response": value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")