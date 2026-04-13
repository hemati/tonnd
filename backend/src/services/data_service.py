"""Shared data access layer for fitness metrics.

Used by both the dashboard (/api/data) and the public API (/api/v1/).
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import FitnessMetric
from src.models.body_models import BodyMeasurement
from src.models.fitbit_models import (
    DailyActivity,
    DailySleep,
    DailyVitals,
    ExerciseLog,
    HourlyIntraday,
    UserContext,
)
from src.models.hevy_models import Routine, Workout, WorkoutExercise


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


async def _query_typed(
    session: AsyncSession, model, user_id,
    start_date=None, end_date=None, source=None,
    limit=100, offset=0, order="desc",
):
    """Generic query for typed tables with user_id, date, source columns."""
    stmt = select(model).where(model.user_id == user_id)
    if start_date:
        stmt = stmt.where(model.date >= start_date)
    if end_date:
        stmt = stmt.where(model.date <= end_date)
    if source:
        stmt = stmt.where(model.source == source)
    stmt = stmt.order_by(model.date.asc() if order == "asc" else model.date.desc())
    stmt = stmt.offset(offset).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def query_daily_vitals(session, user_id, **kw):
    return await _query_typed(session, DailyVitals, user_id, **kw)


async def query_daily_sleep(session, user_id, **kw):
    return await _query_typed(session, DailySleep, user_id, **kw)


async def query_daily_activity(session, user_id, **kw):
    return await _query_typed(session, DailyActivity, user_id, **kw)


async def query_body_measurements(session, user_id, **kw):
    """Query body measurements from all sources."""
    stmt = select(BodyMeasurement).where(BodyMeasurement.user_id == user_id)
    start_date = kw.get("start_date")
    end_date = kw.get("end_date")
    source = kw.get("source")
    limit = kw.get("limit", 100)
    offset = kw.get("offset", 0)
    order = kw.get("order", "desc")
    if start_date:
        stmt = stmt.where(BodyMeasurement.date >= start_date)
    if end_date:
        stmt = stmt.where(BodyMeasurement.date <= end_date)
    if source:
        stmt = stmt.where(BodyMeasurement.source == source)
    stmt = stmt.order_by(BodyMeasurement.date.asc() if order == "asc" else BodyMeasurement.date.desc())
    stmt = stmt.offset(offset).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def query_exercise_logs(session, user_id, **kw):
    return await _query_typed(session, ExerciseLog, user_id, **kw)


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


async def query_user_context(session: AsyncSession, user_id, source=None):
    stmt = select(UserContext).where(UserContext.user_id == user_id)
    if source:
        stmt = stmt.where(UserContext.source == source)
    return list((await session.execute(stmt)).scalars().all())


# ─── Hevy typed-table query functions ──────────────────────────────────────────


async def query_workouts(session, user_id, **kw):
    """Query workouts excluding soft-deleted."""
    stmt = select(Workout).where(
        Workout.user_id == user_id,
        Workout.deleted_at.is_(None),
    )
    start_date = kw.get("start_date")
    end_date = kw.get("end_date")
    source = kw.get("source")
    limit = kw.get("limit", 100)
    offset = kw.get("offset", 0)
    order = kw.get("order", "desc")

    if start_date:
        stmt = stmt.where(Workout.date >= start_date)
    if end_date:
        stmt = stmt.where(Workout.date <= end_date)
    if source:
        stmt = stmt.where(Workout.source == source)
    stmt = stmt.order_by(Workout.date.asc() if order == "asc" else Workout.date.desc())
    stmt = stmt.offset(offset).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def query_workout_by_external_id(session, user_id, external_id: str):
    stmt = select(Workout).where(
        Workout.user_id == user_id,
        Workout.external_id == external_id,
        Workout.deleted_at.is_(None),
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def query_workout_exercises(session, workout_id):
    stmt = (
        select(WorkoutExercise)
        .where(WorkoutExercise.workout_id == workout_id)
        .order_by(WorkoutExercise.exercise_index.asc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def workout_with_exercises(session, workout) -> dict:
    """Serialize a workout with its nested exercises. Used by API, MCP, and app.py."""
    d = workout.to_dict()
    exercises = await query_workout_exercises(session, workout.id)
    d["exercises"] = [e.to_dict() for e in exercises]
    return d


async def query_routines(session, user_id, **kw):
    """Query routines — no date column, ordered by title."""
    limit = kw.get("limit", 100)
    offset = kw.get("offset", 0)
    source = kw.get("source")
    stmt = select(Routine).where(Routine.user_id == user_id)
    if source:
        stmt = stmt.where(Routine.source == source)
    stmt = stmt.order_by(Routine.title.asc()).offset(offset).limit(limit)
    return list((await session.execute(stmt)).scalars().all())
