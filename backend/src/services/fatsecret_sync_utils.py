"""Upsert helpers for FatSecret typed tables (food_entries, daily_nutrition)."""

from datetime import date as date_type

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.fitbit_models import DailyNutrition
from src.models.food_models import FoodEntry
from src.services.sync_utils import _upsert


async def upsert_food_entry(
    session: AsyncSession, user_id, external_id: str, source: str, **fields
) -> None:
    """Upsert a FatSecret food entry. Restores soft-deleted rows on re-appearance."""
    await _upsert(
        session, FoodEntry,
        {"user_id": user_id, "external_id": external_id, "source": source},
        fields,
        undelete_on_match=True,
    )


def _zero_or_float(v) -> float:
    return float(v) if v is not None else 0.0


async def aggregate_daily_nutrition(
    session: AsyncSession, user_id, target_date: date_type, source: str = "fatsecret",
) -> None:
    """Recompute daily_nutrition from non-deleted food_entries for one (user, date, source).

    Always upserts even with zero entries so a fully-deleted day overwrites stale totals.
    """
    stmt = select(
        func.sum(FoodEntry.calories).label("calories"),
        func.sum(FoodEntry.carbs_g).label("carbs_g"),
        func.sum(FoodEntry.fat_g).label("fat_g"),
        func.sum(FoodEntry.protein_g).label("protein_g"),
        func.sum(FoodEntry.fiber_g).label("fiber_g"),
    ).where(
        FoodEntry.user_id == user_id,
        FoodEntry.source == source,
        FoodEntry.date == target_date,
        FoodEntry.deleted_at.is_(None),
    )
    row = (await session.execute(stmt)).mappings().one()

    fields = {
        "calories_in": int(round(_zero_or_float(row["calories"]))),
        "carbs_g": _zero_or_float(row["carbs_g"]),
        "fat_g": _zero_or_float(row["fat_g"]),
        "protein_g": _zero_or_float(row["protein_g"]),
        "fiber_g": _zero_or_float(row["fiber_g"]),
    }
    await _upsert(
        session, DailyNutrition,
        {"user_id": user_id, "date": target_date, "source": source},
        fields,
    )
