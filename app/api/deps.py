"""
Dependency injection utilities for FastAPI route protection and database sessions.

This module provides reusable dependencies that can be injected into any
router to enforce authentication, authorization policies, and database sessions.
"""

from collections.abc import AsyncGenerator
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFoundError
from app.core.security import verify_access_token
from app.db.database import AsyncSessionLocal
from app.models.users import Staff
# 💡 Nota: Si tu archivo de servicios usa "users_service" (en plural), cámbialo aquí abajo.
from app.services.user_service import get_staff_by_id

# ---------------------------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an asynchronous database session for a request.
    Ensures the session is safely closed after the request is processed.
    """
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# OAuth2 token extractor
# ---------------------------------------------------------------------------
# `tokenUrl` points to the login endpoint so that OpenAPI's "Authorize" UI
# knows where to obtain a bearer token. The scheme itself reads the
# `Authorization: Bearer <token>` header automatically.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------------------------------------------------------------------
# Main authentication dependency
# ---------------------------------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Staff:
    """
    FastAPI dependency that validates a JWT bearer token and returns the
    authenticated Staff member.

    Steps performed:
    1. Extract the raw bearer token from the ``Authorization`` header via
       ``OAuth2PasswordBearer`` (raises 401 automatically if header is absent).
    2. Decode and verify the token signature and expiration using the
       application's SECRET_KEY (``verify_access_token``).
    3. Extract the ``sub`` claim (staff UUID) from the decoded payload.
    4. Load the corresponding Staff record from the database.

    Raises:
        HTTPException(401): If the token is missing, malformed, expired,
                            has an invalid signature, or the user no longer
                            exists in the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # --- Step 1: Decode & verify the JWT ---
    try:
        payload: dict = verify_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        # Covers: invalid signature, malformed token, wrong algorithm, etc.
        raise credentials_exception

    # --- Step 2: Extract the subject claim (staff UUID) ---
    sub: str | None = payload.get("sub")
    if sub is None:
        raise credentials_exception

    try:
        staff_id = UUID(sub)
    except ValueError:
        # `sub` exists but is not a valid UUID
        raise credentials_exception

    # --- Step 3: Fetch the user from the database ---
    try:
        staff = await get_staff_by_id(db, staff_id)
    except UserNotFoundError:
        raise credentials_exception

    # --- Step 4: Ensure the account is still active ---
    if not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return staff