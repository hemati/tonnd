"""Typed table for body composition measurements from all sources."""

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
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.db_models import Base
from src.models.fitbit_models import _iso


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, default=None)
    bmi: Mapped[float | None] = mapped_column(Float, default=None)
    body_fat_percent: Mapped[float | None] = mapped_column(Float, default=None)
    body_water_percent: Mapped[float | None] = mapped_column(Float, default=None)
    muscle_mass_percent: Mapped[float | None] = mapped_column(Float, default=None)
    bone_mass_kg: Mapped[float | None] = mapped_column(Float, default=None)
    bmr_kcal: Mapped[int | None] = mapped_column(Integer, default=None)
    visceral_fat: Mapped[float | None] = mapped_column(Float, default=None)
    subcutaneous_fat_percent: Mapped[float | None] = mapped_column(Float, default=None)
    protein_percent: Mapped[float | None] = mapped_column(Float, default=None)
    body_age: Mapped[int | None] = mapped_column(Integer, default=None)
    lean_body_mass_kg: Mapped[float | None] = mapped_column(Float, default=None)
    fat_free_weight_kg: Mapped[float | None] = mapped_column(Float, default=None)
    heart_rate: Mapped[int | None] = mapped_column(Integer, default=None)
    cardiac_index: Mapped[float | None] = mapped_column(Float, default=None)
    body_shape: Mapped[int | None] = mapped_column(Integer, default=None)
    sport_flag: Mapped[bool | None] = mapped_column(Boolean, default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "source", "measured_at", name="uq_body_measurement"),
        Index("ix_body_measurement_user_date", "user_id", "date"),
    )

    def to_dict(self) -> dict:
        d = {
            "date": self.date.isoformat(),
            "source": self.source,
            "measured_at": _iso(self.measured_at),
        }
        for field in (
            "weight_kg", "bmi", "body_fat_percent", "body_water_percent",
            "muscle_mass_percent", "bone_mass_kg", "bmr_kcal", "visceral_fat",
            "subcutaneous_fat_percent", "protein_percent", "body_age",
            "lean_body_mass_kg", "fat_free_weight_kg", "heart_rate",
            "cardiac_index", "body_shape", "sport_flag",
        ):
            val = getattr(self, field)
            if val is not None:
                d[field] = val
        return d
