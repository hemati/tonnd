"""Tests for hevy sync — typed table pipeline and disconnect."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from src.models.db_models import User
from src.models.hevy_models import Routine, Workout, WorkoutExercise
from src.services.hevy.sync import (
    disconnect_hevy,
    sync_hevy_routines,
    sync_hevy_workouts,
)
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


def _mock_workout_data():
    return {
        "data": [
            {
                "external_id": "w1",
                "title": "Push Day",
                "description": "Good session",
                "started_at": "2026-04-10T07:00:00+00:00",
                "ended_at": "2026-04-10T08:00:00+00:00",
                "duration_minutes": 60,
                "total_volume_kg": 5000.0,
                "total_sets": 15,
                "total_reps": 120,
                "muscle_groups": {"chest": 4.0, "triceps": 1.6},
                "exercises": [
                    {
                        "exercise_index": 0,
                        "title": "Bench Press",
                        "external_exercise_id": "t1",
                        "exercise_type": "weight_reps",
                        "is_custom": False,
                        "supersets_id": None,
                        "notes": None,
                        "volume_kg": 2560.0,
                        "primary_muscle": "chest",
                        "secondary_muscles": ["triceps"],
                        "sets": [{"type": "normal", "weight_kg": 80, "reps": 8}],
                    },
                ],
            },
        ],
        "errors": [],
    }


# ---------------------------------------------------------------------------
# sync_hevy_workouts
# ---------------------------------------------------------------------------
class TestSyncHevyWorkouts:
    @pytest.mark.asyncio
    async def test_workouts_land_in_typed_tables(self):
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value=_mock_workout_data(),
            ):
                errors = await sync_hevy_workouts(
                    session, user, date(2026, 4, 10), "test-key"
                )

            await session.flush()

            assert errors == []

            # Verify workout row
            workouts = (
                await session.execute(select(Workout).where(Workout.user_id == user.id))
            ).scalars().all()
            assert len(workouts) == 1
            assert workouts[0].title == "Push Day"
            assert workouts[0].total_volume_kg == 5000.0
            assert workouts[0].external_id == "w1"

            # Verify exercise rows
            exercises = (
                await session.execute(
                    select(WorkoutExercise).where(
                        WorkoutExercise.workout_id == workouts[0].id
                    )
                )
            ).scalars().all()
            assert len(exercises) == 1
            assert exercises[0].title == "Bench Press"
            assert exercises[0].primary_muscle == "chest"

    @pytest.mark.asyncio
    async def test_no_workouts_returns_empty(self):
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value={"data": [], "errors": []},
            ):
                errors = await sync_hevy_workouts(
                    session, user, date(2026, 4, 10), "test-key"
                )

            assert errors == []

    @pytest.mark.asyncio
    async def test_upstream_errors_propagated(self):
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value={"data": [], "errors": ["hevy: partial failure"]},
            ):
                errors = await sync_hevy_workouts(
                    session, user, date(2026, 4, 10), "test-key"
                )

            assert "hevy: partial failure" in errors

    @pytest.mark.asyncio
    async def test_soft_delete_reconciliation(self):
        """Workouts in DB but missing from API get deleted_at set."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            # Pre-insert a workout that will NOT appear in the API response
            old_workout = Workout(
                user_id=user.id,
                date=date(2026, 4, 10),
                source="hevy",
                external_id="old_w",
                title="Old Workout",
            )
            session.add(old_workout)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value=_mock_workout_data(),
            ):
                errors = await sync_hevy_workouts(
                    session, user, date(2026, 4, 10), "test-key"
                )

            await session.flush()

            assert errors == []

            # The old workout should be soft-deleted
            old = (
                await session.execute(
                    select(Workout).where(Workout.external_id == "old_w")
                )
            ).scalar_one()
            assert old.deleted_at is not None

            # The new workout should NOT be soft-deleted
            new = (
                await session.execute(
                    select(Workout).where(Workout.external_id == "w1")
                )
            ).scalar_one()
            assert new.deleted_at is None


# ---------------------------------------------------------------------------
# sync_hevy_routines
# ---------------------------------------------------------------------------
class TestSyncHevyRoutines:
    @pytest.mark.asyncio
    async def test_routines_land_in_typed_table(self):
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            mock_routines = [
                {
                    "external_id": "r1",
                    "title": "PPL Push",
                    "folder_id": 1,
                    "exercises": [{"title": "Bench Press", "sets": []}],
                },
            ]

            with patch(
                "src.services.hevy.sync.get_all_routines",
                new_callable=AsyncMock,
                return_value=mock_routines,
            ):
                errors = await sync_hevy_routines(session, user, "test-key")

            await session.flush()

            assert errors == []

            routines = (
                await session.execute(select(Routine).where(Routine.user_id == user.id))
            ).scalars().all()
            assert len(routines) == 1
            assert routines[0].title == "PPL Push"
            assert routines[0].external_id == "r1"

    @pytest.mark.asyncio
    async def test_empty_routines(self):
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_all_routines",
                new_callable=AsyncMock,
                return_value=[],
            ):
                errors = await sync_hevy_routines(session, user, "test-key")

            assert errors == []


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
