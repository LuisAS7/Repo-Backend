import uuid
import enum

from sqlalchemy import Enum as SQLEnum, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base, uuid_pk, str_100, created_at_dt

class AuditAction(str, enum.Enum):
    """Types of actions that can be logged in the audit log"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class AuditLog(Base):
    """Immutable audit log populated automatically by DB triggers to track all changes to critical tables (appointments, patients, staff)"""
    __tablename__ = "audit_log"

    id: Mapped[uuid_pk]
    table_name: Mapped[str_100] = mapped_column(nullable=False)
    action_type: Mapped[AuditAction] = mapped_column(SQLEnum(AuditAction, name="audit_action"), nullable=False) # INSERT, UPDATE, DELETE
    record_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    
    # JSONB is perfect for storing the exact state of the row before and after
    old_data: Mapped[dict | None] = mapped_column(JSONB)
    new_data: Mapped[dict | None] = mapped_column(JSONB)
    
    changed_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True) # ID of the user who made the change, if available
    changed_at: Mapped[created_at_dt]