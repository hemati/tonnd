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


class HevyAPIError(Exception):
    pass


def _get_client(api_key: str) -> HevyClient:
    return HevyClient(api_key=api_key)


def _validate_api_key(api_key: str) -> bool:
    """Validate a Hevy API key by making a test request."""
    try:
        client = _get_client(api_key)
        response = client.get_workout_count()
        return response.is_success
    except Exception:
        return False


async def validate_hevy_api_key(api_key: str) -> bool:
    return await asyncio.to_thread(_validate_api_key, api_key)


def _fetch_workouts_for_date(api_key: str, target_date: date) -> list[Workout]:
    """Fetch all workouts for a specific date."""
    client = _get_client(api_key)
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


def _workout_to_metrics(workout: Workout) -> dict:
    """Convert a Hevy Workout into metric data dicts for storage."""
    exercises = []
    total_volume_kg = 0.0
    total_sets = 0
    total_reps = 0
    muscle_groups: dict[str, int] = {}

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

        exercises.append({
            "title": ex.title,
            "exercise_template_id": ex.exercise_template_id,
            "sets": ex_sets,
            "volume_kg": round(ex_volume, 1),
        })

        # Simple muscle group heuristic from exercise title
        title_lower = (ex.title or "").lower()
        group = _guess_muscle_group(title_lower)
        muscle_groups[group] = muscle_groups.get(group, 0) + len(ex.sets)

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


def _guess_muscle_group(title: str) -> str:
    """Best-effort muscle group from exercise name."""
    mappings = {
        "chest": ["bench press", "chest", "pec", "fly", "push-up", "pushup"],
        "back": ["row", "pull-up", "pullup", "lat ", "deadlift", "back"],
        "legs": ["squat", "leg", "lunge", "calf", "hamstring", "quad", "glute", "hip"],
        "shoulders": ["shoulder", "overhead press", "lateral raise", "delt", "ohp"],
        "biceps": ["bicep", "curl"],
        "triceps": ["tricep", "pushdown", "skull", "dip"],
        "core": ["ab ", "abs", "core", "plank", "crunch", "sit-up"],
        "cardio": ["run", "bike", "cardio", "treadmill", "elliptical"],
    }
    for group, keywords in mappings.items():
        if any(kw in title for kw in keywords):
            return group
    return "other"


async def get_workouts_for_date(api_key: str, target_date: date) -> dict:
    """
    Fetch and process Hevy workouts for a date.

    Returns: {"data": {"workout": {...}}, "errors": []}
    """
    result: dict = {"data": {}, "errors": []}

    try:
        workouts = await asyncio.to_thread(_fetch_workouts_for_date, api_key, target_date)

        if not workouts:
            return result

        # Merge all workouts for the day into one metric
        all_exercises = []
        total_volume = 0.0
        total_sets = 0
        total_reps = 0
        total_duration = 0
        muscle_groups: dict[str, int] = {}

        for w in workouts:
            metrics = _workout_to_metrics(w)
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

    except Exception as e:
        result["errors"].append(f"hevy: {e}")
        logger.error(f"Hevy fetch failed: {e}")

    return result
