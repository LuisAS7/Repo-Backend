import pytest
from fastapi import status
from httpx import AsyncClient

# Mark the entire module to use asyncio for pytest
pytestmark = pytest.mark.asyncio


# TEST CASES FOR AUTHENTICATION
async def test_login_failed_with_wrong_credentials(client: AsyncClient):
    """
    Verifies that the login endpoint correctly rejects
    invalid credentials and returns a 401 Unauthorized response
    """
    # Swagger send as form-data, so we mimic that behavior in the test
    login_data = {"username": "no_existo@valsync.com", "password": "PasswordInvalido123"}

    response = await client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid email or password / User account is inactive"


# TEST CASES FOR JWT TOKEN VALIDATION
async def test_access_denied_with_invalid_token(client: AsyncClient):
    """
    Verifies that the system rejects any request that includes an invalid JWT token
    that is malformed, invented, or signed with an incorrect secret key.
    """
    # Token JWT invented and signed with a fake secret key (not the one used by the server)
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.soy_un_hacker_malicioso.FirmaFalsa123"
    headers = {"Authorization": f"Bearer {fake_token}"}

    # Try to access a protected endpoint with the fake token
    response = await client.get("/api/v1/patients/", headers=headers)

    # Assert that the request is rejected with a 401 Unauthorized status
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate credentials"
