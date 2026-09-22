"""Add athlete_profiles.strength_days (preferred strength weekdays).

Revision ID: a1b2c3d4e5f6
Revises: 7f3a2b1c9d4e
Create Date: 2026-09-19

Mon=0..Sun=6 to match Python weekday(). Empty list = automatic placement.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7f3a2b1c9d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("athlete_profiles",
                  sa.Column("strength_days", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("athlete_profiles", "strength_days")
