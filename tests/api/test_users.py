from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.users import Staff, StaffRole

# Mark the entire module to use asyncio for pytest
pytestmark = pytest.mark.asyncio


# TEST CASES FOR STAFF MANAGEMENT
async def test_admin_can_create_doctor(client: AsyncClient, db_session: AsyncSession):
    """Verifies that an Admin can create a new Doctor with their nested medical profile."""
    # Create a test Admin user in the database
    admin_user = Staff(
        id=uuid4(),
        first_name="Jefe",
        last_name="Admin",
        email="jefe@valsync.com",
        password_hash=hash_password("Pass123"),
        role=StaffRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin_user)
    await db_session.commit()

    token = create_access_token(data={"sub": str(admin_user.id), "role": admin_user.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    # Payload for creating a new Doctor with nested doctor_profile
    payload = {
        "first_name": "Gregory",
        "last_name": "House",
        "email": "house@valsync.com",
        "password": "SecurePassword123!",
        "role": "DOCTOR",
        "doctor_profile": {
            "specialty_id": str(
                uuid4()
            ),  # In a real test, this should correspond to an existing SpecialtyCatalog ID in the database
            "medical_license": "CMP-123456",
        },
    }

    # Send a POST request to create the new Doctor
    response = await client.post("/api/v1/staff/", json=payload, headers=headers)

    # ⚠️ Nota: Si tu lógica valida que la specialty_id exista en la BD, este test dará 400 o 404.
    # En ese caso, asegúrate de insertar un SpecialtyCatalog en el db_session antes.
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role"] == "DOCTOR"
    assert response.json()["doctor_profile"]["medical_license"] == "CMP-123456"


# TEST CASES FOR RBAC (ROLE-BASED ACCESS CONTROL)
async def test_nurse_cannot_create_staff(client: AsyncClient, db_session: AsyncSession):
    """Verifies that a Nurse cannot create new staff members and receives a 403 Forbidden response."""
    # Create a test Nurse user in the database
    nurse_user = Staff(
        id=uuid4(),
        first_name="Enfermera",
        last_name="Joy",
        email="nurse@valsync.com",
        password_hash=hash_password("Pass123"),
        role=StaffRole.NURSE,
        is_active=True,
    )
    db_session.add(nurse_user)
    await db_session.commit()

    # Generate a valid JWT token for the nurse user to authenticate the request
    token = create_access_token(data={"sub": str(nurse_user.id), "role": nurse_user.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@valsync.com",
        "password": "Pass123!",
        "role": "RECEPTIONIST",
    }

    # Assert that the nurse cannot create a new staff member and receives a 403 Forbidden response
    response = await client.post("/api/v1/staff/", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
