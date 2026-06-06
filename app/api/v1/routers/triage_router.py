from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker, get_db
from app.models.users import Staff, StaffRole
from app.schemas.appointments_schema import TriageCreate, TriageUpdate, TriageResponse
from app.services.triage_service import create_triage, get_triage_by_appointment, update_triage

router = APIRouter(prefix="/triage", tags=["Triage"])

# ---------------------------------------------------------------------------
# POST: Register Triage
# ---------------------------------------------------------------------------
@router.post("/{appointment_id}", response_model=TriageResponse, status_code=status.HTTP_201_CREATED)
async def registrar_triage(
    appointment_id: UUID,
    payload: TriageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(RoleChecker([StaffRole.NURSE, StaffRole.DOCTOR]))
):
    """
    Records vital signs and physical metrics for a specific appointment ID.
    
    Requirements:
        - Path Parameter: appointment_id (UUID)
        - RBAC Enforcement: Accessible by authenticated NURSE, DOCTOR, or ADMIN accounts.
    """
    # 🌟 FIX: Pass the 4 required positional arguments to match the service layer signature.
    # The nurse_id is securely injected from the validated JWT token bearer.
    nuevo_triage = await create_triage(
        db=db, 
        appointment_id=appointment_id, 
        triage_data=payload, 
        nurse_id=current_user.id
    )
    return nuevo_triage


# ---------------------------------------------------------------------------
# GET: Retrieve Triage by Appointment
# ---------------------------------------------------------------------------
@router.get("/{appointment_id}", response_model=TriageResponse, status_code=status.HTTP_200_OK)
async def obtener_triage(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(RoleChecker([StaffRole.NURSE, StaffRole.DOCTOR]))
):
    """
    Retrieves the Triage medical records associated with a specific appointment ID.
    
    Requirements:
        - Path Parameter: appointment_id (UUID)
        - RBAC Enforcement: Accessible by NURSE, DOCTOR, or ADMIN roles for clinical auditing.
    """
    triage = await get_triage_by_appointment(db, appointment_id)
    if not triage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Triage record not found for this appointment"
        )
    return triage


# ---------------------------------------------------------------------------
# PATCH: Partially Update Triage
# ---------------------------------------------------------------------------
@router.patch("/{appointment_id}", response_model=TriageResponse, status_code=status.HTTP_200_OK)
async def actualizar_triage(
    appointment_id: UUID,
    payload: TriageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(RoleChecker([StaffRole.NURSE, StaffRole.DOCTOR]))
):
    """
    Partially updates an existing Triage record. 
    Recomputes the BMI automatically if physical dimensions (weight/height) are altered.
    
    Requirements:
        - Path Parameter: appointment_id (UUID)
        - Request Body: Only include the specific attributes you intend to modify.
        - RBAC Enforcement: Restrained to clinical staff (NURSE or DOCTOR) to guarantee data integrity.
    """
    updated_triage = await update_triage(db, appointment_id, payload)
    return updated_triage