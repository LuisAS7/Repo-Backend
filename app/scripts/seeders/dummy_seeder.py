"""
Dummy data seeder for development and testing
Inserts fake Staff, Patients, and Appointments (NEVER run in production)
"""

import logging
from datetime import date, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.database import AsyncSessionLocal
from app.models.appointments import Appointment, AppointmentOrigin, AppointmentStatus
from app.models.patients import BloodType, Gender, MedicalBackground, Patient
from app.models.users import DoctorProfile, Specialty, Staff, StaffRole

logger = logging.getLogger(__name__)


async def create_dummy_staff(session: AsyncSession):
    """Creates an Admin and a Doctor"""
    # Check if the dummy staff already exists to prevent duplicates on multiple runs
    if (await session.execute(select(Staff).where(Staff.email == "admin@valsync.com"))).scalar_one_or_none():
        logger.info("✅ Dummy Staff already exists. Skipping...")
        return None

    logger.info("⏳ Seeding Dummy Staff...")
    default_password = hash_password("Password123!")

    admin = Staff(
        first_name="System",
        last_name="Admin",
        email="admin@valsync.com",
        password_hash=default_password,
        role=StaffRole.ADMIN,
    )
    session.add(admin)

    # Create a doctor with a specialty
    specialty = (await session.execute(select(Specialty).where(Specialty.name == "Cardiology"))).scalar_one_or_none()

    doctor = Staff(
        first_name="Gregory",
        last_name="House",
        email="house@valsync.com",
        password_hash=default_password,
        role=StaffRole.DOCTOR,
    )
    session.add(doctor)
    await session.flush()  # Flush for obtaining doctor.id

    if specialty:
        profile = DoctorProfile(staff_id=doctor.id, specialty_id=specialty.id, medical_license="MED-998877")
        session.add(profile)

    return doctor


async def create_dummy_patients(session: AsyncSession):
    """Creates a couple of test patients"""
    if (await session.execute(select(Patient).where(Patient.document_number == "123456789"))).scalar_one_or_none():
        logger.info("✅ Dummy Patients already exist. Skipping...")
        return None

    logger.info("⏳ Seeding Dummy Patients...")

    patient1 = Patient(
        document_number="123456789",
        first_name="Frank",
        last_name="Doe",
        birth_date=date(1985, 5, 15),
        gender=Gender.MALE,
        phone="+1234567890",
        email="frank.doe@example.com",
    )
    session.add(patient1)
    await session.flush()

    # Le agregamos background médico
    bg1 = MedicalBackground(patient_id=patient1.id, blood_type=BloodType.O_POS, notes="No known issues")
    session.add(bg1)

    return patient1


async def create_dummy_appointments(session: AsyncSession, doctor: Staff, patient: Patient):
    """Creates a test appointment linking the doctor and patient"""
    if not doctor or not patient:
        return

    logger.info("⏳ Seeding Dummy Appointments...")

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        scheduled_date=date.today() + timedelta(days=1),  # Tomorrow
        scheduled_time=time(10, 30),  # 10:30 AM
        status=AppointmentStatus.SCHEDULED,
        origin=AppointmentOrigin.VALCARE,
        reason="Routine heart checkup",
    )
    session.add(appointment)


async def seed_dummy_data() -> None:
    """Orchestrates the insertion of fake development data"""
    async with AsyncSessionLocal() as session:
        try:
            doctor = await create_dummy_staff(session)
            patient = await create_dummy_patients(session)

            if doctor and patient:
                await create_dummy_appointments(session, doctor, patient)

            await session.commit()
            logger.info("✅ Dummy data seeded successfully!")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error seeding dummy data: {str(e)}")
            raise
