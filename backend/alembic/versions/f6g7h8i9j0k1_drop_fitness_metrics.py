"""Drop legacy fitness_metrics table.

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f6g7h8i9j0k1"
down_revision = "e5f6g7h8i9j0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("fitness_metrics")


def downgrade() -> None:
    # Re-create fitness_metrics with its final schema (including source column).
    op.create_table(
        "fitness_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("metric_type", sa.String(32), nullable=False),
        sa.Column("source", sa.String(16), nullable=False, server_default="fitbit"),
        sa.Column("data", postgresql.JSON(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id", "date", "metric_type", "source", name="uq_user_date_metric_source"
        ),
    )
