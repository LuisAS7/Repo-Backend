from datetime import date, time
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.appointments import Appointment, AppointmentStatus, DiagnosisCatalog
from app.models.patients import Patient
from app.models.users import Staff, StaffRole

# Mark the entire module to use asyncio for pytest
pytestmark = pytest.mark.asyncio


# TEST CASES FOR CONSULTATION CREATION
async def test_create_consultation_success_as_doctor(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies that an authenticated staff member with DOCTOR role can successfully create a consultation
    for a patient who has an appointment in the WAITING state.
    """
    # Create a test Doctor user, a test Patient, and a test Appointment in the database
    doctor_user = Staff(
        id=uuid4(),
        first_name="Doc",
        last_name="House",
        email="doctor@valsync.com",
        password_hash=hash_password("Pass123"),
        role=StaffRole.DOCTOR,
        is_active=True,
    )
    db_session.add(doctor_user)

    test_patient = Patient(
        id=uuid4(),
        document_number="88888888",
        first_name="Ana",
        last_name="Perez",
        birth_date=date(1990, 1, 1),
        gender="FEMALE",
        is_active=True,
    )
    db_session.add(test_patient)

    # Insert a diagnosis catalog entry to be used in the consultation
    test_diagnosis = DiagnosisCatalog(id=uuid4(), code="J00", name="Resfriado común")
    db_session.add(test_diagnosis)

    # Create an appointment in the WAITING state for the patient with the doctor
    test_appointment = Appointment(
        id=uuid4(),
        patient_id=test_patient.id,
        doctor_id=doctor_user.id,
        scheduled_date=date.today(),
        scheduled_time=time(10, 0),
        status=AppointmentStatus.WAITING,  # State must be WAITING to allow consultation creation
    )
    db_session.add(test_appointment)
    await db_session.commit()

    # Generate a valid JWT token for the doctor user to authenticate the request
    token = create_access_token(data={"sub": str(doctor_user.id), "role": doctor_user.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    # Prepare the payload for creating a consultation, including nested prescriptions and diagnoses
    payload = {
        "subjective": "Dolor de cabeza intenso",
        "objective": "Garganta irritada",
        "assessment": "Faringitis viral",
        "plan": "Descanso y paracetamol",
        "diagnosis_ids": [str(test_diagnosis.id)],
        "prescriptions": [
            {"medication": "Paracetamol 500mg", "dose": "1 tableta", "frequency": "Cada 8 horas", "duration_days": 3}
        ],
    }

    # Execute the POST request to create the consultation for the appointment
    response = await client.post(
        f"/api/v1/appointments/{test_appointment.id}/consultation", json=payload, headers=headers
    )

    # Assert that the consultation was created successfully and validate the response content
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["assessment"] == "Faringitis viral"
    assert len(data["diagnoses"]) == 1
    assert data["diagnoses"][0]["code"] == "J00"
    assert len(data["prescriptions"]) == 1
    assert data["prescriptions"][0]["medication"] == "Paracetamol 500mg"


# TEST CASES FOR DOUBLE BOOKING AND TRIAGE VALIDATION
async def test_prevent_double_booking_exception(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies that the system prevents scheduling two appointments for the same doctor at the same date and time,
    and raises a DoubleBookingError with the appropriate HTTP 400 response.
    """
    # Create a test Doctor user and two test Patients in the database
    doctor_user = Staff(
        id=uuid4(),
        first_name="Doc",
        last_name="Conflict",
        email="doc_conflict@valsync.com",
        password_hash=hash_password("Pass123"),
        role=StaffRole.DOCTOR,
        is_active=True,
    )
    admin_user = Staff(
        id=uuid4(),
        first_name="Admin",
        last_name="System",
        email="admin_schedule@valsync.com",
        password_hash=hash_password("Pass123"),
        role=StaffRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([doctor_user, admin_user])

    patient_1 = Patient(
        id=uuid4(),
        document_number="11111111",
        first_name="Paciente",
        last_name="Uno",
        birth_date=date(1990, 1, 1),
        gender="MALE",
        is_active=True,
    )
    patient_2 = Patient(
        id=uuid4(),
        document_number="22222222",
        first_name="Paciente",
        last_name="Dos",
        birth_date=date(1992, 2, 2),
        gender="FEMALE",
        is_active=True,
    )
    db_session.add_all([patient_1, patient_2])
    await db_session.commit()

    # Generate a valid JWT token for the doctor user to authenticate the request
    token = create_access_token(data={"sub": str(admin_user.id), "role": admin_user.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    # Schedule the FIRST appointment (Should be successful)
    payload_1 = {
        "scheduled_date": "2026-10-15",
        "scheduled_time": "14:30:00",
        "patient_id": str(patient_1.id),
        "doctor_id": str(doctor_user.id),
        "reason": "Consulta de rutina",
    }
    response_1 = await client.post("/api/v1/appointments/", json=payload_1, headers=headers)
    assert response_1.status_code == status.HTTP_201_CREATED

    # Try to schedule the SECOND appointment
    # at the same date and time for the same doctor (Should raise DoubleBookingError)
    payload_2 = {
        "scheduled_date": "2026-10-15",
        "scheduled_time": "14:30:00",  # Conflicting time with the first appointment
        "patient_id": str(patient_2.id),
        "doctor_id": str(doctor_user.id),
        "reason": "Urgencia menor",
    }
    response_2 = await client.post("/api/v1/appointments/", json=payload_2, headers=headers)

    # Assert that the second appointment creation failed due to double booking and validate the error response
    assert response_2.status_code == status.HTTP_409_CONFLICT
    assert "the requested time slot is already booked for this doctor" in response_2.json()["message"].lower()


# TEST CASES FOR CONSULTATION CREATION WITH TRIAGE VALIDATION
async def test_prevent_consultation_without_triage(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies that the system prevents creating a consultation for an appointment that has not yet been triaged,
    and raises an HTTP 400 error with an appropriate message.
    """
    # Create a test Doctor user, a test Patient, and a test DiagnosisCatalog entry in the database
    doctor_user = Staff(
        id=uuid4(),
        first_name="Doc",
        last_name="Rules",
        email="doc_rules@valsync.com",
        password_hash=hash_password("Pass123"),
        role=StaffRole.DOCTOR,
        is_active=True,
    )
    test_patient = Patient(
        id=uuid4(),
        document_number="33333333",
        first_name="Paciente",
        last_name="Tres",
        birth_date=date(1995, 3, 3),
        gender="MALE",
        is_active=True,
    )
    test_diagnosis = DiagnosisCatalog(id=uuid4(), code="A09", name="Diarrea y gastroenteritis")
    db_session.add_all([doctor_user, test_patient, test_diagnosis])

    # Appointment in SCHEDULED state (not yet triaged)
    test_appointment = Appointment(
        id=uuid4(),
        patient_id=test_patient.id,
        doctor_id=doctor_user.id,
        scheduled_date=date.today(),
        scheduled_time=time(11, 0),
        status=AppointmentStatus.SCHEDULED,
    )
    db_session.add(test_appointment)
    await db_session.commit()

    token = create_access_token(data={"sub": str(doctor_user.id), "role": doctor_user.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    # Try to create a consultation for the appointment that is still in SCHEDULED state
    payload = {
        "subjective": "Dolor de estómago",
        "objective": "Abdomen tenso",
        "assessment": "Gastroenteritis",
        "plan": "Hidratación",
        "diagnosis_ids": [str(test_diagnosis.id)],
        "prescriptions": [],
    }
    response = await client.post(
        f"/api/v1/appointments/{test_appointment.id}/consultation", json=payload, headers=headers
    )

    # Assert that the consultation creation is rejected due to the appointment not being in WAITING state
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "triage first" in response.json()["detail"].lower()


# TEST CASES FOR APPOINTMENT CANCELLATION
async def test_cancel_appointment_successfully(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies that an authenticated staff member with ADMIN role can successfully cancel an appointment
    and that the cancellation reason is saved correctly.
    """
    # Create a test Admin user, a test Doctor user, a test Patient, and a test Appointment in the database
    admin_user = Staff(
        id=uuid4(),
        first_name="Admin",
        last_name="Cancel",
        email="admin_cancel@valsync.com",
        password_hash=hash_password("Pass123"),
        role=StaffRole.ADMIN,
        is_active=True,
    )
    doctor_user = Staff(
        id=uuid4(),
        first_name="Doc",
        last_name="Cancel",
        email="doc_cancel@valsync.com",
        password_hash=hash_password("Pass123"),
        role=StaffRole.DOCTOR,
        is_active=True,
    )
    test_patient = Patient(
        id=uuid4(),
        document_number="44444444",
        first_name="Paciente",
        last_name="Cuatro",
        birth_date=date(1998, 4, 4),
        gender="FEMALE",
        is_active=True,
    )
    db_session.add_all([admin_user, doctor_user, test_patient])

    test_appointment = Appointment(
        id=uuid4(),
        patient_id=test_patient.id,
        doctor_id=doctor_user.id,
        scheduled_date=date.today(),
        scheduled_time=time(12, 0),
        status=AppointmentStatus.SCHEDULED,
    )
    db_session.add(test_appointment)
    await db_session.commit()

    token = create_access_token(data={"sub": str(admin_user.id), "role": admin_user.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    # The cancellation reason is sent in the request body as JSON
    payload = {"cancellation_reason": "El paciente llamó para cancelar por motivos de salud"}
    response = await client.patch(f"/api/v1/appointments/{test_appointment.id}/cancel", json=payload, headers=headers)

    # Assert that the appointment was canceled successfully and validate the response content
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "CANCELLED"
    assert data["cancellation_reason"] == "El paciente llamó para cancelar por motivos de salud"
