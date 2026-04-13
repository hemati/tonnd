"""GET /api/v1/sleep — sleep metrics from typed daily_sleep table."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import query_daily_sleep

router = APIRouter(prefix="/sleep", tags=["sleep"])


@router.get("")
async def get_sleep(
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    limit: int = Query(default=30, le=365),
    offset: int = 0,
    auth: AuthResult = Depends(require_scope("read:sleep")),
    session=Depends(get_async_session),
):
    rows = await query_daily_sleep(
        session, auth.user.id,
        start_date=start_date, end_date=end_date, source=source,
        limit=limit, offset=offset,
    )
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}
