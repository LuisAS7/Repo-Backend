from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Import custom business exceptions
from app.core.exceptions import NotFoundError, ValidationError
from app.models.appointments import Appointment, AppointmentStatus, Triage
from app.schemas.appointments_schema import TriageCreate, TriageUpdate


# 💡 Local exception definition (can be moved to app.core.exceptions)
class TriageNotFoundError(NotFoundError):
    def __init__(self, detail: str = "Triage record not found for this appointment"):
        super().__init__(detail)


# ---------------------------------------------------------------------------
# Get Triage by Appointment
# ---------------------------------------------------------------------------
async def get_triage_by_appointment(db: AsyncSession, appointment_id: UUID) -> Triage | None:
    """
    Retrieves the Triage record associated with a specific appointment.
    """
    query = select(Triage).where(Triage.appointment_id == appointment_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Create Triage
# ---------------------------------------------------------------------------
# 💡 Added 'nurse_id: UUID' as a mandatory parameter to ensure security
async def create_triage(db: AsyncSession, appointment_id: UUID, triage_data: TriageCreate, nurse_id: UUID) -> Triage:
    """
    Calculates BMI and inserts a new Triage record into the database.
    Safely handles edge cases like 0 in weight or height metrics.
    """
    calculated_bmi = None

    stmt_app = select(Appointment).where(Appointment.id == appointment_id)
    appointment = (await db.execute(stmt_app)).scalar_one_or_none()

    if not appointment or appointment.status not in [
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.READY,
        AppointmentStatus.WAITING,
    ]:
        raise ValidationError(detail="Invalid appointment state for Triage")

    triage_existente = await get_triage_by_appointment(db, appointment_id)
    if triage_existente:
        raise ValidationError("Esta cita ya cuenta con un Triage registrado")

    # Explicit logic: Avoid division by zero if height_cm = 0 is provided in tests
    if triage_data.weight_kg and triage_data.height_cm and triage_data.height_cm > 0:
        height_meters = triage_data.height_cm / Decimal("100")
        calculated_bmi = triage_data.weight_kg / (height_meters**2)

    db_triage = Triage(
        appointment_id=appointment_id,
        nurse_id=nurse_id,  # Use the verified ID extracted from the JWT token
        weight_kg=triage_data.weight_kg,
        height_cm=triage_data.height_cm,
        bmi=calculated_bmi,
        blood_pressure=triage_data.blood_pressure,
        temperature_c=triage_data.temperature_c,
        notes=triage_data.notes,
    )

    try:
        db.add(db_triage)
        appointment.status = AppointmentStatus.WAITING  # Update appointment status to WAITING after Triage
        await db.commit()
        await db.refresh(db_triage)
        return db_triage
    except Exception as e:
        await db.rollback()
        raise e


# ---------------------------------------------------------------------------
# Update Triage (PATCH - Partial Update)
# ---------------------------------------------------------------------------
async def update_triage(db: AsyncSession, appointment_id: UUID, triage_data: TriageUpdate) -> Triage:
    """
    Dynamically updates an existing Triage record using Business Exceptions if not found,
    and automatically recomputes the BMI if physical metrics are modified.
    """
    # 1. Check if the triage record exists using the clean business exception
    db_triage = await get_triage_by_appointment(db, appointment_id)
    if not db_triage:
        raise TriageNotFoundError()

    # 2. Extract only the fields explicitly sent by the client (ignore unset values)
    update_data = triage_data.model_dump(exclude_unset=True)

    # 3. Apply changes dynamically to the database object
    for key, value in update_data.items():
        setattr(db_triage, key, value)

    # 4. Recalculate BMI based on the final state of the record attributes
    current_weight = db_triage.weight_kg
    current_height = db_triage.height_cm

    # 🧮 Bulletproof mathematical validation against zero for the PATCH update
    if current_weight and current_height and current_height > 0:
        height_meters = current_height / Decimal("100")
        db_triage.bmi = current_weight / (height_meters**2)
    else:
        db_triage.bmi = None

    try:
        await db.commit()
        await db.refresh(db_triage)
        return db_triage
    except Exception as e:
        await db.rollback()
        raise e
