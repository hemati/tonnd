"""GET /api/v1/context — user profile context (height, DOB, device info)."""

from datetime import date as date_cls

from fastapi import APIRouter, Depends

from src.auth.dependencies import AuthResult, require_scope
from src.database import get_async_session
from src.services.data_service import query_user_context

router = APIRouter(prefix="/context", tags=["context"])


def _compute_age(dob):
    if not dob:
        return None
    today = date_cls.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


@router.get("")
async def get_context(
    source: str | None = None,
    auth: AuthResult = Depends(require_scope("read:vitals")),
    session=Depends(get_async_session),
):
    rows = await query_user_context(session, auth.user.id, source=source)
    return {
        "count": len(rows),
        "data": [
            {
                "source": r.source,
                "date_of_birth": r.date_of_birth.isoformat() if r.date_of_birth else None,
                "age": _compute_age(r.date_of_birth),
                "gender": r.gender,
                "height_cm": r.height_cm,
                "timezone": r.timezone,
                "utc_offset_ms": r.utc_offset_ms,
                "stride_length_walking": r.stride_length_walking,
                "stride_length_running": r.stride_length_running,
                "device_model": r.device_model,
                "device_battery": r.device_battery,
                "last_device_sync": r.last_device_sync.isoformat() if r.last_device_sync else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ],
    }
