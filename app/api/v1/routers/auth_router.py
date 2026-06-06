"""
Authentication router handling login and token generation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import create_access_token
from app.schemas.users_schema import TokenResponse
from app.services.users_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(credentials: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Authenticates a staff member and returns a JWT access token.
    Raises 401 if credentials are invalid or user is inactive.
    """
    staff = await authenticate_user(db, credentials.username, credentials.password)

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(staff.id), "role": staff.role.value})

    return TokenResponse(access_token=access_token, token_type="bearer")


# SWAGGER ENDPOINT (For the Authorize button - Consumes Form Data)
@router.post("/swagger-login", response_model=TokenResponse, include_in_schema=False)
async def swagger_login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Special endpoint for Swagger UI OAuth2 authorization (Hidden from docs via include_in_schema=False).
    """
    # Swagger sends email inside form_data.username
    staff = await authenticate_user(db, form_data.username, form_data.password)

    if not staff or not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or inactive account",
        )

    access_token = create_access_token(data={"sub": str(staff.id), "role": staff.role.value})
    return TokenResponse(access_token=access_token)
