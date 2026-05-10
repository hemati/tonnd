"""Integration tests for the FatSecret sync pipeline."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from sqlalchemy import select

from src.models.db_models import User
from src.models.fitbit_models import DailyNutrition
from src.models.food_models import FoodEntry
from src.services.fatsecret.client import FatSecretAPIError, FatSecretAuthError
from src.services.fatsecret.sync import (
    backfill_fatsecret,
    disconnect_fatsecret,
    sync_fatsecret_for_date,
)
from src.services.token_encryption import encrypt_token

from tests.conftest import test_session_maker


def _user(**kwargs) -> User:
    defaults = {
        "id": uuid.uuid4(),
        "email": "test@test.com",
        "hashed_password": "hashed",
        "fatsecret_oauth_token": encrypt_token("acc_t"),
        "fatsecret_oauth_token_secret": encrypt_token("acc_s"),
    }
    defaults.update(kwargs)
    return User(**defaults)


def _patch_fetch(entries):
    return patch(
        "src.services.fatsecret.sync.get_food_entries_for_date",
        new_callable=AsyncMock,
        return_value=entries,
    )


def _patch_fetch_raises(exc):
    return patch(
        "src.services.fatsecret.sync.get_food_entries_for_date",
        new_callable=AsyncMock,
        side_effect=exc,
    )


# ─── sync_fatsecret_for_date ─────────────────────────────────────────────


@pytest.mark.asyncio
class TestSyncForDate:
    async def test_inserts_entries_and_aggregates(self):
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()

            entries = [
                {"external_id": "fe1", "date": date(2026, 5, 9),
                 "food_entry_name": "Apple", "meal": "Breakfast",
                 "calories": 95.0, "carbs_g": 25.0},
                {"external_id": "fe2", "date": date(2026, 5, 9),
                 "food_entry_name": "Coffee", "meal": "Breakfast",
                 "calories": 5.0},
            ]
            with _patch_fetch(entries):
                result = await sync_fatsecret_for_date(
                    session, user, date(2026, 5, 9), MagicMock(spec=httpx.AsyncClient),
                )
            await session.flush()

            assert result["errors"] == []
            stored = (await session.execute(
                select(FoodEntry).where(FoodEntry.user_id == user.id)
            )).scalars().all()
            assert len(stored) == 2

            agg = (await session.execute(
                select(DailyNutrition).where(DailyNutrition.user_id == user.id)
            )).scalar_one()
            assert agg.calories_in == 100
            assert agg.carbs_g == 25.0

    async def test_soft_delete_reconciliation(self):
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()

            # Pre-existing entry that won't be in the sync response.
            session.add(FoodEntry(
                user_id=user.id, external_id="fe_stale", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Pizza",
                calories=800.0, carbs_g=100.0,
            ))
            await session.flush()

            with _patch_fetch([
                {"external_id": "fe_new", "date": date(2026, 5, 9),
                 "food_entry_name": "Apple", "calories": 95.0, "carbs_g": 25.0},
            ]):
                await sync_fatsecret_for_date(
                    session, user, date(2026, 5, 9), MagicMock(spec=httpx.AsyncClient),
                )
            await session.flush()

            stale = (await session.execute(
                select(FoodEntry).where(FoodEntry.external_id == "fe_stale")
            )).scalar_one()
            assert stale.deleted_at is not None

            # Aggregation excludes the soft-deleted Pizza.
            agg = (await session.execute(
                select(DailyNutrition).where(DailyNutrition.user_id == user.id)
            )).scalar_one()
            assert agg.calories_in == 95
            assert agg.carbs_g == 25.0

    async def test_empty_day_zeros_aggregate(self):
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()

            with _patch_fetch([]):
                result = await sync_fatsecret_for_date(
                    session, user, date(2026, 5, 9), MagicMock(spec=httpx.AsyncClient),
                )
            await session.flush()

            assert result["errors"] == []
            agg = (await session.execute(
                select(DailyNutrition).where(DailyNutrition.user_id == user.id)
            )).scalar_one()
            assert agg.calories_in == 0
            assert agg.carbs_g == 0.0

    async def test_undeletes_returning_entry(self):
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()

            ts = datetime(2026, 5, 8, 12, tzinfo=timezone.utc)
            session.add(FoodEntry(
                user_id=user.id, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
                deleted_at=ts,
            ))
            await session.flush()

            with _patch_fetch([
                {"external_id": "fe1", "date": date(2026, 5, 9),
                 "food_entry_name": "Apple", "calories": 95.0},
            ]):
                await sync_fatsecret_for_date(
                    session, user, date(2026, 5, 9), MagicMock(spec=httpx.AsyncClient),
                )
            await session.flush()

            row = (await session.execute(
                select(FoodEntry).where(FoodEntry.external_id == "fe1")
            )).scalar_one()
            assert row.deleted_at is None

    async def test_auth_error_propagates(self):
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()

            with _patch_fetch_raises(FatSecretAuthError("token rejected")):
                with pytest.raises(FatSecretAuthError):
                    await sync_fatsecret_for_date(
                        session, user, date(2026, 5, 9), MagicMock(spec=httpx.AsyncClient),
                    )

    async def test_api_error_recorded_and_aggregate_still_runs(self):
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()

            # Pre-existing entry; aggregation should still produce a row using DB state.
            session.add(FoodEntry(
                user_id=user.id, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
                calories=95.0,
            ))
            await session.flush()

            with _patch_fetch_raises(FatSecretAPIError("transient")):
                result = await sync_fatsecret_for_date(
                    session, user, date(2026, 5, 9), MagicMock(spec=httpx.AsyncClient),
                )
            await session.flush()

            assert any("transient" in e for e in result["errors"])
            agg = (await session.execute(
                select(DailyNutrition).where(DailyNutrition.user_id == user.id)
            )).scalar_one()
            assert agg.calories_in == 95


# ─── backfill ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestBackfill:
    async def test_iterates_n_days(self):
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()
            with _patch_fetch([]) as fetch:
                await backfill_fatsecret(
                    session, user, num_days=3, http=MagicMock(spec=httpx.AsyncClient),
                )
            assert fetch.call_count == 3

    async def test_aborts_on_auth_error(self):
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()
            with _patch_fetch_raises(FatSecretAuthError("rejected")) as fetch:
                result = await backfill_fatsecret(
                    session, user, num_days=10, http=MagicMock(spec=httpx.AsyncClient),
                )
            # Stops at the first auth failure.
            assert fetch.call_count == 1
            assert any("auth" in e for e in result["errors"])


class TestDisconnect:
    def test_clears_tokens(self):
        u = _user()
        disconnect_fatsecret(u)
        assert u.fatsecret_oauth_token is None
        assert u.fatsecret_oauth_token_secret is None
