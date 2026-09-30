"""Add stroke_count_50m to swim_tests (Salo Ch1 technique_flag: high stroke
count => drills + DPS sets in generation).

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("swim_tests", sa.Column("stroke_count_50m", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("swim_tests", "stroke_count_50m")
