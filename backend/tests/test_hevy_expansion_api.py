"""Tests for Hevy typed table query + serialization layer."""

import uuid
from datetime import date, datetime, timezone

import pytest

from src.models.hevy_models import Routine, Workout, WorkoutExercise
from src.services.data_service import (
    query_routines,
    query_workout_by_external_id,
    query_workout_exercises,
    query_workouts,
)
from tests.conftest import test_session_maker

USER_ID = uuid.uuid4()


@pytest.mark.asyncio
class TestQueryWorkouts:
    async def test_excludes_soft_deleted(self):
        async with test_session_maker() as session:
            session.add(Workout(user_id=USER_ID, date=date(2026, 4, 10),
                                source="hevy", external_id="w1", title="Active"))
            session.add(Workout(user_id=USER_ID, date=date(2026, 4, 10),
                                source="hevy", external_id="w2", title="Deleted",
                                deleted_at=datetime.now(timezone.utc)))
            await session.commit()
            rows = await query_workouts(session, USER_ID)
            assert len(rows) == 1
            assert rows[0].title == "Active"

    async def test_to_dict_no_deleted_at(self):
        async with test_session_maker() as session:
            session.add(Workout(user_id=USER_ID, date=date(2026, 4, 10),
                                source="hevy", external_id="w1", title="Push",
                                total_volume_kg=5000.0))
            await session.commit()
            rows = await query_workouts(session, USER_ID)
            d = rows[0].to_dict()
            assert d["title"] == "Push"
            assert "deleted_at" not in d


@pytest.mark.asyncio
class TestQueryWorkoutExercises:
    async def test_ordered_by_index(self):
        async with test_session_maker() as session:
            w = Workout(user_id=USER_ID, date=date(2026, 4, 10),
                        source="hevy", external_id="w1")
            session.add(w)
            await session.commit()
            await session.refresh(w)
            session.add(WorkoutExercise(workout_id=w.id, exercise_index=1,
                                        title="OHP", volume_kg=400))
            session.add(WorkoutExercise(workout_id=w.id, exercise_index=0,
                                        title="Bench", volume_kg=800))
            await session.commit()
            exercises = await query_workout_exercises(session, w.id)
            assert exercises[0].title == "Bench"
            assert exercises[1].title == "OHP"


@pytest.mark.asyncio
class TestQueryWorkoutByExternalId:
    async def test_finds_by_external_id(self):
        async with test_session_maker() as session:
            session.add(Workout(user_id=USER_ID, date=date(2026, 4, 10),
                                source="hevy", external_id="ext123", title="Legs"))
            await session.commit()
            result = await query_workout_by_external_id(session, USER_ID, "ext123")
            assert result is not None
            assert result.title == "Legs"

    async def test_returns_none_for_missing(self):
        async with test_session_maker() as session:
            result = await query_workout_by_external_id(session, USER_ID, "nope")
            assert result is None

    async def test_excludes_soft_deleted(self):
        async with test_session_maker() as session:
            session.add(Workout(user_id=USER_ID, date=date(2026, 4, 10),
                                source="hevy", external_id="del1", title="Deleted",
                                deleted_at=datetime.now(timezone.utc)))
            await session.commit()
            result = await query_workout_by_external_id(session, USER_ID, "del1")
            assert result is None


@pytest.mark.asyncio
class TestQueryRoutines:
    async def test_basic_query(self):
        async with test_session_maker() as session:
            session.add(Routine(user_id=USER_ID, source="hevy",
                                external_id="r1", title="PPL Push",
                                exercises=[{"title": "Bench"}]))
            await session.commit()
            rows = await query_routines(session, USER_ID)
            assert len(rows) == 1
            d = rows[0].to_dict()
            assert d["title"] == "PPL Push"
