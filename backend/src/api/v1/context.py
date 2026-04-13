"""GET /api/v1/context — user profile context (height, DOB, device info)."""

from fastapi import APIRouter, Depends

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import query_user_context

router = APIRouter(prefix="/context", tags=["context"])


@router.get("")
async def get_context(
    source: str | None = None,
    auth: AuthResult = Depends(require_scope("read:vitals")),
    session=Depends(get_async_session),
):
    rows = await query_user_context(session, auth.user.id, source=source)
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}
