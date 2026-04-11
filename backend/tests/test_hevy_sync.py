"""Tests for hevy_sync — Hevy data sync and disconnect."""

import uuid
from datetime import date
from unittest.mock import patch

import pytest
from sqlalchemy import select

from src.models.db_models import FitnessMetric, User
from src.services.hevy.sync import disconnect_hevy, sync_hevy_data
from src.services.token_encryption import encrypt_token

from tests.conftest import test_session_maker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_user(**overrides) -> User:
    defaults = {
        "id": uuid.uuid4(),
        "email": "hevy-user@test.com",
        "hashed_password": "hashed",
        "hevy_api_key": encrypt_token("test-hevy-api-key"),
    }
    defaults.update(overrides)
    return User(**defaults)


# ---------------------------------------------------------------------------
# sync_hevy_data
# ---------------------------------------------------------------------------
class TestSyncHevyData:
    @pytest.mark.asyncio
    async def test_connected_user_syncs_metrics(self):
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            hevy_result = {
                "data": {
                    "workout": {
                        "title": "Push Day",
                        "duration_minutes": 60,
                        "total_volume_kg": 5000,
                        "total_sets": 15,
                        "total_reps": 120,
                        "exercises": [],
                        "muscle_groups": {"chest": 9, "triceps": 6},
                    }
                },
                "errors": [],
            }

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                return_value=hevy_result,
            ):
                result = await sync_hevy_data(session, user, date(2026, 4, 7))

            await session.commit()

            assert len(result["synced_metrics"]) == 1
            assert "workout" in result["synced_metrics"][0]
            assert result["errors"] == []

            # Verify DB
            stmt = select(FitnessMetric).where(FitnessMetric.user_id == user.id)
            metrics = (await session.execute(stmt)).scalars().all()
            assert len(metrics) == 1
            assert metrics[0].source == "hevy"
            assert metrics[0].metric_type == "workout"
            assert metrics[0].data["total_volume_kg"] == 5000

    @pytest.mark.asyncio
    async def test_disconnected_user_returns_error(self):
        async with test_session_maker() as session:
            user = _make_user(hevy_api_key=None)
            session.add(user)
            await session.flush()

            result = await sync_hevy_data(session, user, date(2026, 4, 7))

            assert result["synced_metrics"] == []
            assert "Hevy not connected" in result["errors"]

    @pytest.mark.asyncio
    async def test_no_workout_returns_empty(self):
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                return_value={"data": {}, "errors": []},
            ):
                result = await sync_hevy_data(session, user, date(2026, 4, 7))

            assert result["synced_metrics"] == []
            assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_exception_caught(self):
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                side_effect=RuntimeError("boom"),
            ):
                result = await sync_hevy_data(session, user, date(2026, 4, 7))

            assert result["synced_metrics"] == []
            assert any("hevy" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_upstream_errors_propagated(self):
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            hevy_result = {
                "data": {"workout": {"title": "Test", "total_volume_kg": 100, "total_sets": 1, "total_reps": 5,
                                       "duration_minutes": 30, "exercises": [], "muscle_groups": {}}},
                "errors": ["hevy: partial failure"],
            }

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                return_value=hevy_result,
            ):
                result = await sync_hevy_data(session, user, date(2026, 4, 7))

            assert len(result["synced_metrics"]) == 1
            assert "hevy: partial failure" in result["errors"]


# ---------------------------------------------------------------------------
# disconnect_hevy
# ---------------------------------------------------------------------------
class TestDisconnectHevy:
    def test_clears_api_key(self):
        user = _make_user()
        assert user.hevy_api_key is not None

        disconnect_hevy(user)

        assert user.hevy_api_key is None

    def test_idempotent(self):
        user = _make_user(hevy_api_key=None)
        disconnect_hevy(user)
        assert user.hevy_api_key is None
