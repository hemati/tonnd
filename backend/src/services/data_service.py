"""Shared data access layer for fitness metrics.

Used by both the dashboard (/api/data) and the public API (/api/v1/).
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import FitnessMetric
from src.models.fitbit_models import (
    DailyActivity,
    DailyBody,
    DailySleep,
    DailyVitals,
    ExerciseLog,
    HourlyIntraday,
    UserContext,
)


async def query_metrics(
    session: AsyncSession,
    user_id,
    metric_types: list[str] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    source: str | None = None,
    limit: int = 100,
    offset: int = 0,
    order: str = "desc",
) -> list[FitnessMetric]:
    """Query fitness metrics with filtering, pagination, and ordering."""
    stmt = select(FitnessMetric).where(FitnessMetric.user_id == user_id)

    if metric_types:
        stmt = stmt.where(FitnessMetric.metric_type.in_(metric_types))

    if start_date:
        stmt = stmt.where(FitnessMetric.date >= start_date)

    if end_date:
        stmt = stmt.where(FitnessMetric.date <= end_date)

    if source:
        stmt = stmt.where(FitnessMetric.source == source)

    if order == "asc":
        stmt = stmt.order_by(FitnessMetric.date.asc())
    else:
        stmt = stmt.order_by(FitnessMetric.date.desc())

    stmt = stmt.offset(offset).limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())


def metric_to_dict(m: FitnessMetric) -> dict:
    """Convert a FitnessMetric row to a flat dict for API responses."""
    return {
        "date": m.date.isoformat(),
        "metric_type": m.metric_type,
        "source": m.source,
        **m.data,
    }


async def get_latest(
    session: AsyncSession,
    user_id,
    metric_type: str,
) -> dict | None:
    """Get the most recent metric of a given type for a user."""
    stmt = (
        select(FitnessMetric)
        .where(
            FitnessMetric.user_id == user_id,
            FitnessMetric.metric_type == metric_type,
        )
        .order_by(FitnessMetric.date.desc())
        .limit(1)
    )
    m = (await session.execute(stmt)).scalar_one_or_none()
    return metric_to_dict(m) if m else None


def compute_recovery_score(
    latest_hrv: dict | None,
    latest_sleep: dict | None,
    latest_hr: dict | None,
) -> dict:
    """Compute recovery score from latest HRV, sleep, and heart rate data.

    Formula: 40% HRV + 35% sleep efficiency + 25% resting HR.
    """
    result = {
        "score": None,
        "hrv_score": None,
        "sleep_score": None,
        "rhr_score": None,
        "latest_hrv": latest_hrv,
        "latest_sleep": latest_sleep,
        "latest_hr": latest_hr,
    }

    if not (latest_hrv and latest_sleep and latest_hr):
        return result

    hrv_val = latest_hrv.get("daily_rmssd")
    sleep_eff = latest_sleep.get("efficiency")
    rhr = latest_hr.get("resting_heart_rate")

    if not (hrv_val and sleep_eff and rhr):
        return result

    hrv_score = min(100.0, (hrv_val / 100) * 100)
    sleep_score = float(sleep_eff)
    rhr_score = max(0.0, min(100.0, (100 - rhr) * 2))

    result["hrv_score"] = round(hrv_score, 1)
    result["sleep_score"] = round(sleep_score, 1)
    result["rhr_score"] = round(rhr_score, 1)
    result["score"] = round(hrv_score * 0.4 + sleep_score * 0.35 + rhr_score * 0.25)

    return result


# ─── Typed-table query functions ────────────────────────────────────────────


async def query_daily_vitals(
    session: AsyncSession, user_id, start_date=None, end_date=None,
    source=None, limit=100, offset=0, order="desc",
):
    stmt = select(DailyVitals).where(DailyVitals.user_id == user_id)
    if start_date:
        stmt = stmt.where(DailyVitals.date >= start_date)
    if end_date:
        stmt = stmt.where(DailyVitals.date <= end_date)
    if source:
        stmt = stmt.where(DailyVitals.source == source)
    stmt = stmt.order_by(DailyVitals.date.asc() if order == "asc" else DailyVitals.date.desc())
    stmt = stmt.offset(offset).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def query_daily_sleep(
    session: AsyncSession, user_id, start_date=None, end_date=None,
    source=None, limit=100, offset=0, order="desc",
):
    stmt = select(DailySleep).where(DailySleep.user_id == user_id)
    if start_date:
        stmt = stmt.where(DailySleep.date >= start_date)
    if end_date:
        stmt = stmt.where(DailySleep.date <= end_date)
    if source:
        stmt = stmt.where(DailySleep.source == source)
    stmt = stmt.order_by(DailySleep.date.asc() if order == "asc" else DailySleep.date.desc())
    stmt = stmt.offset(offset).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def query_daily_activity(
    session: AsyncSession, user_id, start_date=None, end_date=None,
    source=None, limit=100, offset=0, order="desc",
):
    stmt = select(DailyActivity).where(DailyActivity.user_id == user_id)
    if start_date:
        stmt = stmt.where(DailyActivity.date >= start_date)
    if end_date:
        stmt = stmt.where(DailyActivity.date <= end_date)
    if source:
        stmt = stmt.where(DailyActivity.source == source)
    stmt = stmt.order_by(DailyActivity.date.asc() if order == "asc" else DailyActivity.date.desc())
    stmt = stmt.offset(offset).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def query_daily_body(
    session: AsyncSession, user_id, start_date=None, end_date=None,
    source=None, limit=100, offset=0, order="desc",
):
    stmt = select(DailyBody).where(DailyBody.user_id == user_id)
    if start_date:
        stmt = stmt.where(DailyBody.date >= start_date)
    if end_date:
        stmt = stmt.where(DailyBody.date <= end_date)
    if source:
        stmt = stmt.where(DailyBody.source == source)
    stmt = stmt.order_by(DailyBody.date.asc() if order == "asc" else DailyBody.date.desc())
    stmt = stmt.offset(offset).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def query_hourly_intraday(
    session: AsyncSession, user_id, metric_type: str,
    start_date=None, end_date=None, source=None,
    start_hour=None, end_hour=None, limit=500, offset=0,
):
    stmt = select(HourlyIntraday).where(
        HourlyIntraday.user_id == user_id,
        HourlyIntraday.metric_type == metric_type,
    )
    if start_date:
        stmt = stmt.where(HourlyIntraday.date >= start_date)
    if end_date:
        stmt = stmt.where(HourlyIntraday.date <= end_date)
    if source:
        stmt = stmt.where(HourlyIntraday.source == source)
    if start_hour is not None:
        stmt = stmt.where(HourlyIntraday.hour >= start_hour)
    if end_hour is not None:
        stmt = stmt.where(HourlyIntraday.hour <= end_hour)
    stmt = stmt.order_by(HourlyIntraday.date.asc(), HourlyIntraday.hour.asc())
    stmt = stmt.offset(offset).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def query_exercise_logs(
    session: AsyncSession, user_id, start_date=None, end_date=None,
    source=None, limit=100, offset=0, order="desc",
):
    stmt = select(ExerciseLog).where(ExerciseLog.user_id == user_id)
    if start_date:
        stmt = stmt.where(ExerciseLog.date >= start_date)
    if end_date:
        stmt = stmt.where(ExerciseLog.date <= end_date)
    if source:
        stmt = stmt.where(ExerciseLog.source == source)
    stmt = stmt.order_by(ExerciseLog.date.asc() if order == "asc" else ExerciseLog.date.desc())
    stmt = stmt.offset(offset).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def query_user_context(session: AsyncSession, user_id, source=None):
    stmt = select(UserContext).where(UserContext.user_id == user_id)
    if source:
        stmt = stmt.where(UserContext.source == source)
    return list((await session.execute(stmt)).scalars().all())
