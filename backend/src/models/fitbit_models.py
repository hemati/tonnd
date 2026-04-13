"""Typed tables for Fitbit data expansion.

Replaces JSON-blob rows in fitness_metrics with real columns.
All tables include a `source` column for future multi-tracker support.
"""

import uuid
from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.db_models import Base

# Use JSONB on PostgreSQL, fall back to JSON on SQLite (tests)
JSONBCompat = JSON().with_variant(JSONB, "postgresql")


def _iso(val):
    """Convert date/datetime to ISO string, or return None."""
    return val.isoformat() if val else None


class DailyVitals(Base):
    __tablename__ = "daily_vitals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    resting_heart_rate: Mapped[float | None] = mapped_column(Float, default=None)
    hr_zones: Mapped[dict | None] = mapped_column(JSONBCompat, default=None)
    daily_rmssd: Mapped[float | None] = mapped_column(Float, default=None)
    deep_rmssd: Mapped[float | None] = mapped_column(Float, default=None)
    spo2_avg: Mapped[float | None] = mapped_column(Float, default=None)
    spo2_min: Mapped[float | None] = mapped_column(Float, default=None)
    spo2_max: Mapped[float | None] = mapped_column(Float, default=None)
    breathing_rate: Mapped[float | None] = mapped_column(Float, default=None)
    vo2_max: Mapped[float | None] = mapped_column(Float, default=None)
    temp_relative_deviation: Mapped[float | None] = mapped_column(Float, default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "date", "source", name="uq_daily_vitals"),
        Index("ix_daily_vitals_user_date", "user_id", "date"),
    )

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(), "source": self.source,
            "resting_heart_rate": self.resting_heart_rate, "hr_zones": self.hr_zones,
            "daily_rmssd": self.daily_rmssd, "deep_rmssd": self.deep_rmssd,
            "spo2_avg": self.spo2_avg, "spo2_min": self.spo2_min, "spo2_max": self.spo2_max,
            "breathing_rate": self.breathing_rate, "vo2_max": self.vo2_max,
            "temp_relative_deviation": self.temp_relative_deviation,
        }


class DailySleep(Base):
    __tablename__ = "daily_sleep"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    total_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    deep_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    light_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    rem_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    awake_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    efficiency: Mapped[int | None] = mapped_column(Integer, default=None)
    minutes_to_fall_asleep: Mapped[int | None] = mapped_column(Integer, default=None)
    time_in_bed: Mapped[int | None] = mapped_column(Integer, default=None)
    is_main_sleep: Mapped[bool | None] = mapped_column(Boolean, default=None)
    stages_30s_summary: Mapped[dict | None] = mapped_column(JSONBCompat, default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "source", "external_id", name="uq_daily_sleep"),
        Index("ix_daily_sleep_user_date", "user_id", "date"),
    )

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(), "source": self.source,
            "external_id": self.external_id,
            "start_time": _iso(self.start_time), "end_time": _iso(self.end_time),
            "total_minutes": self.total_minutes, "deep_minutes": self.deep_minutes,
            "light_minutes": self.light_minutes, "rem_minutes": self.rem_minutes,
            "awake_minutes": self.awake_minutes, "efficiency": self.efficiency,
            "minutes_to_fall_asleep": self.minutes_to_fall_asleep,
            "time_in_bed": self.time_in_bed, "is_main_sleep": self.is_main_sleep,
            "stages_30s_summary": self.stages_30s_summary,
        }


class DailyActivity(Base):
    __tablename__ = "daily_activity"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    steps: Mapped[int | None] = mapped_column(Integer, default=None)
    calories_burned: Mapped[int | None] = mapped_column(Integer, default=None)
    distance_km: Mapped[float | None] = mapped_column(Float, default=None)
    active_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    sedentary_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    lightly_active_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    floors: Mapped[int | None] = mapped_column(Integer, default=None)
    calories_bmr: Mapped[int | None] = mapped_column(Integer, default=None)
    fat_burn_azm: Mapped[int | None] = mapped_column(Integer, default=None)
    cardio_azm: Mapped[int | None] = mapped_column(Integer, default=None)
    peak_azm: Mapped[int | None] = mapped_column(Integer, default=None)
    total_azm: Mapped[int | None] = mapped_column(Integer, default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "date", "source", name="uq_daily_activity"),
    )

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(), "source": self.source,
            "steps": self.steps, "calories_burned": self.calories_burned,
            "distance_km": self.distance_km, "active_minutes": self.active_minutes,
            "sedentary_minutes": self.sedentary_minutes,
            "lightly_active_minutes": self.lightly_active_minutes,
            "floors": self.floors, "calories_bmr": self.calories_bmr,
            "fat_burn_azm": self.fat_burn_azm, "cardio_azm": self.cardio_azm,
            "peak_azm": self.peak_azm, "total_azm": self.total_azm,
        }


class DailyBody(Base):
    __tablename__ = "daily_body"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, default=None)
    bmi: Mapped[float | None] = mapped_column(Float, default=None)
    body_fat_percent: Mapped[float | None] = mapped_column(Float, default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "date", "source", name="uq_daily_body"),
    )

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(), "source": self.source,
            "weight_kg": self.weight_kg, "bmi": self.bmi,
            "body_fat_percent": self.body_fat_percent,
        }


class DailyNutrition(Base):
    """Reserved — sync not implemented yet."""

    __tablename__ = "daily_nutrition"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    calories_in: Mapped[int | None] = mapped_column(Integer, default=None)
    carbs_g: Mapped[float | None] = mapped_column(Float, default=None)
    fat_g: Mapped[float | None] = mapped_column(Float, default=None)
    protein_g: Mapped[float | None] = mapped_column(Float, default=None)
    fiber_g: Mapped[float | None] = mapped_column(Float, default=None)
    water_ml: Mapped[int | None] = mapped_column(Integer, default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "date", "source", name="uq_daily_nutrition"),
    )


class HourlyIntraday(Base):
    __tablename__ = "hourly_intraday"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    hour: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    metric_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    avg_value: Mapped[float | None] = mapped_column(Float, default=None)
    min_value: Mapped[float | None] = mapped_column(Float, default=None)
    max_value: Mapped[float | None] = mapped_column(Float, default=None)
    sample_count: Mapped[int | None] = mapped_column(Integer, default=None)
    extra: Mapped[dict | None] = mapped_column(JSONBCompat, default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "date", "hour", "metric_type", "source", name="uq_hourly_intraday"),
        Index("ix_intraday_user_metric_date", "user_id", "metric_type", "date", "hour"),
    )

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(), "hour": self.hour,
            "metric_type": self.metric_type, "source": self.source,
            "avg_value": self.avg_value, "min_value": self.min_value,
            "max_value": self.max_value, "sample_count": self.sample_count,
            "extra": self.extra,
        }


class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    activity_name: Mapped[str | None] = mapped_column(String(128), default=None)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    avg_heart_rate: Mapped[int | None] = mapped_column(Integer, default=None)
    calories: Mapped[int | None] = mapped_column(Integer, default=None)
    distance_km: Mapped[float | None] = mapped_column(Float, default=None)
    elevation_gain: Mapped[float | None] = mapped_column(Float, default=None)
    speed_kmh: Mapped[float | None] = mapped_column(Float, default=None)
    log_type: Mapped[str | None] = mapped_column(String(16), default=None)
    hr_zones: Mapped[dict | None] = mapped_column(JSONBCompat, default=None)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "external_id", "source", name="uq_exercise_log"),
        Index("ix_exercise_log_user_date", "user_id", "date"),
    )

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(), "source": self.source,
            "external_id": self.external_id,
            "started_at": _iso(self.started_at), "ended_at": _iso(self.ended_at),
            "activity_name": self.activity_name,
            "duration_minutes": self.duration_minutes,
            "avg_heart_rate": self.avg_heart_rate, "calories": self.calories,
            "distance_km": self.distance_km, "elevation_gain": self.elevation_gain,
            "speed_kmh": self.speed_kmh, "log_type": self.log_type,
            "hr_zones": self.hr_zones,
        }


class UserContext(Base):
    __tablename__ = "user_context"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    date_of_birth: Mapped[date_type | None] = mapped_column(Date, default=None)
    gender: Mapped[str | None] = mapped_column(String(16), default=None)
    height_cm: Mapped[float | None] = mapped_column(Float, default=None)
    timezone: Mapped[str | None] = mapped_column(String(64), default=None)
    utc_offset_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    stride_length_walking: Mapped[float | None] = mapped_column(Float, default=None)
    stride_length_running: Mapped[float | None] = mapped_column(Float, default=None)
    device_model: Mapped[str | None] = mapped_column(String(64), default=None)
    device_battery: Mapped[int | None] = mapped_column(Integer, default=None)
    last_device_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "source", name="uq_user_context"),
    )

    def to_dict(self) -> dict:
        from datetime import date as d
        today = d.today()
        age = None
        if self.date_of_birth:
            age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return {
            "source": self.source,
            "date_of_birth": _iso(self.date_of_birth), "age": age,
            "gender": self.gender, "height_cm": self.height_cm,
            "timezone": self.timezone,
            "device_model": self.device_model, "device_battery": self.device_battery,
            "last_device_sync": _iso(self.last_device_sync),
        }
