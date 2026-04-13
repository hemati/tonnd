"""Add body_measurements table, drop daily_body.

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e5f6g7h8i9j0"
down_revision = "d4e5f6g7h8i9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- body_measurements (replaces daily_body with richer Renpho fields) ---
    op.create_table(
        "body_measurements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("bmi", sa.Float(), nullable=True),
        sa.Column("body_fat_percent", sa.Float(), nullable=True),
        sa.Column("body_water_percent", sa.Float(), nullable=True),
        sa.Column("muscle_mass_percent", sa.Float(), nullable=True),
        sa.Column("bone_mass_kg", sa.Float(), nullable=True),
        sa.Column("bmr_kcal", sa.Integer(), nullable=True),
        sa.Column("visceral_fat", sa.Float(), nullable=True),
        sa.Column("subcutaneous_fat_percent", sa.Float(), nullable=True),
        sa.Column("protein_percent", sa.Float(), nullable=True),
        sa.Column("body_age", sa.Integer(), nullable=True),
        sa.Column("lean_body_mass_kg", sa.Float(), nullable=True),
        sa.Column("fat_free_weight_kg", sa.Float(), nullable=True),
        sa.Column("heart_rate", sa.Integer(), nullable=True),
        sa.Column("cardiac_index", sa.Float(), nullable=True),
        sa.Column("body_shape", sa.Integer(), nullable=True),
        sa.Column("sport_flag", sa.Boolean(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "source", "measured_at", name="uq_body_measurement"),
    )
    op.create_index("ix_body_measurement_user_date", "body_measurements", ["user_id", "date"])

    # --- drop daily_body (replaced by body_measurements) ---
    op.drop_table("daily_body")


def downgrade() -> None:
    # --- re-create daily_body ---
    op.create_table(
        "daily_body",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("bmi", sa.Float(), nullable=True),
        sa.Column("body_fat_percent", sa.Float(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "date", "source", name="uq_daily_body"),
    )

    # --- drop body_measurements ---
    op.drop_index("ix_body_measurement_user_date", table_name="body_measurements")
    op.drop_table("body_measurements")
