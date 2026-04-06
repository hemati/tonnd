"""Daily Fitbit sync scheduler — replaces AWS EventBridge."""

import asyncio
import logging
import time
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_maker
from src.models.db_models import User
from src.services.fitbit_client import FitbitClient, RateLimitError, TokenExpiredError
from src.services.fitbit_sync import (
    disconnect_fitbit,
    ensure_valid_token,
    upsert_metric,
)

logger = logging.getLogger(__name__)

DELAY_BETWEEN_USERS = 2  # Fitbit allows ~150 req/hour


async def sync_user(session: AsyncSession, user: User) -> str:
    """Sync a single user's Fitbit data. Returns status string."""
    try:
        access_token = await ensure_valid_token(user)
        client = FitbitClient(access_token)

        for days_ago in [1, 0]:
            sync_date = date.today() - timedelta(days=days_ago)
            result = await client.get_all_data_for_date(sync_date.isoformat())

            for metric_type, metric_data in result["data"].items():
                await upsert_metric(
                    session, user.id, sync_date, metric_type, metric_data
                )

        user.last_sync = datetime.now(timezone.utc)
        await session.commit()
        return "success"

    except TokenExpiredError:
        disconnect_fitbit(user)
        await session.commit()
        return "token_expired"

    except RateLimitError:
        return "rate_limited"

    except Exception as e:
        logger.error(f"Sync failed for user {user.id}: {e}")
        return "failed"


async def daily_sync_all():
    """Sync all users with connected Fitbit accounts."""
    start = time.time()
    logger.info("Starting daily sync for all users")

    async with async_session_maker() as session:
        stmt = select(User).where(User.fitbit_access_token.isnot(None))
        result = await session.execute(stmt)
        users = result.scalars().all()

    stats = {"success": 0, "failed": 0, "token_expired": 0, "rate_limited": 0}

    for user in users:
        async with async_session_maker() as session:
            user = await session.get(User, user.id)
            status = await sync_user(session, user)
            stats[status] = stats.get(status, 0) + 1

            if status == "rate_limited":
                logger.warning("Rate limited — stopping batch")
                break

            await asyncio.sleep(DELAY_BETWEEN_USERS)

    elapsed = round(time.time() - start, 1)
    logger.info(f"Daily sync complete in {elapsed}s: {stats}")
    return stats
