"""Widen session focus to String(100) (Salo suffixes exceed legacy 50).

SQLite never enforced VARCHAR length, so this only matters on Postgres,
where long focus strings 500'd session generation.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("training_sessions", "focus",
                    existing_type=sa.String(length=50),
                    type_=sa.String(length=100),
                    existing_nullable=True)
    op.alter_column("strength_sessions", "focus",
                    existing_type=sa.String(length=50),
                    type_=sa.String(length=100),
                    existing_nullable=False)


def downgrade() -> None:
    op.alter_column("strength_sessions", "focus",
                    existing_type=sa.String(length=100),
                    type_=sa.String(length=50),
                    existing_nullable=False)
    op.alter_column("training_sessions", "focus",
                    existing_type=sa.String(length=100),
                    type_=sa.String(length=50),
                    existing_nullable=True)
