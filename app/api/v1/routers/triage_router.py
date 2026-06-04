from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker, get_db
from app.models.users import Staff, StaffRole
from app.schemas.appointments_schema import TriageCreate, TriageResponse
from app.services.triage_service import create_triage

router = APIRouter(prefix="/triage", tags=["Triage"])

@router.post("/{appointment_id}", response_model=TriageResponse, status_code=status.HTTP_201_CREATED)
async def registrar_triage(
    appointment_id: UUID,
    payload: TriageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(RoleChecker([StaffRole.NURSE, StaffRole.DOCTOR]))
):
    """
    Records vital signs for a specific appointment ID.
    
    Requirements:
        - Path Parameter: appointment_id (UUID)
        - RBAC Enforcement: Only accessible by authenticated NURSE or DOCTOR accounts.
    """
    # Security mapping: Override or bind the nurse_id to the authenticated token bearer's ID
    payload.nurse_id = current_user.id
    
    nuevo_triage = await create_triage(db, appointment_id, payload)
    return nuevo_triage