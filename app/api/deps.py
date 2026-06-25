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
from app.models.users import Staff, StaffRole
from app.services.users_service import get_staff_by_id


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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


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

    # --- Decode & verify the JWT ---
    try:
        payload: dict = verify_access_token(token)
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
    except jwt.InvalidTokenError as err:
        # Covers invalid signature, malformed token, wrong algorithm, etc.
        raise credentials_exception from err

    # --- Extract the subject claim (staff UUID) ---
    sub: str | None = payload.get("sub")
    if sub is None:
        raise credentials_exception

    try:
        staff_id = UUID(sub)
    except ValueError as err:
        # `sub` exists but is not a valid UUID
        raise credentials_exception from err

    # --- Fetch the user from the database ---
    try:
        staff = await get_staff_by_id(db, staff_id)
    except UserNotFoundError as err:
        raise credentials_exception from err

    # --- Ensure the account is still active ---
    if not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return staff


# ---------------------------------------------------------------------------
# Role-Based Access Control (RBAC) Dependency
# ---------------------------------------------------------------------------


class RoleChecker:
    """
    FastAPI dependency that enforces Role-Based Access Control (RBAC).

    Validates if the currently authenticated user possesses one of the allowed
    roles required to interact with the route.
    """

    def __init__(self, allowed_roles: list[StaffRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Staff = Depends(get_current_user)) -> Staff:
        # Checks if the logged-in user's role is in the allowed list
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required permissions to perform this action",
            )

        return current_user
