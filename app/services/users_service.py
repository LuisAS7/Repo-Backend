"""
Business logic and CRUD operations for Staff and Doctor Profiles
Handles database transactions, password hashing, and business rules validation
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import EmailAlreadyExistsError, InvalidDoctorProfileError, UserNotFoundError
from app.core.security import hash_password
from app.models.users import DoctorProfile, Staff, StaffRole
from app.schemas.users_schema import StaffCreate, StaffUpdate


async def get_staff_by_email(session: AsyncSession, email: str) -> Staff | None:
    """Retrieves a staff member by email using scalar_one_or_none for strictness"""
    stmt = select(Staff).where(Staff.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_staff_by_id(session: AsyncSession, staff_id: UUID) -> Staff:
    """Retrieves a staff member eagerly loading their profile"""
    stmt = select(Staff).options(selectinload(Staff.doctor_profile)).where(Staff.id == staff_id)
    result = await session.execute(stmt)
    staff = result.scalar_one_or_none()

    if not staff:
        raise UserNotFoundError(identifier=str(staff_id))

    return staff


async def create_staff(session: AsyncSession, staff_create: StaffCreate) -> Staff:
    """
    Creates a new staff member ensuring role consistency and transaction safety
    """
    # Validation: Role vs Doctor Profile consistency
    if staff_create.role != StaffRole.DOCTOR and staff_create.doctor_profile:
        raise InvalidDoctorProfileError("Only staff members with the DOCTOR role can have a doctor profile")

    if staff_create.role == StaffRole.DOCTOR and not staff_create.doctor_profile:
        raise InvalidDoctorProfileError("A doctor profile is required when creating a DOCTOR staff member")

    # Validation: Email Uniqueness
    existing_user = await get_staff_by_email(session, staff_create.email)
    if existing_user:
        raise EmailAlreadyExistsError(email=staff_create.email)

    # Data Preparation
    staff_data = staff_create.model_dump(exclude={"doctor_profile", "password"})
    staff_data["password_hash"] = hash_password(staff_create.password)
    new_staff = Staff(**staff_data)

    # Database Transaction: Add staff and optionally doctor profile, ensuring rollback on failure
    try:
        session.add(new_staff)
        await session.flush()  # Generates new_staff.id securely

        if staff_create.doctor_profile:
            profile_data = staff_create.doctor_profile.model_dump()
            session.add(DoctorProfile(staff_id=new_staff.id, **profile_data))

        new_staff_id = new_staff.id  # Capture the generated ID for later retrieval

        await session.commit()  # Safely commit the transaction if everything is fine
    except Exception:
        await session.rollback()  # If any error occurs, rollback to maintain data integrity
        raise

    return await get_staff_by_id(session, new_staff_id)


async def get_all_active_staff(session: AsyncSession, skip: int = 0, limit: int = 50) -> list[Staff]:
    """
    Retrieves a paginated list of active staff members, sorted by newest first
    Includes defensive pagination limits to prevent performance issues
    """
    safe_limit = min(limit, 100)  # Prevents memory overload attacks

    stmt = (
        select(Staff)
        .options(selectinload(Staff.doctor_profile))
        .where(Staff.is_active.is_(True))
        .order_by(Staff.created_at.desc())  # Stable pagination
        .offset(skip)
        .limit(safe_limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_staff(session: AsyncSession, staff_id: UUID, staff_update: StaffUpdate) -> Staff:
    """Partially updates a staff member's information"""
    staff = await get_staff_by_id(session, staff_id)

    # Only include fields that were actually provided in the update request
    update_data = staff_update.model_dump(exclude_unset=True)

    # Validation: If email is being updated, ensure it's not already taken by another user
    if "email" in update_data and update_data["email"] != staff.email:
        if await get_staff_by_email(session, update_data["email"]):
            raise EmailAlreadyExistsError(email=update_data["email"])

    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))

    # Apply updates and commit within a transaction block to ensure data integrity
    try:
        for key, value in update_data.items():
            setattr(staff, key, value)
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return await get_staff_by_id(session, staff_id)
