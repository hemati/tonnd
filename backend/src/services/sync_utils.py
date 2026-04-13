"""Shared sync utilities used by all data source sync modules."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _upsert(
    session: AsyncSession, model, lookup: dict, fields: dict,
    timestamp_col: str = "synced_at",
):
    """Generic upsert: SELECT by lookup keys, then INSERT or UPDATE fields. Returns the row."""
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
        row = model(**lookup, **fields)
        session.add(row)
    return row
