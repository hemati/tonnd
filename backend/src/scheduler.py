"""Daily sync scheduler for all connected data sources."""

import asyncio
import logging
import time
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_maker
from src.models.db_models import User
from src.services.fitbit.client import FitbitClient, RateLimitError, TokenExpiredError
from src.services.fitbit.sync import disconnect_fitbit, ensure_valid_token
from src.services.sync_utils import upsert_metric
from src.services.hevy.sync import sync_hevy_data
from src.services.renpho.sync import sync_renpho_data

logger = logging.getLogger(__name__)

DELAY_BETWEEN_USERS = 2  # Fitbit allows ~150 req/hour


async def sync_user(session: AsyncSession, user: User) -> str:
    """Sync all connected sources for a single user."""
    status = "success"

    # Fitbit
    if user.fitbit_access_token:
        try:
            access_token = await ensure_valid_token(user)
            client = FitbitClient(access_token)

            for days_ago in [1, 0]:
                sync_date = date.today() - timedelta(days=days_ago)
                result = await client.get_all_data_for_date(sync_date.isoformat())

                for metric_type, metric_data in result["data"].items():
                    await upsert_metric(
                        session, user.id, sync_date, metric_type, metric_data, source="fitbit"
                    )

        except TokenExpiredError:
            disconnect_fitbit(user)
            status = "token_expired"

        except RateLimitError:
            status = "rate_limited"

        except Exception as e:
            logger.error(f"Fitbit sync failed for user {user.id}: {e}")
            status = "failed"

    # Renpho
    if user.renpho_session_key:
        for days_ago in [1, 0]:
            sync_date = date.today() - timedelta(days=days_ago)
            renpho_result = await sync_renpho_data(session, user, sync_date)
            if renpho_result["errors"]:
                logger.warning(f"Renpho errors for user {user.id}: {renpho_result['errors']}")

    # Hevy
    if user.hevy_api_key:
        for days_ago in [1, 0]:
            sync_date = date.today() - timedelta(days=days_ago)
            hevy_result = await sync_hevy_data(session, user, sync_date)
            if hevy_result["errors"]:
                logger.warning(f"Hevy errors for user {user.id}: {hevy_result['errors']}")

    user.last_sync = datetime.now(timezone.utc)
    await session.commit()
    return status


async def daily_sync_all():
    """Sync all users with any connected data source."""
    start = time.time()
    logger.info("Starting daily sync for all users")

    async with async_session_maker() as session:
        stmt = select(User).where(
            or_(
                User.fitbit_access_token.isnot(None),
                User.renpho_session_key.isnot(None),
                User.hevy_api_key.isnot(None),
            )
        )
        result = await session.execute(stmt)
        users = result.scalars().unique().all()

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
