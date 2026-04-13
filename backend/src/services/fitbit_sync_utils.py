"""Typed upsert functions for Fitbit expansion tables.

Partial syncs (e.g., activity without AZM) don't overwrite each other
because each upsert only sets fields with non-None values.
"""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.fitbit_models import (
    DailyActivity,
    DailyBody,
    DailySleep,
    DailyVitals,
    ExerciseLog,
    HourlyIntraday,
    UserContext,
)
from src.services.sync_utils import _upsert


async def upsert_daily_vitals(
    session: AsyncSession, user_id, d: date, source: str, **fields
) -> None:
    await _upsert(session, DailyVitals,
                  {"user_id": user_id, "date": d, "source": source}, fields)


async def upsert_daily_sleep(
    session: AsyncSession, user_id, external_id: str, source: str, **fields
) -> None:
    await _upsert(session, DailySleep,
                  {"user_id": user_id, "source": source, "external_id": external_id}, fields)


async def upsert_daily_activity(
    session: AsyncSession, user_id, d: date, source: str, **fields
) -> None:
    await _upsert(session, DailyActivity,
                  {"user_id": user_id, "date": d, "source": source}, fields)


async def upsert_daily_activity_azm(
    session: AsyncSession, user_id, d: date, source: str, **fields
) -> None:
    await _upsert(session, DailyActivity,
                  {"user_id": user_id, "date": d, "source": source}, fields)


async def upsert_daily_body(
    session: AsyncSession, user_id, d: date, source: str, **fields
) -> None:
    await _upsert(session, DailyBody,
                  {"user_id": user_id, "date": d, "source": source}, fields)


async def upsert_hourly_intraday(
    session: AsyncSession, user_id, d: date, hour: int,
    metric_type: str, source: str,
    avg_value: float, min_value: float, max_value: float,
    sample_count: int, extra: dict | None = None,
) -> None:
    await _upsert(
        session, HourlyIntraday,
        {"user_id": user_id, "date": d, "hour": hour,
         "metric_type": metric_type, "source": source},
        {"avg_value": avg_value, "min_value": min_value,
         "max_value": max_value, "sample_count": sample_count, "extra": extra},
    )


async def upsert_exercise_log(
    session: AsyncSession, user_id, external_id: str, source: str, **fields
) -> None:
    await _upsert(session, ExerciseLog,
                  {"user_id": user_id, "external_id": external_id, "source": source}, fields)


async def upsert_user_context(
    session: AsyncSession, user_id, source: str, **fields
) -> None:
    await _upsert(session, UserContext,
                  {"user_id": user_id, "source": source}, fields,
                  timestamp_col="updated_at")
