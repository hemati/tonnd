"""GET /api/v1/workouts — workout history from typed tables."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import (
    query_workout_by_external_id,
    query_workout_exercises,
    query_workouts,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


async def _workout_with_exercises(session, workout):
    d = workout.to_dict()
    exercises = await query_workout_exercises(session, workout.id)
    d["exercises"] = [e.to_dict() for e in exercises]
    return d


@router.get("")
async def get_workouts(
    auth: AuthResult = Depends(require_scope("read:workouts")),
    session: AsyncSession = Depends(get_async_session),
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    workouts = await query_workouts(
        session, auth.user.id,
        start_date=start_date, end_date=end_date,
        source=source, limit=limit, offset=offset, order=order,
    )
    data = [await _workout_with_exercises(session, w) for w in workouts]
    return {"count": len(data), "data": data}


@router.get("/{external_id}")
async def get_workout_by_id(
    external_id: str,
    auth: AuthResult = Depends(require_scope("read:workouts")),
    session: AsyncSession = Depends(get_async_session),
):
    workout = await query_workout_by_external_id(session, auth.user.id, external_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return await _workout_with_exercises(session, workout)
