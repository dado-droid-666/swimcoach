"""Push subscriptions + reminder prefs (Phase 1: infra, no scheduler yet).

- push_subscriptions: Web Push endpoints per user (upsert by endpoint).
- athlete_profiles.reminder_time/reminder_tz: per-user reminder prefs,
  modeled now so Phase 2 (scheduler) needs no new migration.

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h8c9d0e1f2a3'
down_revision: Union[str, Sequence[str], None] = 'g7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("endpoint", sa.Text(), nullable=False, unique=True),
        sa.Column("p256dh", sa.String(255), nullable=False),
        sa.Column("auth", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.add_column("athlete_profiles", sa.Column("reminder_time", sa.String(5), nullable=True))
    op.add_column("athlete_profiles", sa.Column("reminder_tz", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("athlete_profiles", "reminder_tz")
    op.drop_column("athlete_profiles", "reminder_time")
    op.drop_table("push_subscriptions")
