"""Integration-style tests for the Hevy typed-table sync pipeline.

Tests that sync_hevy_workouts and sync_hevy_routines correctly distribute
data into the workouts, workout_exercises, and routines tables.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from src.models.db_models import User
from src.models.hevy_models import Routine, Workout, WorkoutExercise
from src.services.hevy.sync import sync_hevy_routines, sync_hevy_workouts
from src.services.token_encryption import encrypt_token

from tests.conftest import test_session_maker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_user(**kwargs) -> User:
    defaults = {
        "id": uuid.uuid4(),
        "email": "test@test.com",
        "hashed_password": "hashed",
        "hevy_api_key": encrypt_token("encrypted_key"),
    }
    defaults.update(kwargs)
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


def _mock_two_workouts():
    return {
        "data": [
            {
                "external_id": "w1",
                "title": "Push Day",
                "description": None,
                "started_at": "2026-04-10T07:00:00+00:00",
                "ended_at": "2026-04-10T08:00:00+00:00",
                "duration_minutes": 60,
                "total_volume_kg": 5000.0,
                "total_sets": 15,
                "total_reps": 120,
                "muscle_groups": {"chest": 4.0},
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
                        "secondary_muscles": [],
                        "sets": [{"type": "normal", "weight_kg": 80, "reps": 8}],
                    },
                ],
            },
            {
                "external_id": "w2",
                "title": "Pull Day",
                "description": None,
                "started_at": "2026-04-10T09:00:00+00:00",
                "ended_at": "2026-04-10T10:00:00+00:00",
                "duration_minutes": 60,
                "total_volume_kg": 4000.0,
                "total_sets": 12,
                "total_reps": 96,
                "muscle_groups": {"back": 4.0},
                "exercises": [
                    {
                        "exercise_index": 0,
                        "title": "Barbell Row",
                        "external_exercise_id": "t2",
                        "exercise_type": "weight_reps",
                        "is_custom": False,
                        "supersets_id": None,
                        "notes": None,
                        "volume_kg": 1600.0,
                        "primary_muscle": "back",
                        "secondary_muscles": ["biceps"],
                        "sets": [{"type": "normal", "weight_kg": 60, "reps": 10}],
                    },
                ],
            },
        ],
        "errors": [],
    }


# ---------------------------------------------------------------------------
# sync_hevy_workouts — data lands in workouts + workout_exercises tables
# ---------------------------------------------------------------------------
class TestSyncHevyWorkoutsPipeline:
    @pytest.mark.asyncio
    async def test_workout_and_exercises_inserted(self):
        """Single workout with exercises lands in both typed tables."""
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

            # Check workouts table
            workouts = (
                await session.execute(select(Workout).where(Workout.user_id == user.id))
            ).scalars().all()
            assert len(workouts) == 1
            w = workouts[0]
            assert w.external_id == "w1"
            assert w.title == "Push Day"
            assert w.total_volume_kg == 5000.0
            assert w.total_sets == 15
            assert w.total_reps == 120
            assert w.source == "hevy"
            assert w.date == date(2026, 4, 10)
            assert w.muscle_groups == {"chest": 4.0, "triceps": 1.6}
            assert w.deleted_at is None

            # Check workout_exercises table
            exercises = (
                await session.execute(
                    select(WorkoutExercise).where(WorkoutExercise.workout_id == w.id)
                )
            ).scalars().all()
            assert len(exercises) == 1
            ex = exercises[0]
            assert ex.title == "Bench Press"
            assert ex.exercise_index == 0
            assert ex.primary_muscle == "chest"
            assert ex.secondary_muscles == ["triceps"]
            assert ex.volume_kg == 2560.0
            assert ex.sets == [{"type": "normal", "weight_kg": 80, "reps": 8}]

    @pytest.mark.asyncio
    async def test_multiple_workouts_same_date(self):
        """Two workouts on the same date both get inserted."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value=_mock_two_workouts(),
            ):
                errors = await sync_hevy_workouts(
                    session, user, date(2026, 4, 10), "test-key"
                )

            await session.flush()
            assert errors == []

            workouts = (
                await session.execute(
                    select(Workout).where(Workout.user_id == user.id).order_by(Workout.external_id)
                )
            ).scalars().all()
            assert len(workouts) == 2
            assert workouts[0].title == "Push Day"
            assert workouts[1].title == "Pull Day"

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_workout(self):
        """Re-syncing the same workout updates fields rather than duplicating."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value=_mock_workout_data(),
            ):
                await sync_hevy_workouts(session, user, date(2026, 4, 10), "test-key")
            await session.flush()

            # Modify the mock data and sync again
            updated = _mock_workout_data()
            updated["data"][0]["title"] = "Push Day (Updated)"
            updated["data"][0]["total_volume_kg"] = 6000.0

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value=updated,
            ):
                await sync_hevy_workouts(session, user, date(2026, 4, 10), "test-key")
            await session.flush()

            workouts = (
                await session.execute(select(Workout).where(Workout.user_id == user.id))
            ).scalars().all()
            assert len(workouts) == 1
            assert workouts[0].title == "Push Day (Updated)"
            assert workouts[0].total_volume_kg == 6000.0

    @pytest.mark.asyncio
    async def test_datetime_strings_parsed(self):
        """started_at and ended_at strings are converted to datetime objects."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value=_mock_workout_data(),
            ):
                await sync_hevy_workouts(session, user, date(2026, 4, 10), "test-key")
            await session.flush()

            w = (
                await session.execute(select(Workout).where(Workout.user_id == user.id))
            ).scalar_one()
            assert w.started_at is not None
            assert w.ended_at is not None


# ---------------------------------------------------------------------------
# sync_hevy_workouts — soft-delete reconciliation
# ---------------------------------------------------------------------------
class TestSyncHevySoftDelete:
    @pytest.mark.asyncio
    async def test_missing_workout_gets_soft_deleted(self):
        """Workout in DB but not in API response gets deleted_at timestamp."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            # Pre-insert a workout that will be missing from the API
            stale = Workout(
                user_id=user.id,
                date=date(2026, 4, 10),
                source="hevy",
                external_id="stale_w",
                title="Stale Workout",
            )
            session.add(stale)
            await session.flush()

            # Sync returns different workout — stale_w is missing
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

            stale_row = (
                await session.execute(
                    select(Workout).where(Workout.external_id == "stale_w")
                )
            ).scalar_one()
            assert stale_row.deleted_at is not None

    @pytest.mark.asyncio
    async def test_synced_workout_not_soft_deleted(self):
        """Workout that appears in API response does NOT get deleted_at."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value=_mock_workout_data(),
            ):
                await sync_hevy_workouts(session, user, date(2026, 4, 10), "test-key")
            await session.flush()

            w = (
                await session.execute(
                    select(Workout).where(Workout.external_id == "w1")
                )
            ).scalar_one()
            assert w.deleted_at is None

    @pytest.mark.asyncio
    async def test_already_soft_deleted_not_affected(self):
        """Workout already soft-deleted is not touched again."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            past_ts = datetime(2026, 4, 8, 12, 0, 0, tzinfo=timezone.utc)
            already_deleted = Workout(
                user_id=user.id,
                date=date(2026, 4, 10),
                source="hevy",
                external_id="already_gone",
                title="Already Deleted",
                deleted_at=past_ts,
            )
            session.add(already_deleted)
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value={"data": [], "errors": []},
            ):
                await sync_hevy_workouts(session, user, date(2026, 4, 10), "test-key")
            await session.flush()

            row = (
                await session.execute(
                    select(Workout).where(Workout.external_id == "already_gone")
                )
            ).scalar_one()
            # deleted_at should remain as the original timestamp (not updated)
            # because the query filters for deleted_at.is_(None)
            assert row.deleted_at == past_ts

    @pytest.mark.asyncio
    async def test_empty_api_response_soft_deletes_all(self):
        """When API returns no workouts, all stored workouts for that date get soft-deleted."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            w1 = Workout(
                user_id=user.id, date=date(2026, 4, 10),
                source="hevy", external_id="w_a", title="A",
            )
            w2 = Workout(
                user_id=user.id, date=date(2026, 4, 10),
                source="hevy", external_id="w_b", title="B",
            )
            session.add_all([w1, w2])
            await session.flush()

            with patch(
                "src.services.hevy.sync.get_workouts_for_date",
                new_callable=AsyncMock,
                return_value={"data": [], "errors": []},
            ):
                await sync_hevy_workouts(session, user, date(2026, 4, 10), "test-key")
            await session.flush()

            stored = (
                await session.execute(
                    select(Workout).where(Workout.user_id == user.id)
                )
            ).scalars().all()
            assert all(w.deleted_at is not None for w in stored)


# ---------------------------------------------------------------------------
# sync_hevy_routines — data lands in routines table
# ---------------------------------------------------------------------------
class TestSyncHevyRoutinesPipeline:
    @pytest.mark.asyncio
    async def test_routines_inserted(self):
        """Routines from API land in the routines table."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            mock_routines = [
                {
                    "external_id": "r1",
                    "title": "PPL Push",
                    "folder_id": 1,
                    "exercises": [
                        {"title": "Bench Press", "sets": [{"type": "normal", "weight_kg": 80, "reps": 8}]},
                    ],
                },
                {
                    "external_id": "r2",
                    "title": "PPL Pull",
                    "folder_id": 1,
                    "exercises": [
                        {"title": "Barbell Row", "sets": [{"type": "normal", "weight_kg": 60, "reps": 10}]},
                    ],
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
                await session.execute(
                    select(Routine).where(Routine.user_id == user.id).order_by(Routine.external_id)
                )
            ).scalars().all()
            assert len(routines) == 2
            assert routines[0].title == "PPL Push"
            assert routines[0].external_id == "r1"
            assert routines[1].title == "PPL Pull"
            assert routines[1].external_id == "r2"

    @pytest.mark.asyncio
    async def test_routine_upsert_updates_existing(self):
        """Re-syncing updates existing routine instead of duplicating."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            initial = [
                {"external_id": "r1", "title": "Push A", "folder_id": 1, "exercises": []},
            ]
            with patch(
                "src.services.hevy.sync.get_all_routines",
                new_callable=AsyncMock,
                return_value=initial,
            ):
                await sync_hevy_routines(session, user, "test-key")
            await session.flush()

            updated = [
                {"external_id": "r1", "title": "Push A (v2)", "folder_id": 2, "exercises": [{"title": "OHP"}]},
            ]
            with patch(
                "src.services.hevy.sync.get_all_routines",
                new_callable=AsyncMock,
                return_value=updated,
            ):
                await sync_hevy_routines(session, user, "test-key")
            await session.flush()

            routines = (
                await session.execute(select(Routine).where(Routine.user_id == user.id))
            ).scalars().all()
            assert len(routines) == 1
            assert routines[0].title == "Push A (v2)"

    @pytest.mark.asyncio
    async def test_empty_routines(self):
        """Empty routine list from API produces no errors and no rows."""
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

            count = (
                await session.execute(select(Routine).where(Routine.user_id == user.id))
            ).scalars().all()
            assert len(count) == 0

    @pytest.mark.asyncio
    async def test_routine_without_external_id_skipped(self):
        """Routines missing external_id are silently skipped."""
        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            mock_routines = [
                {"external_id": "", "title": "No ID", "folder_id": None, "exercises": []},
                {"external_id": "r1", "title": "Valid", "folder_id": None, "exercises": []},
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
            assert routines[0].external_id == "r1"
