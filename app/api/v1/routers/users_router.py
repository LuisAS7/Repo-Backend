"""
API Router for Staff and Doctor Profiles
Exposes RESTful endpoints for the users_service to manage staff and doctor profiles
Includes endpoints for creating, retrieving, and updating staff members
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker, get_current_user, get_db
from app.models.users import Staff, StaffRole
from app.schemas.users_schema import StaffCreate, StaffResponse, StaffUpdate
from app.services import users_service

# Create a router instance for staff-related endpoints
router = APIRouter(prefix="/staff", tags=["Staff & Doctors"])


@router.post(
    "/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED, summary="Create a new staff member"
)
async def create_staff(
    staff_in: StaffCreate,
    session: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(RoleChecker([StaffRole.ADMIN])),
):
    """
    Registers a new staff member
    If the role is DOCTOR, a nested doctor_profile is required
    """
    return await users_service.create_staff(session, staff_in)


@router.get(
    "/me", response_model=StaffResponse, status_code=status.HTTP_200_OK, summary="Get current logged-in staff profile"
)
async def get_me(current_user: Staff = Depends(get_current_user)):
    """
    Retrieves the profile of the currently authenticated staff member.
    The get_current_user dependency already validates the JWT and fetches the user from the database.
    """
    return current_user


@router.get(
    "/{staff_id}", response_model=StaffResponse, status_code=status.HTTP_200_OK, summary="Get a staff member by ID"
)
async def get_staff(
    staff_id: UUID, session: AsyncSession = Depends(get_db), current_user: Staff = Depends(get_current_user)
):
    """
    Retrieves a specific staff member by their UUID
    """
    return await users_service.get_staff_by_id(session, staff_id)


@router.get(
    "/",
    response_model=list[StaffResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all active staff members with pagination",
)
async def get_all_active_staff(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    session: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """
    Retrieves a paginated list of all active staff members
    """
    return await users_service.get_all_active_staff(session, skip, limit)


@router.patch(
    "/{staff_id}",
    response_model=StaffResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a staff member's information",
)
async def update_staff(
    staff_id: UUID,
    staff_update: StaffUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(RoleChecker([StaffRole.ADMIN])),
):
    """
    Partially updates a staff member's information
    """
    return await users_service.update_staff(session, staff_id, staff_update)
