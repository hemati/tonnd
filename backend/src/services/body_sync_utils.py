"""Upsert function for body_measurements table."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.body_models import BodyMeasurement
from src.services.sync_utils import _upsert


async def upsert_body_measurement(
    session: AsyncSession, user_id, source: str, measured_at: datetime, **fields
) -> None:
    await _upsert(session, BodyMeasurement,
                  {"user_id": user_id, "source": source, "measured_at": measured_at}, fields)
