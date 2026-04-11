"""GET /api/v1/body — weight, body_composition."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import AuthResult, require_scope
from src.auth.scopes import SCOPE_METRICS
from src.database import get_async_session
from src.services.data_service import metric_to_dict, query_metrics

router = APIRouter()

BODY_TYPES = SCOPE_METRICS["read:body"]


@router.get("/body")
async def get_body(
    auth: AuthResult = Depends(require_scope("read:body")),
    session: AsyncSession = Depends(get_async_session),
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    rows = await query_metrics(
        session, auth.user.id,
        metric_types=BODY_TYPES,
        start_date=start_date, end_date=end_date,
        source=source, limit=limit, offset=offset, order=order,
    )
    data = [metric_to_dict(r) for r in rows]
    return {"count": len(data), "data": data}


@router.get("/body/{metric_type}")
async def get_body_by_type(
    metric_type: str,
    auth: AuthResult = Depends(require_scope("read:body")),
    session: AsyncSession = Depends(get_async_session),
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    if metric_type not in BODY_TYPES:
        raise HTTPException(status_code=404, detail="Unknown body metric type")

    rows = await query_metrics(
        session, auth.user.id,
        metric_types=[metric_type],
        start_date=start_date, end_date=end_date,
        source=source, limit=limit, offset=offset, order=order,
    )
    data = [metric_to_dict(r) for r in rows]
    return {"metric_type": metric_type, "count": len(data), "data": data}
