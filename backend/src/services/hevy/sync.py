"""Hevy sync pipeline — typed tables for workouts, exercises, routines."""

import logging
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import User
from src.models.hevy_models import Workout
from src.services.hevy.client import get_workouts_for_date
from src.services.hevy.routines import get_all_routines
from src.services.hevy_sync_utils import (
    delete_and_insert_exercises,
    upsert_routine,
    upsert_workout,
)

logger = logging.getLogger(__name__)


async def sync_hevy_workouts(
    session: AsyncSession, user: User, sync_date: date,
    api_key: str, hevy_client=None, template_cache: dict | None = None,
) -> list[str]:
    """Sync Hevy workouts + exercises into typed tables for a single date."""
    errors = []

    result = await get_workouts_for_date(api_key, sync_date, hevy_client, template_cache)
    errors.extend(result.get("errors", []))
    workout_dicts = result.get("data", [])

    synced_external_ids = set()
    for wd in workout_dicts:
        external_id = wd.pop("external_id", "")
        if not external_id:
            continue
        exercises = wd.pop("exercises", [])

        # Parse datetimes
        for dt_field in ("started_at", "ended_at"):
            val = wd.get(dt_field)
            if isinstance(val, str):
                try:
                    wd[dt_field] = datetime.fromisoformat(val)
                except (ValueError, TypeError):
                    wd[dt_field] = None

        workout_id = await upsert_workout(
            session, user.id, external_id, "hevy",
            date=sync_date, **wd,
        )
        await delete_and_insert_exercises(session, workout_id, exercises)
        synced_external_ids.add(external_id)

    # Soft-delete reconciliation: mark workouts missing from API for this date.
    # Known limitation: only detects deletions within the synced date range (last 2 days).
    # Older deletions require the event-feed endpoint (GET /v1/workouts/events).
    stored = (await session.execute(
        select(Workout).where(
            Workout.user_id == user.id,
            Workout.date == sync_date,
            Workout.source == "hevy",
            Workout.deleted_at.is_(None),
        )
    )).scalars().all()
    for w in stored:
        if w.external_id not in synced_external_ids:
            w.deleted_at = datetime.now(timezone.utc)

    return errors


async def sync_hevy_routines(
    session: AsyncSession, user: User, api_key: str,
) -> list[str]:
    """Sync all Hevy routines into typed table."""
    errors = []

    routine_dicts = await get_all_routines(api_key)
    for rd in routine_dicts:
        external_id = rd.pop("external_id", "")
        if not external_id:
            continue
        await upsert_routine(session, user.id, external_id, "hevy", **rd)

    return errors


def disconnect_hevy(user: User) -> None:
    """Clear Hevy API key from user."""
    user.hevy_api_key = None
