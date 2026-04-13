"""GET /api/v1/vitals — vital signs from typed daily_vitals table."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import query_daily_vitals

router = APIRouter(prefix="/vitals", tags=["vitals"])


@router.get("")
async def get_vitals(
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    limit: int = Query(default=30, le=365),
    offset: int = 0,
    auth: AuthResult = Depends(require_scope("read:vitals")),
    session=Depends(get_async_session),
):
    rows = await query_daily_vitals(
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
                "resting_heart_rate": r.resting_heart_rate,
                "hr_zones": r.hr_zones,
                "daily_rmssd": r.daily_rmssd,
                "deep_rmssd": r.deep_rmssd,
                "spo2_avg": r.spo2_avg,
                "spo2_min": r.spo2_min,
                "spo2_max": r.spo2_max,
                "breathing_rate": r.breathing_rate,
                "vo2_max": r.vo2_max,
                "temp_relative_deviation": r.temp_relative_deviation,
            }
            for r in rows
        ],
    }
