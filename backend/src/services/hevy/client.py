"""
Hevy workout tracking client.

Uses the remuzel/hevy-api library (sync). Wrapped with asyncio.to_thread()
for async compatibility in FastAPI.
"""

import asyncio
import logging
from datetime import date, datetime, timezone

from hevy_api.client import HevyClient
from hevy_api.models.model import Workout

logger = logging.getLogger(__name__)

SECONDARY_MUSCLE_WEIGHT = 0.4
UNKNOWN_MUSCLE_GROUP = "other"


class HevyAPIError(Exception):
    pass


def get_client(api_key: str) -> HevyClient:
    return HevyClient(api_key=api_key)


def _validate_api_key(api_key: str) -> bool:
    """Validate a Hevy API key by making a test request."""
    try:
        client = get_client(api_key)
        response = client.get_workout_count()
        return response.is_success
    except Exception:
        return False


async def validate_hevy_api_key(api_key: str) -> bool:
    return await asyncio.to_thread(_validate_api_key, api_key)


def _fetch_workouts_for_date(api_key: str, target_date: date) -> list[Workout]:
    """Fetch all workouts for a specific date."""
    client = get_client(api_key)
    matching = []
    page = 1

    while True:
        response = client.get_workouts(page_number=page, page_size=10)
        if not response.is_success or not response.workouts:
            break

        for w in response.workouts:
            w_date = w.start_time.date() if isinstance(w.start_time, datetime) else w.start_time
            if w_date == target_date:
                matching.append(w)
            elif w_date < target_date:
                # Workouts are ordered newest-first, stop if we've passed the date
                return matching

        page += 1
        if page > 50:  # safety limit
            break

    return matching


def _fetch_template_muscles(client: HevyClient, template_id: str, cache: dict) -> tuple[str, list[str]]:
    """Get primary + secondary muscle groups for an exercise template. Uses cache."""
    if template_id in cache:
        return cache[template_id]

    try:
        resp = client.get_exercise_template(template_id)
        t = resp.exercise_template
        primary = t.primary_muscle_group or UNKNOWN_MUSCLE_GROUP
        secondary = list(t.secondary_muscle_groups or [])
        cache[template_id] = (primary, secondary)
        return primary, secondary
    except Exception:
        cache[template_id] = (UNKNOWN_MUSCLE_GROUP, [])
        return UNKNOWN_MUSCLE_GROUP, []


def _workout_to_metrics(workout: Workout, template_cache: dict, hevy_client: HevyClient) -> dict:
    """Convert a Hevy Workout into metric data dicts for storage."""
    exercises: list[dict] = []
    total_volume_kg = 0.0
    total_sets = 0
    total_reps = 0
    muscle_groups: dict[str, float] = {}

    for ex in workout.exercises:
        ex_sets = []
        ex_volume = 0.0

        for s in ex.sets:
            weight = s.weight_kg or 0
            reps = s.reps or 0
            volume = weight * reps
            ex_volume += volume
            total_sets += 1
            total_reps += reps

            ex_sets.append({
                "type": s.type,
                "weight_kg": weight,
                "reps": reps,
                "rpe": s.rpe,
                "distance_meters": s.distance_meters,
                "duration_seconds": s.duration_seconds,
            })

        total_volume_kg += ex_volume

        primary, secondary = _fetch_template_muscles(hevy_client, ex.exercise_template_id, template_cache)

        exercises.append({
            "title": ex.title,
            "exercise_template_id": ex.exercise_template_id,
            "sets": ex_sets,
            "volume_kg": round(ex_volume, 1),
            "primary_muscle": primary,
            "secondary_muscles": secondary,
        })

        n_sets = len(ex.sets)
        muscle_groups[primary] = muscle_groups.get(primary, 0) + n_sets
        for sec in secondary:
            muscle_groups[sec] = round(muscle_groups.get(sec, 0) + n_sets * SECONDARY_MUSCLE_WEIGHT, 1)

    duration_minutes = 0
    if workout.start_time and workout.end_time:
        start = workout.start_time if isinstance(workout.start_time, datetime) else datetime.fromisoformat(str(workout.start_time))
        end = workout.end_time if isinstance(workout.end_time, datetime) else datetime.fromisoformat(str(workout.end_time))
        duration_minutes = int((end - start).total_seconds() / 60)

    return {
        "workout": {
            "title": workout.title,
            "duration_minutes": duration_minutes,
            "total_volume_kg": round(total_volume_kg, 1),
            "total_sets": total_sets,
            "total_reps": total_reps,
            "exercises": exercises,
            "muscle_groups": muscle_groups,
        }
    }



def _process_workouts(
    api_key: str,
    target_date: date,
    hevy_client: HevyClient | None = None,
    template_cache: dict | None = None,
) -> dict:
    """Fetch workouts for a date, enrich with template muscle data. Runs in thread."""
    result: dict = {"data": {}, "errors": []}

    workouts = _fetch_workouts_for_date(api_key, target_date)
    if not workouts:
        return result

    if hevy_client is None:
        hevy_client = get_client(api_key)
    if template_cache is None:
        template_cache = {}

    all_exercises = []
    total_volume = 0.0
    total_sets = 0
    total_reps = 0
    total_duration = 0
    muscle_groups: dict[str, float] = {}

    for w in workouts:
        metrics = _workout_to_metrics(w, template_cache, hevy_client)
        wd = metrics["workout"]
        all_exercises.extend(wd["exercises"])
        total_volume += wd["total_volume_kg"]
        total_sets += wd["total_sets"]
        total_reps += wd["total_reps"]
        total_duration += wd["duration_minutes"]
        for group, sets in wd["muscle_groups"].items():
            muscle_groups[group] = muscle_groups.get(group, 0) + sets

    result["data"]["workout"] = {
        "workout_count": len(workouts),
        "title": workouts[0].title if len(workouts) == 1 else f"{len(workouts)} workouts",
        "duration_minutes": total_duration,
        "total_volume_kg": round(total_volume, 1),
        "total_sets": total_sets,
        "total_reps": total_reps,
        "exercises": all_exercises,
        "muscle_groups": muscle_groups,
    }

    return result


async def get_workouts_for_date(
    api_key: str,
    target_date: date,
    hevy_client: HevyClient | None = None,
    template_cache: dict | None = None,
) -> dict:
    """Fetch and process Hevy workouts for a date."""
    try:
        return await asyncio.to_thread(_process_workouts, api_key, target_date, hevy_client, template_cache)
    except Exception as e:
        logger.error(f"Hevy fetch failed: {e}")
        return {"data": {}, "errors": [f"hevy: {e}"]}
