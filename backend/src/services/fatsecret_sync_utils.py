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


async def aggregate_daily_nutrition(
    session: AsyncSession, user_id, target_date: date_type, source: str = "fatsecret",
) -> None:
    """Recompute daily_nutrition from non-deleted food_entries for one (user, date, source).

    Always upserts the daily_nutrition row, even when no entries exist for the date —
    callers rely on this to zero out a day when all entries get soft-deleted.
    """
    stmt = select(
        func.coalesce(func.sum(FoodEntry.calories), 0.0),
        func.sum(FoodEntry.carbs_g),
        func.sum(FoodEntry.fat_g),
        func.sum(FoodEntry.protein_g),
        func.sum(FoodEntry.fiber_g),
    ).where(
        FoodEntry.user_id == user_id,
        FoodEntry.source == source,
        FoodEntry.date == target_date,
        FoodEntry.deleted_at.is_(None),
    )
    cal, carbs, fat, protein, fiber = (await session.execute(stmt)).one()

    fields = {
        "calories_in": int(round(cal)) if cal is not None else 0,
        "carbs_g": float(carbs) if carbs is not None else 0.0,
        "fat_g": float(fat) if fat is not None else 0.0,
        "protein_g": float(protein) if protein is not None else 0.0,
        "fiber_g": float(fiber) if fiber is not None else 0.0,
    }
    await _upsert(
        session, DailyNutrition,
        {"user_id": user_id, "date": target_date, "source": source},
        fields,
    )
