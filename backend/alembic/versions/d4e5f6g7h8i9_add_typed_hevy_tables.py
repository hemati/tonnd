"""Add typed hevy tables (workouts, workout_exercises, routines).

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4e5f6g7h8i9"
down_revision = "c3d4e5f6g7h8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- workouts ---
    op.create_table(
        "workouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("total_volume_kg", sa.Float(), nullable=True),
        sa.Column("total_sets", sa.Integer(), nullable=True),
        sa.Column("total_reps", sa.Integer(), nullable=True),
        sa.Column("muscle_groups", postgresql.JSONB(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "external_id", "source", name="uq_workout"),
    )
    op.create_index("ix_workout_user_date", "workouts", ["user_id", "date"])

    # --- workout_exercises ---
    op.create_table(
        "workout_exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workout_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workouts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("exercise_index", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.String(256), nullable=True),
        sa.Column("external_exercise_id", sa.String(64), nullable=True),
        sa.Column("exercise_type", sa.String(32), nullable=True),
        sa.Column("is_custom", sa.Boolean(), nullable=True),
        sa.Column("supersets_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("volume_kg", sa.Float(), nullable=True),
        sa.Column("primary_muscle", sa.String(32), nullable=True),
        sa.Column("secondary_muscles", postgresql.JSONB(), nullable=True),
        sa.Column("sets", postgresql.JSONB(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_workout_exercise_workout", "workout_exercises", ["workout_id"])

    # --- routines ---
    op.create_table(
        "routines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=True),
        sa.Column("folder_id", sa.Integer(), nullable=True),
        sa.Column("exercises", postgresql.JSONB(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "external_id", "source", name="uq_routine"),
    )


def downgrade() -> None:
    op.drop_table("routines")
    op.drop_table("workout_exercises")
    op.drop_table("workouts")
