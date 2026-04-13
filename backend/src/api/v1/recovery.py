"""GET /api/v1/recovery — computed recovery score."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import compute_recovery_score, query_daily_sleep, query_daily_vitals

router = APIRouter()


@router.get("/recovery")
async def get_recovery(
    auth: AuthResult = Depends(require_scope("read:recovery")),
    session: AsyncSession = Depends(get_async_session),
):
    vitals = await query_daily_vitals(session, auth.user.id, limit=1)
    sleeps = await query_daily_sleep(session, auth.user.id, limit=1)

    latest_hrv = {"daily_rmssd": vitals[0].daily_rmssd} if vitals else None
    latest_hr = {"resting_heart_rate": vitals[0].resting_heart_rate} if vitals else None
    latest_sleep = {"efficiency": sleeps[0].efficiency} if sleeps else None

    return compute_recovery_score(latest_hrv, latest_sleep, latest_hr)
