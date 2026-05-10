"""Typed table for FatSecret food diary entries."""

import uuid
from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import (
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


class FoodEntry(Base):
    __tablename__ = "food_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    meal: Mapped[str | None] = mapped_column(String(32), default=None)

    food_id: Mapped[str | None] = mapped_column(String(64), default=None)
    serving_id: Mapped[str | None] = mapped_column(String(64), default=None)
    food_entry_name: Mapped[str] = mapped_column(String(256), nullable=False)
    food_entry_description: Mapped[str | None] = mapped_column(String(512), default=None)
    number_of_units: Mapped[float | None] = mapped_column(Float, default=None)

    # Macros (per FatSecret: already multiplied by number_of_units)
    calories: Mapped[float | None] = mapped_column(Float, default=None)
    carbs_g: Mapped[float | None] = mapped_column(Float, default=None)
    fat_g: Mapped[float | None] = mapped_column(Float, default=None)
    protein_g: Mapped[float | None] = mapped_column(Float, default=None)
    fiber_g: Mapped[float | None] = mapped_column(Float, default=None)
    sugar_g: Mapped[float | None] = mapped_column(Float, default=None)
    saturated_fat_g: Mapped[float | None] = mapped_column(Float, default=None)
    polyunsaturated_fat_g: Mapped[float | None] = mapped_column(Float, default=None)
    monounsaturated_fat_g: Mapped[float | None] = mapped_column(Float, default=None)

    # Micros
    cholesterol_mg: Mapped[float | None] = mapped_column(Float, default=None)
    sodium_mg: Mapped[float | None] = mapped_column(Float, default=None)
    calcium_mg: Mapped[float | None] = mapped_column(Float, default=None)
    iron_mg: Mapped[float | None] = mapped_column(Float, default=None)
    potassium_mg: Mapped[float | None] = mapped_column(Float, default=None)
    vitamin_a_iu: Mapped[float | None] = mapped_column(Float, default=None)
    vitamin_c_mg: Mapped[float | None] = mapped_column(Float, default=None)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "source", "external_id", name="uq_food_entry"),
        Index("ix_food_entry_user_date", "user_id", "date"),
    )

    _SKIP = {"id", "user_id", "synced_at"}

    def to_dict(self) -> dict:
        d: dict = {}
        for col in self.__table__.columns:
            if col.name in self._SKIP:
                continue
            val = getattr(self, col.name)
            if val is None:
                continue
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            d[col.name] = val
        return d
