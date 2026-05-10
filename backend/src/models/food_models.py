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
from src.models.fitbit_models import _iso


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
        Index("ix_food_entries_user_date", "user_id", "date"),
    )

    def to_dict(self) -> dict:
        d = {
            "external_id": self.external_id,
            "source": self.source,
            "date": self.date.isoformat(),
            "food_entry_name": self.food_entry_name,
        }
        if self.deleted_at is not None:
            d["deleted_at"] = _iso(self.deleted_at)
        for field in (
            "meal", "food_id", "serving_id", "food_entry_description", "number_of_units",
            "calories", "carbs_g", "fat_g", "protein_g", "fiber_g", "sugar_g",
            "saturated_fat_g", "polyunsaturated_fat_g", "monounsaturated_fat_g",
            "cholesterol_mg", "sodium_mg", "calcium_mg", "iron_mg", "potassium_mg",
            "vitamin_a_iu", "vitamin_c_mg",
        ):
            val = getattr(self, field)
            if val is not None:
                d[field] = val
        return d
