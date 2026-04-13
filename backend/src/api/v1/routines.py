"""GET /api/v1/routines — workout routine templates."""

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import query_routines

router = APIRouter(prefix="/routines", tags=["routines"])


@router.get("")
async def get_routines(
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    auth: AuthResult = Depends(require_scope("read:workouts")),
    session=Depends(get_async_session),
):
    rows = await query_routines(session, auth.user.id, limit=limit, offset=offset)
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}
