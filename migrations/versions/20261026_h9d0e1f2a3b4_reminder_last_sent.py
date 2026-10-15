"""Reminder dedup guard (Phase 2 scheduler).

athlete_profiles.reminder_last_sent (DATE, nullable): last calendar day a
reminder push was sent. Persistent (in-memory would be wiped by Free sleep).
Dispatch sends at most once per user per day.

Revision ID: h9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h9d0e1f2a3b4'
down_revision: Union[str, Sequence[str], None] = 'h8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("athlete_profiles", sa.Column("reminder_last_sent", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("athlete_profiles", "reminder_last_sent")
