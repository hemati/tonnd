"""Typed upsert functions for Fitbit expansion tables.

Each function uses SELECT + INSERT/UPDATE targeting specific columns
so that partial syncs (e.g., activity without AZM) don't overwrite each other.
"""

from datetime import date, datetime, timezone

from sqlalchemy import select
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


async def upsert_daily_vitals(
    session: AsyncSession, user_id, d: date, source: str, **fields
) -> None:
    stmt = select(DailyVitals).where(
        DailyVitals.user_id == user_id,
        DailyVitals.date == d,
        DailyVitals.source == source,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row:
        for k, v in fields.items():
            if v is not None:
                setattr(row, k, v)
        row.synced_at = datetime.now(timezone.utc)
    else:
        session.add(DailyVitals(user_id=user_id, date=d, source=source, **fields))


async def upsert_daily_sleep(
    session: AsyncSession, user_id, external_id: str, source: str, **fields
) -> None:
    stmt = select(DailySleep).where(
        DailySleep.user_id == user_id,
        DailySleep.source == source,
        DailySleep.external_id == external_id,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row:
        for k, v in fields.items():
            if v is not None:
                setattr(row, k, v)
        row.synced_at = datetime.now(timezone.utc)
    else:
        session.add(DailySleep(
            user_id=user_id, source=source, external_id=external_id, **fields
        ))


async def upsert_daily_activity(
    session: AsyncSession, user_id, d: date, source: str, **fields
) -> None:
    """Upsert activity fields only (steps, calories, distance, etc.)."""
    stmt = select(DailyActivity).where(
        DailyActivity.user_id == user_id,
        DailyActivity.date == d,
        DailyActivity.source == source,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row:
        for k, v in fields.items():
            if v is not None:
                setattr(row, k, v)
        row.synced_at = datetime.now(timezone.utc)
    else:
        session.add(DailyActivity(user_id=user_id, date=d, source=source, **fields))


async def upsert_daily_activity_azm(
    session: AsyncSession, user_id, d: date, source: str, **fields
) -> None:
    """Upsert AZM fields only. Creates row if needed, but only sets AZM columns."""
    stmt = select(DailyActivity).where(
        DailyActivity.user_id == user_id,
        DailyActivity.date == d,
        DailyActivity.source == source,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row:
        for k, v in fields.items():
            if v is not None:
                setattr(row, k, v)
        row.synced_at = datetime.now(timezone.utc)
    else:
        session.add(DailyActivity(user_id=user_id, date=d, source=source, **fields))


async def upsert_daily_body(
    session: AsyncSession, user_id, d: date, source: str, **fields
) -> None:
    stmt = select(DailyBody).where(
        DailyBody.user_id == user_id,
        DailyBody.date == d,
        DailyBody.source == source,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row:
        for k, v in fields.items():
            if v is not None:
                setattr(row, k, v)
        row.synced_at = datetime.now(timezone.utc)
    else:
        session.add(DailyBody(user_id=user_id, date=d, source=source, **fields))


async def upsert_hourly_intraday(
    session: AsyncSession, user_id, d: date, hour: int,
    metric_type: str, source: str,
    avg_value: float, min_value: float, max_value: float,
    sample_count: int, extra: dict | None = None,
) -> None:
    stmt = select(HourlyIntraday).where(
        HourlyIntraday.user_id == user_id,
        HourlyIntraday.date == d,
        HourlyIntraday.hour == hour,
        HourlyIntraday.metric_type == metric_type,
        HourlyIntraday.source == source,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row:
        row.avg_value = avg_value
        row.min_value = min_value
        row.max_value = max_value
        row.sample_count = sample_count
        row.extra = extra
        row.synced_at = datetime.now(timezone.utc)
    else:
        session.add(HourlyIntraday(
            user_id=user_id, date=d, hour=hour, metric_type=metric_type,
            source=source, avg_value=avg_value, min_value=min_value,
            max_value=max_value, sample_count=sample_count, extra=extra,
        ))


async def upsert_exercise_log(
    session: AsyncSession, user_id, external_id: str, source: str, **fields
) -> None:
    stmt = select(ExerciseLog).where(
        ExerciseLog.user_id == user_id,
        ExerciseLog.external_id == external_id,
        ExerciseLog.source == source,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row:
        for k, v in fields.items():
            if v is not None:
                setattr(row, k, v)
        row.synced_at = datetime.now(timezone.utc)
    else:
        session.add(ExerciseLog(
            user_id=user_id, external_id=external_id, source=source, **fields
        ))


async def upsert_user_context(
    session: AsyncSession, user_id, source: str, **fields
) -> None:
    stmt = select(UserContext).where(
        UserContext.user_id == user_id,
        UserContext.source == source,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row:
        for k, v in fields.items():
            if v is not None:
                setattr(row, k, v)
        row.updated_at = datetime.now(timezone.utc)
    else:
        session.add(UserContext(user_id=user_id, source=source, **fields))
