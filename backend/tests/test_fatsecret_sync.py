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


def _patch_fetch(entries, api_ids=None):
    """Patch get_food_entries_for_date with the new dict return shape.

    `api_ids` defaults to the set of external_ids in `entries` — most callers
    want them to match. Tests for malformed-entry reconciliation pass a
    superset to simulate "API saw an id we couldn't normalize".
    """
    if api_ids is None:
        api_ids = {e["external_id"] for e in entries if "external_id" in e}
    return patch(
        "src.services.fatsecret.sync.get_food_entries_for_date",
        new_callable=AsyncMock,
        return_value={"normalized": entries, "api_external_ids": api_ids},
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
class TestAdversarialRegressions:
    async def test_api_failure_with_no_existing_entries_does_not_write_zero(self):
        """End-of-plan adversarial finding: a transient API failure with an
        empty diary used to write a "trusted 0 calories" daily_nutrition row,
        misleading the user. Now we skip aggregation in that case."""
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()

            with _patch_fetch_raises(FatSecretAPIError("transient")):
                await sync_fatsecret_for_date(
                    session, user, date(2026, 5, 9), MagicMock(spec=httpx.AsyncClient),
                )
            await session.flush()

            agg = (await session.execute(
                select(DailyNutrition).where(DailyNutrition.user_id == user.id)
            )).scalar_one_or_none()
            assert agg is None

    async def test_malformed_entry_does_not_soft_delete_existing(self):
        """End-of-plan adversarial finding: a FatSecret response missing
        food_entry_name on an existing entry used to silently soft-delete the
        stored row because the malformed entry returned None from
        _normalize_entry and dropped out of the upserted set used for
        reconciliation. Reconciliation now uses api_external_ids (which
        includes ids of entries we couldn't normalize)."""
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()
            session.add(FoodEntry(
                user_id=user.id, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
                calories=95.0,
            ))
            await session.flush()

            # API returns the entry but malformed (no name) — _normalize_entry
            # drops it. api_external_ids still contains "fe1".
            with _patch_fetch([], api_ids={"fe1"}):
                await sync_fatsecret_for_date(
                    session, user, date(2026, 5, 9), MagicMock(spec=httpx.AsyncClient),
                )
            await session.flush()

            row = (await session.execute(
                select(FoodEntry).where(FoodEntry.external_id == "fe1")
            )).scalar_one()
            assert row.deleted_at is None

    async def test_api_failure_with_existing_entries_still_aggregates(self):
        """If we have stored data, an API failure shouldn't block recompute —
        the aggregate against current DB state is still meaningful."""
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()
            session.add(FoodEntry(
                user_id=user.id, external_id="fe1", source="fatsecret",
                date=date(2026, 5, 9), food_entry_name="Apple",
                calories=95.0, carbs_g=25.0,
            ))
            await session.flush()

            with _patch_fetch_raises(FatSecretAPIError("transient")):
                await sync_fatsecret_for_date(
                    session, user, date(2026, 5, 9), MagicMock(spec=httpx.AsyncClient),
                )
            await session.flush()

            agg = (await session.execute(
                select(DailyNutrition).where(DailyNutrition.user_id == user.id)
            )).scalar_one()
            assert agg.calories_in == 95


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


# ─── decrypt failure handling ─────────────────────────────────────────


@pytest.mark.asyncio
class TestDecryptFailure:
    async def test_missing_token_raises_auth_error(self):
        async with test_session_maker() as session:
            user = _user(fatsecret_oauth_token=None)
            session.add(user)
            await session.flush()
            with _patch_fetch([]):
                with pytest.raises(FatSecretAuthError):
                    await sync_fatsecret_for_date(
                        session, user, date(2026, 5, 9),
                        MagicMock(spec=httpx.AsyncClient),
                    )

    async def test_corrupt_token_raises_auth_error(self):
        async with test_session_maker() as session:
            # A non-Fernet ciphertext triggers InvalidToken on decrypt.
            user = _user(fatsecret_oauth_token="not-a-valid-fernet-ciphertext")
            session.add(user)
            await session.flush()
            with _patch_fetch([]):
                with pytest.raises(FatSecretAuthError):
                    await sync_fatsecret_for_date(
                        session, user, date(2026, 5, 9),
                        MagicMock(spec=httpx.AsyncClient),
                    )

    async def test_auth_error_message_omits_underlying_detail(self):
        async with test_session_maker() as session:
            user = _user(fatsecret_oauth_token="not-a-valid-fernet-ciphertext")
            session.add(user)
            await session.flush()
            with _patch_fetch([]):
                with pytest.raises(FatSecretAuthError) as exc_info:
                    await sync_fatsecret_for_date(
                        session, user, date(2026, 5, 9),
                        MagicMock(spec=httpx.AsyncClient),
                    )
            # Message must not echo the encrypted value back.
            assert "not-a-valid-fernet-ciphertext" not in str(exc_info.value)


@pytest.mark.asyncio
class TestBackfillCapping:
    async def test_clamps_num_days_to_max(self):
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()
            with _patch_fetch([]) as fetch:
                from src.services.fatsecret.sync import MAX_BACKFILL_DAYS
                await backfill_fatsecret(
                    session, user, num_days=10_000,
                    http=MagicMock(spec=httpx.AsyncClient),
                )
            assert fetch.call_count == MAX_BACKFILL_DAYS

    async def test_clamps_negative_to_zero(self):
        async with test_session_maker() as session:
            user = _user()
            session.add(user)
            await session.flush()
            with _patch_fetch([]) as fetch:
                await backfill_fatsecret(
                    session, user, num_days=-5,
                    http=MagicMock(spec=httpx.AsyncClient),
                )
            assert fetch.call_count == 0
