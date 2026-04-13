"""Upsert functions for Hevy typed tables."""

import uuid as uuid_mod

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.hevy_models import Routine, Workout, WorkoutExercise
from src.services.sync_utils import _upsert


async def upsert_workout(
    session: AsyncSession, user_id, external_id: str, source: str, **fields
) -> uuid_mod.UUID:
    """Upsert a workout and return its UUID (needed for exercise insertion)."""
    row = await _upsert(session, Workout,
                        {"user_id": user_id, "external_id": external_id, "source": source}, fields)
    await session.flush()
    return row.id


async def delete_and_insert_exercises(
    session: AsyncSession, workout_id: uuid_mod.UUID, exercises: list[dict],
) -> None:
    """Delete all exercises for a workout, then insert fresh ones."""
    await session.execute(
        delete(WorkoutExercise).where(WorkoutExercise.workout_id == workout_id)
    )
    for ex in exercises:
        session.add(WorkoutExercise(workout_id=workout_id, **ex))


async def upsert_routine(
    session: AsyncSession, user_id, external_id: str, source: str, **fields
) -> None:
    await _upsert(session, Routine,
                  {"user_id": user_id, "external_id": external_id, "source": source}, fields)
