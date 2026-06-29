"""add_walk_in_to_appointment_origin_enum

Revision ID: c726ce276b8e
Revises: 73e24f19d0c8
Create Date: 2026-06-28 18:43:03.213744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c726ce276b8e'
down_revision: Union[str, Sequence[str], None] = '73e24f19d0c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE appointment_origin ADD VALUE IF NOT EXISTS 'WALK_IN'")


def downgrade() -> None:
    pass
