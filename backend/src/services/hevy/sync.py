"""Hevy sync helpers — analogous to renpho_sync.py."""

import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import User
from src.services.sync_utils import upsert_metric
from src.services.hevy.client import HevyClient, get_workouts_for_date, get_client
from src.services.token_encryption import decrypt_token

logger = logging.getLogger(__name__)


async def sync_hevy_data(
    session: AsyncSession,
    user: User,
    target_date: date,
    hevy_client: HevyClient | None = None,
    template_cache: dict | None = None,
) -> dict:
    """
    Sync Hevy workout data for a single date.

    Returns: {"synced_metrics": [...], "errors": [...]}
    """
    synced_metrics = []
    errors = []

    if not user.hevy_api_key:
        return {"synced_metrics": [], "errors": ["Hevy not connected"]}

    api_key = decrypt_token(user.hevy_api_key)

    try:
        result = await get_workouts_for_date(api_key, target_date, hevy_client, template_cache)

        for metric_type, metric_data in result["data"].items():
            await upsert_metric(
                session, user.id, target_date, metric_type, metric_data, source="hevy"
            )
            synced_metrics.append(f"hevy:{target_date.isoformat()}#{metric_type}")

        errors.extend(result.get("errors", []))

    except Exception as e:
        errors.append(f"hevy: {e}")
        logger.error(f"Hevy sync failed for user {user.id}: {e}")

    return {"synced_metrics": synced_metrics, "errors": errors}


def disconnect_hevy(user: User) -> None:
    """Clear Hevy API key from user."""
    user.hevy_api_key = None
