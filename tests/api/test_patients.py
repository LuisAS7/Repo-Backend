from datetime import date
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.patients import Patient
from app.models.users import Staff, StaffRole

# Mark the entire module to use asyncio for pytest
pytestmark = pytest.mark.asyncio


# TEST CASES FOR PATIENT MANAGEMENT
async def test_protected_route_requires_authentication(client: AsyncClient):
    """
    Verifies that the global route protection works and blocks requests with a 401
    if the Authorization header is not provided.
    """
    # Try to access a protected endpoint without an Authorization header
    target_patient_id = "c624dde1-5a1a-45d1-ae76-fbc7cef7d889"

    response = await client.patch(f"/api/v1/patients/{target_patient_id}/status", json={"is_active": False})

    # 401 Unauthorized is expected because no JWT token was provided
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# TEST CASES FOR SOFT DELETE PATIENT
async def test_soft_delete_patient_success_as_admin(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies that an authenticated staff member with ADMIN role can
    successfully toggle a patient's active status.
    """
    # Create a test Admin user and a test Patient in the database
    admin_user = Staff(
        id=uuid4(),
        first_name="Admin",
        last_name="Valsync",
        email="admin_test@valsync.com",
        password_hash=hash_password("AdminSecurePassword123"),
        role=StaffRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin_user)

    test_patient = Patient(
        id=uuid4(),
        document_number="77777777",
        first_name="Carlos",
        last_name="Mendoza",
        birth_date=date(1995, 5, 15),
        gender="MALE",
        is_active=True,
    )
    db_session.add(test_patient)
    await db_session.commit()

    # Generate a valid JWT token for the admin user to authenticate the request
    token = create_access_token(data={"sub": str(admin_user.id), "role": admin_user.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    # Execute the PATCH request to toggle the patient's active status
    payload = {"is_active": False}
    response = await client.patch(f"/api/v1/patients/{test_patient.id}/status", json=payload, headers=headers)

    # Validate the response to ensure the soft delete was successful
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_active"] is False
    assert response.json()["id"] == str(test_patient.id)
