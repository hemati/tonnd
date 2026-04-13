"""Typed tables for Hevy workout data.

Replaces JSON-blob rows in fitness_metrics (source='hevy').
"""

import uuid
from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.db_models import Base
from src.models.fitbit_models import JSONBCompat, _iso


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str | None] = mapped_column(String(256), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    total_volume_kg: Mapped[float | None] = mapped_column(Float, default=None)
    total_sets: Mapped[int | None] = mapped_column(Integer, default=None)
    total_reps: Mapped[int | None] = mapped_column(Integer, default=None)
    muscle_groups: Mapped[dict | None] = mapped_column(JSONBCompat, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "external_id", "source", name="uq_workout"),
        Index("ix_workout_user_date", "user_id", "date"),
    )

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(), "source": self.source,
            "external_id": self.external_id, "title": self.title,
            "description": self.description,
            "started_at": _iso(self.started_at), "ended_at": _iso(self.ended_at),
            "duration_minutes": self.duration_minutes,
            "total_volume_kg": self.total_volume_kg,
            "total_sets": self.total_sets, "total_reps": self.total_reps,
            "muscle_groups": self.muscle_groups,
        }


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    exercise_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str | None] = mapped_column(String(256), default=None)
    external_exercise_id: Mapped[str | None] = mapped_column(String(64), default=None)
    exercise_type: Mapped[str | None] = mapped_column(String(32), default=None)
    is_custom: Mapped[bool | None] = mapped_column(Boolean, default=None)
    supersets_id: Mapped[int | None] = mapped_column(Integer, default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    volume_kg: Mapped[float | None] = mapped_column(Float, default=None)
    primary_muscle: Mapped[str | None] = mapped_column(String(32), default=None)
    secondary_muscles: Mapped[list | None] = mapped_column(JSONBCompat, default=None)
    sets: Mapped[list | None] = mapped_column(JSONBCompat, default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_workout_exercise_workout", "workout_id"),
    )

    def to_dict(self) -> dict:
        return {
            "exercise_index": self.exercise_index, "title": self.title,
            "external_exercise_id": self.external_exercise_id,
            "exercise_type": self.exercise_type, "is_custom": self.is_custom,
            "supersets_id": self.supersets_id, "notes": self.notes,
            "volume_kg": self.volume_kg,
            "primary_muscle": self.primary_muscle,
            "secondary_muscles": self.secondary_muscles,
            "sets": self.sets,
        }


class Routine(Base):
    __tablename__ = "routines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str | None] = mapped_column(String(256), default=None)
    folder_id: Mapped[int | None] = mapped_column(Integer, default=None)
    exercises: Mapped[list | None] = mapped_column(JSONBCompat, default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "external_id", "source", name="uq_routine"),
    )

    def to_dict(self) -> dict:
        return {
            "source": self.source, "external_id": self.external_id,
            "title": self.title, "folder_id": self.folder_id,
            "exercises": self.exercises,
        }
