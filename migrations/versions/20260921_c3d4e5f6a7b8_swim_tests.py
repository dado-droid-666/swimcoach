"""Create swim_tests (persisted CSS test + athlete data).

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "swim_tests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("date", sa.Date(), nullable=False, index=True),
        sa.Column("tiempo_400_seg", sa.Float(), nullable=True),
        sa.Column("tiempo_200_seg", sa.Float(), nullable=True),
        sa.Column("tiempo_50_seg", sa.Float(), nullable=True),
        sa.Column("css_pace_100_seg", sa.Float(), nullable=True),
        sa.Column("edad", sa.Integer(), nullable=True),
        sa.Column("peso_kg", sa.Float(), nullable=True),
        sa.Column("altura_cm", sa.Float(), nullable=True),
        sa.Column("tier", sa.Integer(), nullable=True),
        sa.Column("modelo_version", sa.String(length=60), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("swim_tests")
