"""Tests for renpho_sync — Renpho data sync and disconnect."""

import uuid
from datetime import date
from unittest.mock import patch

import pytest
from sqlalchemy import select

from src.models.db_models import FitnessMetric, User
from src.services.renpho.client import RenphoAPIError
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


# ---------------------------------------------------------------------------
# sync_renpho_data
# ---------------------------------------------------------------------------
class TestSyncRenphoData:
    @pytest.mark.asyncio
    async def test_connected_user_syncs_metrics(self):
        """With a connected user and data, metrics get upserted."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            renpho_result = {
                "data": {
                    "weight": {"weight_kg": 78.5, "bmi": 24.0, "body_fat_percent": 18.0},
                    "body_composition": {"body_fat_percent": 18.0, "muscle_mass_percent": 40.0},
                },
                "errors": [],
            }

            with patch(
                "src.services.renpho.sync.get_measurements_for_date",
                return_value=renpho_result,
            ):
                result = await sync_renpho_data(session, user, date(2026, 4, 7))

            await session.commit()

            assert len(result["synced_metrics"]) == 2
            assert any("weight" in m for m in result["synced_metrics"])
            assert any("body_composition" in m for m in result["synced_metrics"])
            assert result["errors"] == []

            # Verify DB
            stmt = select(FitnessMetric).where(FitnessMetric.user_id == user.id)
            metrics = (await session.execute(stmt)).scalars().all()
            assert len(metrics) == 2
            assert all(m.source == "renpho" for m in metrics)

    @pytest.mark.asyncio
    async def test_disconnected_user_returns_error(self):
        """User without renpho_email gets an error, not a crash."""
        async with test_session_maker() as session:
            user = _make_user(renpho_email=None, renpho_session_key=None)
            session.add(user)
            await session.flush()

            result = await sync_renpho_data(session, user, date(2026, 4, 7))

            assert result["synced_metrics"] == []
            assert "Renpho not connected" in result["errors"]

    @pytest.mark.asyncio
    async def test_missing_session_key_returns_error(self):
        """User with email but no session_key is treated as disconnected."""
        async with test_session_maker() as session:
            user = _make_user(renpho_session_key=None)
            session.add(user)
            await session.flush()

            result = await sync_renpho_data(session, user, date(2026, 4, 7))

            assert "Renpho not connected" in result["errors"]

    @pytest.mark.asyncio
    async def test_renpho_api_error_caught(self):
        """RenphoAPIError is caught and added to errors."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.renpho.sync.get_measurements_for_date",
                side_effect=RenphoAPIError("auth failed"),
            ):
                result = await sync_renpho_data(session, user, date(2026, 4, 7))

            assert result["synced_metrics"] == []
            assert any("renpho" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_generic_exception_caught(self):
        """Any unexpected exception is caught and added to errors."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.renpho.sync.get_measurements_for_date",
                side_effect=RuntimeError("boom"),
            ):
                result = await sync_renpho_data(session, user, date(2026, 4, 7))

            assert result["synced_metrics"] == []
            assert len(result["errors"]) == 1

    @pytest.mark.asyncio
    async def test_upstream_errors_propagated(self):
        """Errors from get_measurements_for_date result are included."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            renpho_result = {
                "data": {"weight": {"weight_kg": 80}},
                "errors": ["renpho: partial failure"],
            }

            with patch(
                "src.services.renpho.sync.get_measurements_for_date",
                return_value=renpho_result,
            ):
                result = await sync_renpho_data(session, user, date(2026, 4, 7))

            assert len(result["synced_metrics"]) == 1
            assert "renpho: partial failure" in result["errors"]


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
