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
