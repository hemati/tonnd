"""Tests for FoodEntry model — schema, constraints, to_dict."""

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from src.models.food_models import FoodEntry

from tests.conftest import test_session_maker


@pytest.mark.asyncio
class TestFoodEntrySchema:
    async def test_insert_minimal(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            session.add(FoodEntry(
                user_id=uid, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
            ))
            await session.commit()

    async def test_unique_user_source_external_id(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            session.add(FoodEntry(
                user_id=uid, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
            ))
            await session.commit()
            session.add(FoodEntry(
                user_id=uid, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 10), food_entry_name="Apple v2",
            ))
            with pytest.raises(IntegrityError):
                await session.commit()

    async def test_same_external_id_different_user_ok(self):
        async with test_session_maker() as session:
            session.add(FoodEntry(
                user_id=uuid.uuid4(), external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
            ))
            session.add(FoodEntry(
                user_id=uuid.uuid4(), external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
            ))
            await session.commit()


@pytest.mark.asyncio
class TestFoodEntryToDict:
    async def test_required_fields_always_present(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            row = FoodEntry(
                user_id=uid, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
            )
            session.add(row)
            await session.commit()
            d = row.to_dict()
            assert d["external_id"] == "fe1"
            assert d["source"] == "fatsecret"
            assert d["date"] == "2026-05-09"
            assert d["food_entry_name"] == "Apple"

    async def test_omits_null_macros_and_micros(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            row = FoodEntry(
                user_id=uid, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Oatmeal",
                meal="Breakfast", calories=350.0, carbs_g=60.0, protein_g=12.0,
            )
            session.add(row)
            await session.commit()
            d = row.to_dict()
            assert d["meal"] == "Breakfast"
            assert d["calories"] == 350.0
            assert d["carbs_g"] == 60.0
            assert d["protein_g"] == 12.0
            assert "fat_g" not in d
            assert "sodium_mg" not in d
            assert "vitamin_c_mg" not in d
            assert "deleted_at" not in d

    async def test_includes_deleted_at_when_set(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            ts = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
            row = FoodEntry(
                user_id=uid, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
                deleted_at=ts,
            )
            session.add(row)
            await session.commit()
            d = row.to_dict()
            assert "deleted_at" in d
            assert d["deleted_at"].startswith("2026-05-09T12:00:00")

    async def test_excludes_internal_fields(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            row = FoodEntry(
                user_id=uid, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            d = row.to_dict()
            assert "id" not in d
            assert "user_id" not in d
            assert "synced_at" not in d
