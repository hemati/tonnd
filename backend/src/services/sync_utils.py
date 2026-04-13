"""Shared sync utilities used by all data source sync modules."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import FitnessMetric


async def upsert_metric(
    session: AsyncSession,
    user_id,
    metric_date,
    metric_type: str,
    metric_data: dict,
    source: str = "fitbit",
) -> None:
    """Insert or update a single fitness metric."""
    stmt = select(FitnessMetric).where(
        FitnessMetric.user_id == user_id,
        FitnessMetric.date == metric_date,
        FitnessMetric.metric_type == metric_type,
        FitnessMetric.source == source,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.data = metric_data
        existing.synced_at = datetime.now(timezone.utc)
    else:
        session.add(
            FitnessMetric(
                user_id=user_id,
                date=metric_date,
                metric_type=metric_type,
                source=source,
                data=metric_data,
            )
        )


async def _upsert(
    session: AsyncSession, model, lookup: dict, fields: dict,
    timestamp_col: str = "synced_at",
) -> None:
    """Generic upsert: SELECT by lookup keys, then INSERT or UPDATE fields."""
    stmt = select(model)
    for col, val in lookup.items():
        stmt = stmt.where(getattr(model, col) == val)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row:
        for k, v in fields.items():
            if v is not None:
                setattr(row, k, v)
        setattr(row, timestamp_col, datetime.now(timezone.utc))
    else:
        session.add(model(**lookup, **fields))
