"""GET /api/v1/body — body metrics from typed daily_body table."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import query_daily_body

router = APIRouter(prefix="/body", tags=["body"])


@router.get("")
async def get_body(
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    limit: int = Query(default=30, le=365),
    offset: int = 0,
    auth: AuthResult = Depends(require_scope("read:body")),
    session=Depends(get_async_session),
):
    rows = await query_daily_body(
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
                "weight_kg": r.weight_kg,
                "bmi": r.bmi,
                "body_fat_percent": r.body_fat_percent,
            }
            for r in rows
        ],
    }
