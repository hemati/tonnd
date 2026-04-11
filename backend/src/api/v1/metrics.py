"""GET /api/v1/metrics — all raw metrics (paginated, filterable)."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import AuthResult, get_auth
from src.auth.scopes import metric_types_for_scopes
from src.database import get_async_session
from src.services.data_service import metric_to_dict, query_metrics

router = APIRouter()


@router.get("/metrics")
async def get_all_metrics(
    auth: AuthResult = Depends(get_auth),
    session: AsyncSession = Depends(get_async_session),
    start_date: date | None = None,
    end_date: date | None = None,
    metric_type: str | None = None,
    source: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    # For PAT auth, restrict to scoped metric types
    allowed_types = None
    if auth.token is not None:
        allowed_types = list(metric_types_for_scopes(auth.token.scopes))
        if metric_type:
            if metric_type not in allowed_types:
                raise HTTPException(
                    status_code=403,
                    detail="Token does not have access to this metric type",
                )
            allowed_types = [metric_type]
    elif metric_type:
        allowed_types = [metric_type]

    rows = await query_metrics(
        session, auth.user.id,
        metric_types=allowed_types,
        start_date=start_date, end_date=end_date,
        source=source, limit=limit, offset=offset, order=order,
    )
    data = [metric_to_dict(r) for r in rows]
    return {"count": len(data), "data": data}
