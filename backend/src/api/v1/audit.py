"""GET /api/v1/audit — user's own audit trail (JWT auth only)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.models.api_models import AuditLog
from src.models.db_models import User
from src.schemas.api_schemas import AuditEntry, AuditListResponse
from src.services.user_service import current_active_user

router = APIRouter()


@router.get("/audit", response_model=AuditListResponse)
async def get_audit_log(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    stmt = (
        select(AuditLog)
        .where(AuditLog.user_id == user.id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()

    count_stmt = (
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.user_id == user.id)
    )
    total = (await session.execute(count_stmt)).scalar() or 0

    return AuditListResponse(
        count=total,
        data=[
            AuditEntry(
                id=r.id,
                action=r.action,
                resource=r.resource,
                method=r.method,
                ip_address=r.ip_address,
                status_code=r.status_code,
                created_at=r.created_at,
            )
            for r in rows
        ],
    )
