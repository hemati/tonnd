"""GET /api/v1/intraday — hourly intraday summaries."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import query_hourly_intraday

router = APIRouter(prefix="/intraday", tags=["intraday"])


@router.get("")
async def get_intraday(
    metric_type: str = Query(..., description="heart_rate, hrv, spo2, steps, azm"),
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    start_hour: int | None = None,
    end_hour: int | None = None,
    limit: int = Query(default=200, le=500),
    offset: int = 0,
    auth: AuthResult = Depends(require_scope("read:vitals")),
    session=Depends(get_async_session),
):
    rows = await query_hourly_intraday(
        session, auth.user.id, metric_type,
        start_date=start_date, end_date=end_date, source=source,
        start_hour=start_hour, end_hour=end_hour,
        limit=limit, offset=offset,
    )
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}
