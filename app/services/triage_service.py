from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.appointments import Triage
from app.schemas.appointments_schema import TriageCreate

async def create_triage(db: AsyncSession, appointment_id: UUID, triage_data: TriageCreate) -> Triage:
    """
    Calculates BMI and inserts a new Triage record into the database.
    
    Args:
        db (AsyncSession): The database session.
        appointment_id (UUID): The target appointment unique identifier.
        triage_data (TriageCreate): Input validation schema from the request body.
        
    Returns:
        Triage: The newly created and persisted Triage database object.
    """
    calculated_bmi = None
    
    # Business logic: Automatically compute BMI if both physical metrics are present
    if triage_data.weight_kg and triage_data.height_cm:
        height_meters = triage_data.height_cm / Decimal("100")
        calculated_bmi = triage_data.weight_kg / (height_meters ** 2)

    db_triage = Triage(
        appointment_id=appointment_id,
        nurse_id=triage_data.nurse_id,
        weight_kg=triage_data.weight_kg,
        height_cm=triage_data.height_cm,
        bmi=calculated_bmi,
        blood_pressure=triage_data.blood_pressure,
        temperature_c=triage_data.temperature_c,
        notes=triage_data.notes
    )
    
    db.add(db_triage)
    await db.commit()
    await db.refresh(db_triage)
    return db_triage