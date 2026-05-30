"""Add fitbit_backfill_jobs table for paced historical backfill.

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fitbit_backfill_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("state", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("phase", sa.String(16), nullable=False, server_default="ranges"),
        sa.Column("days_requested", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("days_done", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ranges_done", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_resume_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_fitbit_backfill_jobs_user", "fitbit_backfill_jobs", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_fitbit_backfill_jobs_user", table_name="fitbit_backfill_jobs")
    op.drop_table("fitbit_backfill_jobs")
