"""Add typed fitbit tables, user flags, clean slate.

Revision ID: c3d4e5f6g7h8
Revises: b2f3a4d5e6g7
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6g7h8"
down_revision = "b2f3a4d5e6g7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- User model: new Fitbit capability flags ---
    op.add_column("user", sa.Column("fitbit_intraday_available", sa.Boolean(), nullable=True))
    op.add_column(
        "user",
        sa.Column("fitbit_scopes_version", sa.Integer(), nullable=True, server_default="1"),
    )

    # --- daily_vitals ---
    op.create_table(
        "daily_vitals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("resting_heart_rate", sa.Float(), nullable=True),
        sa.Column("hr_zones", postgresql.JSONB(), nullable=True),
        sa.Column("daily_rmssd", sa.Float(), nullable=True),
        sa.Column("deep_rmssd", sa.Float(), nullable=True),
        sa.Column("spo2_avg", sa.Float(), nullable=True),
        sa.Column("spo2_min", sa.Float(), nullable=True),
        sa.Column("spo2_max", sa.Float(), nullable=True),
        sa.Column("breathing_rate", sa.Float(), nullable=True),
        sa.Column("vo2_max", sa.Float(), nullable=True),
        sa.Column("temp_relative_deviation", sa.Float(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "date", "source", name="uq_daily_vitals"),
    )
    op.create_index("ix_daily_vitals_user_date", "daily_vitals", ["user_id", "date"])

    # --- daily_sleep ---
    op.create_table(
        "daily_sleep",
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
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_minutes", sa.Integer(), nullable=True),
        sa.Column("deep_minutes", sa.Integer(), nullable=True),
        sa.Column("light_minutes", sa.Integer(), nullable=True),
        sa.Column("rem_minutes", sa.Integer(), nullable=True),
        sa.Column("awake_minutes", sa.Integer(), nullable=True),
        sa.Column("efficiency", sa.Integer(), nullable=True),
        sa.Column("minutes_to_fall_asleep", sa.Integer(), nullable=True),
        sa.Column("time_in_bed", sa.Integer(), nullable=True),
        sa.Column("is_main_sleep", sa.Boolean(), nullable=True),
        sa.Column("stages_30s_summary", postgresql.JSONB(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "source", "external_id", name="uq_daily_sleep"),
    )
    op.create_index("ix_daily_sleep_user_date", "daily_sleep", ["user_id", "date"])

    # --- daily_activity ---
    op.create_table(
        "daily_activity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("calories_burned", sa.Integer(), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("active_minutes", sa.Integer(), nullable=True),
        sa.Column("sedentary_minutes", sa.Integer(), nullable=True),
        sa.Column("lightly_active_minutes", sa.Integer(), nullable=True),
        sa.Column("floors", sa.Integer(), nullable=True),
        sa.Column("calories_bmr", sa.Integer(), nullable=True),
        sa.Column("fat_burn_azm", sa.Integer(), nullable=True),
        sa.Column("cardio_azm", sa.Integer(), nullable=True),
        sa.Column("peak_azm", sa.Integer(), nullable=True),
        sa.Column("total_azm", sa.Integer(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "date", "source", name="uq_daily_activity"),
    )

    # --- daily_body ---
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

    # --- daily_nutrition ---
    op.create_table(
        "daily_nutrition",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("calories_in", sa.Integer(), nullable=True),
        sa.Column("carbs_g", sa.Float(), nullable=True),
        sa.Column("fat_g", sa.Float(), nullable=True),
        sa.Column("protein_g", sa.Float(), nullable=True),
        sa.Column("fiber_g", sa.Float(), nullable=True),
        sa.Column("water_ml", sa.Integer(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "date", "source", name="uq_daily_nutrition"),
    )

    # --- hourly_intraday ---
    op.create_table(
        "hourly_intraday",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("hour", sa.SmallInteger(), nullable=False),
        sa.Column("metric_type", sa.String(32), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("avg_value", sa.Float(), nullable=True),
        sa.Column("min_value", sa.Float(), nullable=True),
        sa.Column("max_value", sa.Float(), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id", "date", "hour", "metric_type", "source", name="uq_hourly_intraday"
        ),
    )
    op.create_index(
        "ix_intraday_user_metric_date",
        "hourly_intraday",
        ["user_id", "metric_type", "date", "hour"],
    )

    # --- exercise_logs ---
    op.create_table(
        "exercise_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activity_name", sa.String(128), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("avg_heart_rate", sa.Integer(), nullable=True),
        sa.Column("calories", sa.Integer(), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("elevation_gain", sa.Float(), nullable=True),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("log_type", sa.String(16), nullable=True),
        sa.Column("hr_zones", postgresql.JSONB(), nullable=True),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "external_id", "source", name="uq_exercise_log"),
    )
    op.create_index("ix_exercise_log_user_date", "exercise_logs", ["user_id", "date"])

    # --- user_context ---
    op.create_table(
        "user_context",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(16), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("utc_offset_ms", sa.Integer(), nullable=True),
        sa.Column("stride_length_walking", sa.Float(), nullable=True),
        sa.Column("stride_length_running", sa.Float(), nullable=True),
        sa.Column("device_model", sa.String(64), nullable=True),
        sa.Column("device_battery", sa.Integer(), nullable=True),
        sa.Column("last_device_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "source", name="uq_user_context"),
    )


def downgrade() -> None:
    op.drop_table("user_context")
    op.drop_table("exercise_logs")
    op.drop_table("hourly_intraday")
    op.drop_table("daily_nutrition")
    op.drop_table("daily_body")
    op.drop_table("daily_activity")
    op.drop_table("daily_sleep")
    op.drop_table("daily_vitals")
    op.drop_column("user", "fitbit_scopes_version")
    op.drop_column("user", "fitbit_intraday_available")
