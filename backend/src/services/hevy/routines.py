"""Hevy routine fetching and parsing."""

import asyncio
import logging

from hevy_api import HevyClient
from hevy_api.models.model import Routine as HevyRoutine

logger = logging.getLogger(__name__)


def parse_routines(routines: list[HevyRoutine]) -> list[dict]:
    """Convert Hevy Routine objects to storage-ready dicts."""
    result = []
    for r in routines:
        exercises = []
        for ex in r.exercises:
            sets = [
                {
                    "type": s.type,
                    "weight_kg": s.weight_kg,
                    "reps": s.reps,
                    "rpe": s.rpe,
                    "distance_meters": s.distance_meters,
                    "duration_seconds": s.duration_seconds,
                }
                for s in ex.sets
            ]
            exercises.append(
                {
                    "title": ex.title,
                    "template_id": ex.exercise_template_id,
                    "supersets_id": ex.supersets_id,
                    "notes": ex.notes,
                    "rest_seconds": None,  # hevy-api library doesn't expose rest_seconds
                    "sets": sets,
                }
            )
        result.append(
            {
                "external_id": r.id,
                "title": r.title,
                "folder_id": r.folder_id,
                "exercises": exercises,
            }
        )
    return result


def _fetch_all_routines(api_key: str) -> list[HevyRoutine]:
    """Paginate through all routines."""
    client = HevyClient(api_key=api_key)
    routines = []
    page = 1
    while True:
        resp = client.get_routines(page_number=page, page_size=10)
        if not resp.routines:
            break
        routines.extend(resp.routines)
        if len(resp.routines) < 10:
            break
        page += 1
    return routines


async def get_all_routines(api_key: str) -> list[dict]:
    """Fetch and parse all routines."""
    try:
        raw = await asyncio.to_thread(_fetch_all_routines, api_key)
        return parse_routines(raw)
    except Exception as e:
        logger.error(f"Routine fetch failed: {e}")
        return []
