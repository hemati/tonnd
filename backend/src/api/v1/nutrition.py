"""GET /api/v1/nutrition/daily and /api/v1/nutrition/entries.

Two routes instead of `?detail=` so the response shape is unambiguous in
OpenAPI / generated clients. Both gated by the same `read:nutrition` scope.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import query_daily_nutrition, query_food_entries

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.get("/daily")
async def get_daily_nutrition(
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    limit: int = Query(default=30, le=365),
    offset: int = 0,
    auth: AuthResult = Depends(require_scope("read:nutrition")),
    session=Depends(get_async_session),
):
    rows = await query_daily_nutrition(
        session, auth.user.id,
        start_date=start_date, end_date=end_date, source=source,
        limit=limit, offset=offset,
    )
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}


@router.get("/entries")
async def get_food_entries(
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    meal: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    auth: AuthResult = Depends(require_scope("read:nutrition")),
    session=Depends(get_async_session),
):
    rows = await query_food_entries(
        session, auth.user.id,
        start_date=start_date, end_date=end_date,
        source=source, meal=meal,
        limit=limit, offset=offset,
    )
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}
