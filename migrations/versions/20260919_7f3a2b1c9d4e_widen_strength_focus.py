"""Widen strength_sessions.focus to VARCHAR(50) for split labels.

Revision ID: 7f3a2b1c9d4e
Revises: dc338242d280
Create Date: 2026-09-19

Split labels like "General adaptation · Split A (Pull + Core)" (40 chars)
overflowed the original VARCHAR(20) and broke macrocycle generation.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f3a2b1c9d4e'
down_revision: Union[str, Sequence[str], None] = 'dc338242d280'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("strength_sessions", "focus",
                    existing_type=sa.VARCHAR(length=20),
                    type_=sa.String(length=50),
                    existing_nullable=False)


def downgrade() -> None:
    op.alter_column("strength_sessions", "focus",
                    existing_type=sa.VARCHAR(length=50),
                    type_=sa.String(length=20),
                    existing_nullable=False)
