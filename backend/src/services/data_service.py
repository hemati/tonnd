"""Shared data access layer for fitness metrics.

Used by both the dashboard (/api/data) and the public API (/api/v1/).
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import FitnessMetric


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
