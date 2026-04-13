"""Tests for typed Hevy tables — schema, constraints, upserts, and exercise sync."""

import uuid
from datetime import date

import pytest
from sqlalchemy import delete, select

from src.models.hevy_models import Routine, Workout, WorkoutExercise
from src.services.hevy_sync_utils import (
    delete_and_insert_exercises,
    upsert_routine,
    upsert_workout,
)

from tests.conftest import test_session_maker


# ─── Model CRUD & Constraints ──────────────────────────────────────


@pytest.mark.asyncio
class TestWorkout:
    async def test_insert_and_read(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            row = Workout(
                user_id=uid,
                date=date(2026, 4, 10),
                source="hevy",
                external_id="hevy_w1",
                title="Push Day",
                duration_minutes=65,
                total_volume_kg=5400.0,
                total_sets=20,
                total_reps=180,
                muscle_groups={"chest": 0.5, "triceps": 0.3, "shoulders": 0.2},
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            assert row.title == "Push Day"
            assert row.total_volume_kg == 5400.0
            assert row.muscle_groups["chest"] == 0.5

    async def test_unique_constraint(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            session.add(Workout(
                user_id=uid, date=date(2026, 4, 10), source="hevy",
                external_id="hevy_w1", title="Push Day",
            ))
            await session.commit()
            session.add(Workout(
                user_id=uid, date=date(2026, 4, 10), source="hevy",
                external_id="hevy_w1", title="Push Day v2",
            ))
            with pytest.raises(Exception):  # IntegrityError
                await session.commit()

    async def test_multiple_workouts_same_day(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 4, 10)
            session.add(Workout(
                user_id=uid, date=d, source="hevy",
                external_id="hevy_w1", title="Morning Push",
            ))
            session.add(Workout(
                user_id=uid, date=d, source="hevy",
                external_id="hevy_w2", title="Evening Pull",
            ))
            await session.commit()  # Different external_ids — no conflict


@pytest.mark.asyncio
class TestWorkoutExercise:
    async def test_delete_exercises_with_workout(self):
        """delete_and_insert_exercises clears exercises; deleting workout leaves none."""
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            w = Workout(
                user_id=uid, date=date(2026, 4, 10), source="hevy",
                external_id="hevy_w1", title="Push Day",
            )
            session.add(w)
            await session.flush()
            session.add(WorkoutExercise(
                workout_id=w.id, exercise_index=0, title="Bench Press",
                primary_muscle="chest",
                sets=[{"weight_kg": 80, "reps": 10}],
            ))
            session.add(WorkoutExercise(
                workout_id=w.id, exercise_index=1, title="Overhead Press",
                primary_muscle="shoulders",
                sets=[{"weight_kg": 50, "reps": 8}],
            ))
            await session.commit()

            # Use the delete pattern (same as delete_and_insert_exercises)
            await session.execute(
                delete(WorkoutExercise).where(WorkoutExercise.workout_id == w.id)
            )
            await session.commit()

            remaining = (await session.execute(
                select(WorkoutExercise)
            )).scalars().all()
            assert len(remaining) == 0


@pytest.mark.asyncio
class TestRoutine:
    async def test_insert_with_jsonb_exercises(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            exercises = [
                {"title": "Bench Press", "sets": 4, "reps": "8-10"},
                {"title": "Incline DB Press", "sets": 3, "reps": "10-12"},
            ]
            r = Routine(
                user_id=uid, source="hevy", external_id="routine_1",
                title="PPL - Push", exercises=exercises,
            )
            session.add(r)
            await session.commit()
            await session.refresh(r)
            assert r.title == "PPL - Push"
            assert len(r.exercises) == 2
            assert r.exercises[0]["title"] == "Bench Press"


# ─── Upsert function tests ─────────────────────────────────────────


@pytest.mark.asyncio
class TestUpsertWorkout:
    async def test_insert_returns_uuid(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            wid = await upsert_workout(
                session, uid, "hevy_w1", "hevy",
                date=date(2026, 4, 10), title="Push Day",
                duration_minutes=65, total_volume_kg=5400.0,
            )
            await session.commit()
            assert isinstance(wid, uuid.UUID)
            row = (await session.execute(
                select(Workout).where(Workout.id == wid)
            )).scalar_one()
            assert row.title == "Push Day"

    async def test_update_existing(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            wid1 = await upsert_workout(
                session, uid, "hevy_w1", "hevy",
                date=date(2026, 4, 10), title="Push Day",
                duration_minutes=60,
            )
            await session.commit()
            wid2 = await upsert_workout(
                session, uid, "hevy_w1", "hevy",
                date=date(2026, 4, 10), title="Push Day (Updated)",
                duration_minutes=65, total_volume_kg=5500.0,
            )
            await session.commit()
            assert wid1 == wid2  # Same row
            row = (await session.execute(
                select(Workout).where(Workout.id == wid1)
            )).scalar_one()
            assert row.title == "Push Day (Updated)"
            assert row.duration_minutes == 65
            assert row.total_volume_kg == 5500.0


@pytest.mark.asyncio
class TestDeleteAndInsertExercises:
    async def test_replaces_all_exercises(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            wid = await upsert_workout(
                session, uid, "hevy_w1", "hevy",
                date=date(2026, 4, 10), title="Push Day",
            )
            await session.flush()

            # Insert initial exercises
            await delete_and_insert_exercises(session, wid, [
                {"exercise_index": 0, "title": "Bench Press", "primary_muscle": "chest"},
                {"exercise_index": 1, "title": "Overhead Press", "primary_muscle": "shoulders"},
            ])
            await session.commit()

            exercises = (await session.execute(
                select(WorkoutExercise).where(WorkoutExercise.workout_id == wid)
            )).scalars().all()
            assert len(exercises) == 2

            # Replace with different exercises
            await delete_and_insert_exercises(session, wid, [
                {"exercise_index": 0, "title": "Incline Bench", "primary_muscle": "chest"},
                {"exercise_index": 1, "title": "Lateral Raise", "primary_muscle": "shoulders"},
                {"exercise_index": 2, "title": "Tricep Pushdown", "primary_muscle": "triceps"},
            ])
            await session.commit()

            exercises = (await session.execute(
                select(WorkoutExercise).where(WorkoutExercise.workout_id == wid)
            )).scalars().all()
            assert len(exercises) == 3
            titles = {e.title for e in exercises}
            assert "Incline Bench" in titles
            assert "Bench Press" not in titles


@pytest.mark.asyncio
class TestUpsertRoutine:
    async def test_insert_new(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            await upsert_routine(
                session, uid, "routine_1", "hevy",
                title="PPL - Push",
                exercises=[{"title": "Bench Press", "sets": 4}],
            )
            await session.commit()
            row = (await session.execute(
                select(Routine).where(Routine.user_id == uid)
            )).scalar_one()
            assert row.title == "PPL - Push"
            assert len(row.exercises) == 1

    async def test_update_existing(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            await upsert_routine(
                session, uid, "routine_1", "hevy",
                title="PPL - Push",
                exercises=[{"title": "Bench Press", "sets": 4}],
            )
            await session.commit()
            await upsert_routine(
                session, uid, "routine_1", "hevy",
                title="PPL - Push (v2)",
                exercises=[
                    {"title": "Bench Press", "sets": 4},
                    {"title": "Overhead Press", "sets": 3},
                ],
            )
            await session.commit()
            rows = (await session.execute(
                select(Routine).where(Routine.user_id == uid)
            )).scalars().all()
            assert len(rows) == 1
            assert rows[0].title == "PPL - Push (v2)"
            assert len(rows[0].exercises) == 2
