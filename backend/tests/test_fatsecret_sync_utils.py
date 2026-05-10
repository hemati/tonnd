"""Tests for fatsecret_sync_utils: upsert_food_entry + aggregate_daily_nutrition."""

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from src.models.fitbit_models import DailyNutrition
from src.models.food_models import FoodEntry
from src.services.fatsecret_sync_utils import (
    aggregate_daily_nutrition,
    upsert_food_entry,
)

from tests.conftest import test_session_maker


@pytest.mark.asyncio
class TestUpsertFoodEntry:
    async def test_insert_new(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            await upsert_food_entry(
                session, uid, "fe1", "fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
                meal="Breakfast", calories=95.0, carbs_g=25.0,
            )
            await session.commit()
            row = (await session.execute(
                select(FoodEntry).where(FoodEntry.user_id == uid)
            )).scalar_one()
            assert row.external_id == "fe1"
            assert row.calories == 95.0
            assert row.deleted_at is None

    async def test_update_existing(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            await upsert_food_entry(
                session, uid, "fe1", "fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
                calories=95.0,
            )
            await session.commit()
            await upsert_food_entry(
                session, uid, "fe1", "fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple (revised)",
                calories=100.0, fiber_g=4.0,
            )
            await session.commit()
            rows = (await session.execute(
                select(FoodEntry).where(FoodEntry.user_id == uid)
            )).scalars().all()
            assert len(rows) == 1
            assert rows[0].food_entry_name == "Apple (revised)"
            assert rows[0].calories == 100.0
            assert rows[0].fiber_g == 4.0

    async def test_undelete_on_reappearance(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            ts = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)
            old_synced = datetime(2026, 5, 8, 6, 0, 0, tzinfo=timezone.utc)
            session.add(FoodEntry(
                user_id=uid, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
                deleted_at=ts, synced_at=old_synced,
            ))
            await session.commit()
            await upsert_food_entry(
                session, uid, "fe1", "fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
                calories=95.0,
            )
            await session.commit()
            row = (await session.execute(
                select(FoodEntry).where(FoodEntry.external_id == "fe1")
            )).scalar_one()
            assert row.deleted_at is None
            assert row.calories == 95.0
            # SQLite drops tz-info on round-trip; compare as naive UTC.
            synced = row.synced_at.replace(tzinfo=None) if row.synced_at.tzinfo else row.synced_at
            assert synced > old_synced.replace(tzinfo=None)


@pytest.mark.asyncio
class TestAggregateDailyNutrition:
    async def test_sums_active_entries(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 5, 9)
            for i, (cal, c, f, p, fb) in enumerate([
                (300.0, 40.0, 8.0, 12.0, 5.0),
                (500.0, 60.0, 15.0, 25.0, 8.0),
            ]):
                session.add(FoodEntry(
                    user_id=uid, external_id=f"fe{i}", source="fatsecret",
                    date=d, food_entry_name=f"Item {i}",
                    calories=cal, carbs_g=c, fat_g=f, protein_g=p, fiber_g=fb,
                ))
            await session.commit()
            await aggregate_daily_nutrition(session, uid, d)
            await session.commit()

            row = (await session.execute(
                select(DailyNutrition).where(DailyNutrition.user_id == uid)
            )).scalar_one()
            assert row.calories_in == 800
            assert row.carbs_g == 100.0
            assert row.fat_g == 23.0
            assert row.protein_g == 37.0
            assert row.fiber_g == 13.0
            assert row.source == "fatsecret"

    async def test_excludes_soft_deleted_entries(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 5, 9)
            ts = datetime.now(timezone.utc)
            session.add(FoodEntry(
                user_id=uid, external_id="fe_active", source="fatsecret",
                date=d, food_entry_name="Apple",
                calories=95.0, carbs_g=25.0,
            ))
            session.add(FoodEntry(
                user_id=uid, external_id="fe_deleted", source="fatsecret",
                date=d, food_entry_name="Pizza",
                calories=800.0, carbs_g=100.0,
                deleted_at=ts,
            ))
            await session.commit()
            await aggregate_daily_nutrition(session, uid, d)
            await session.commit()
            row = (await session.execute(
                select(DailyNutrition).where(DailyNutrition.user_id == uid)
            )).scalar_one()
            assert row.calories_in == 95
            assert row.carbs_g == 25.0

    async def test_zeros_when_no_entries(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 5, 9)
            await aggregate_daily_nutrition(session, uid, d)
            await session.commit()
            row = (await session.execute(
                select(DailyNutrition).where(DailyNutrition.user_id == uid)
            )).scalar_one()
            assert row.calories_in == 0
            assert row.carbs_g == 0.0
            assert row.fat_g == 0.0
            assert row.protein_g == 0.0
            assert row.fiber_g == 0.0

    async def test_recompute_overwrites_previous_aggregate(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 5, 9)
            session.add(FoodEntry(
                user_id=uid, external_id="fe1", source="fatsecret",
                date=d, food_entry_name="Apple",
                calories=500.0, carbs_g=50.0,
            ))
            await session.commit()
            await aggregate_daily_nutrition(session, uid, d)
            await session.commit()

            # Soft-delete the entry, re-aggregate → should drop to 0
            row = (await session.execute(
                select(FoodEntry).where(FoodEntry.user_id == uid)
            )).scalar_one()
            row.deleted_at = datetime.now(timezone.utc)
            await session.commit()
            await aggregate_daily_nutrition(session, uid, d)
            await session.commit()

            agg = (await session.execute(
                select(DailyNutrition).where(DailyNutrition.user_id == uid)
            )).scalar_one()
            assert agg.calories_in == 0
            assert agg.carbs_g == 0.0

