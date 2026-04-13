"""GET /api/v1/exercises — exercise logs from typed exercise_logs table."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import query_exercise_logs

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("")
async def get_exercises(
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    limit: int = Query(default=30, le=365),
    offset: int = 0,
    auth: AuthResult = Depends(require_scope("read:activity")),
    session=Depends(get_async_session),
):
    rows = await query_exercise_logs(
        session, auth.user.id,
        start_date=start_date, end_date=end_date, source=source,
        limit=limit, offset=offset,
    )
    return {
        "count": len(rows),
        "data": [
            {
                "date": r.date.isoformat(),
                "source": r.source,
                "external_id": r.external_id,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                "activity_name": r.activity_name,
                "duration_minutes": r.duration_minutes,
                "avg_heart_rate": r.avg_heart_rate,
                "calories": r.calories,
                "distance_km": r.distance_km,
                "elevation_gain": r.elevation_gain,
                "speed_kmh": r.speed_kmh,
                "log_type": r.log_type,
                "hr_zones": r.hr_zones,
            }
            for r in rows
        ],
    }
