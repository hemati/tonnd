"""GET /api/v1/recovery — computed recovery score."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import compute_recovery_score, get_latest

router = APIRouter()


@router.get("/recovery")
async def get_recovery(
    auth: AuthResult = Depends(require_scope("read:recovery")),
    session: AsyncSession = Depends(get_async_session),
):
    latest_hrv = await get_latest(session, auth.user.id, "hrv")
    latest_sleep = await get_latest(session, auth.user.id, "sleep")
    latest_hr = await get_latest(session, auth.user.id, "heart_rate")

    return compute_recovery_score(latest_hrv, latest_sleep, latest_hr)
