"""Tests for renpho_sync — Renpho data sync to body_measurements and disconnect."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import select

from src.models.body_models import BodyMeasurement
from src.models.db_models import User
from src.services.renpho.sync import disconnect_renpho, sync_renpho_data
from src.services.token_encryption import encrypt_token

from tests.conftest import test_session_maker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_user(**overrides) -> User:
    defaults = {
        "id": uuid.uuid4(),
        "email": "renpho-user@test.com",
        "hashed_password": "hashed",
        "renpho_email": encrypt_token("real@renpho.com"),
        "renpho_session_key": encrypt_token("renpho-password-123"),
    }
    defaults.update(overrides)
    return User(**defaults)


def _measurement(ts_hour: int = 10, weight: float = 78.5) -> dict:
    """Build a measurement dict matching the new client return format."""
    measured_at = datetime(2026, 4, 7, ts_hour, 0, 0, tzinfo=timezone.utc)
    return {
        "date": date(2026, 4, 7),
        "measured_at": measured_at,
        "weight_kg": weight,
        "bmi": 24.0,
        "body_fat_percent": 18.0,
        "body_water_percent": 55.0,
        "muscle_mass_percent": 40.0,
        "bone_mass_kg": 3.1,
        "bmr_kcal": 1650,
        "visceral_fat": 8,
        "subcutaneous_fat_percent": 12.0,
        "protein_percent": 18.0,
        "body_age": 28,
        "lean_body_mass_kg": 55.0,
        "fat_free_weight_kg": 62.0,
        "heart_rate": 68,
        "cardiac_index": 2.5,
        "body_shape": 3,
        "sport_flag": True,
    }


# ---------------------------------------------------------------------------
# sync_renpho_data
# ---------------------------------------------------------------------------
class TestSyncRenphoData:
    @pytest.mark.asyncio
    async def test_connected_user_syncs_to_body_measurements(self):
        """With a connected user and data, measurements land in body_measurements."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            renpho_result = {
                "data": [_measurement()],
                "errors": [],
            }

            with patch(
                "src.services.renpho.sync.get_measurements_for_date",
                return_value=renpho_result,
            ):
                result = await sync_renpho_data(session, user, date(2026, 4, 7))

            await session.commit()

            assert len(result["synced_metrics"]) == 1
            assert "body" in result["synced_metrics"][0]
            assert result["errors"] == []

            # Verify data in body_measurements table
            stmt = select(BodyMeasurement).where(BodyMeasurement.user_id == user.id)
            rows = (await session.execute(stmt)).scalars().all()
            assert len(rows) == 1
            assert rows[0].source == "renpho"
            assert rows[0].weight_kg == 78.5
            assert rows[0].bmi == 24.0
            assert rows[0].cardiac_index == 2.5
            assert rows[0].body_shape == 3
            assert rows[0].sport_flag is True

    @pytest.mark.asyncio
    async def test_two_measurements_same_day(self):
        """Two measurements for the same day produce two body_measurements rows."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            renpho_result = {
                "data": [_measurement(ts_hour=7, weight=80.0), _measurement(ts_hour=20, weight=80.5)],
                "errors": [],
            }

            with patch(
                "src.services.renpho.sync.get_measurements_for_date",
                return_value=renpho_result,
            ):
                result = await sync_renpho_data(session, user, date(2026, 4, 7))

            await session.commit()

            assert len(result["synced_metrics"]) == 2

            stmt = select(BodyMeasurement).where(BodyMeasurement.user_id == user.id)
            rows = (await session.execute(stmt)).scalars().all()
            assert len(rows) == 2
            weights = sorted(r.weight_kg for r in rows)
            assert weights == [80.0, 80.5]

    @pytest.mark.asyncio
    async def test_disconnected_user_returns_error(self):
        """User without renpho_email gets an error, not a crash."""
        async with test_session_maker() as session:
            user = _make_user(renpho_email=None, renpho_session_key=None)
            session.add(user)
            await session.flush()

            result = await sync_renpho_data(session, user, date(2026, 4, 7))

            assert result["synced_metrics"] == []
            assert "renpho: not connected" in result["errors"]

    @pytest.mark.asyncio
    async def test_missing_session_key_returns_error(self):
        """User with email but no session_key is treated as disconnected."""
        async with test_session_maker() as session:
            user = _make_user(renpho_session_key=None)
            session.add(user)
            await session.flush()

            result = await sync_renpho_data(session, user, date(2026, 4, 7))

            assert "renpho: not connected" in result["errors"]

    @pytest.mark.asyncio
    async def test_upstream_errors_propagated(self):
        """Errors from get_measurements_for_date result are included."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            renpho_result = {
                "data": [_measurement()],
                "errors": ["renpho: partial failure"],
            }

            with patch(
                "src.services.renpho.sync.get_measurements_for_date",
                return_value=renpho_result,
            ):
                result = await sync_renpho_data(session, user, date(2026, 4, 7))

            assert len(result["synced_metrics"]) == 1
            assert "renpho: partial failure" in result["errors"]

    @pytest.mark.asyncio
    async def test_empty_data_no_writes(self):
        """When client returns no data, nothing is written."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            renpho_result = {"data": [], "errors": []}

            with patch(
                "src.services.renpho.sync.get_measurements_for_date",
                return_value=renpho_result,
            ):
                result = await sync_renpho_data(session, user, date(2026, 4, 7))

            assert result["synced_metrics"] == []
            assert result["errors"] == []


# ---------------------------------------------------------------------------
# disconnect_renpho
# ---------------------------------------------------------------------------
class TestDisconnectRenpho:
    def test_clears_fields(self):
        user = _make_user()
        assert user.renpho_email is not None
        assert user.renpho_session_key is not None

        disconnect_renpho(user)

        assert user.renpho_email is None
        assert user.renpho_session_key is None

    def test_idempotent(self):
        user = _make_user(renpho_email=None, renpho_session_key=None)
        disconnect_renpho(user)
        assert user.renpho_email is None
        assert user.renpho_session_key is None
