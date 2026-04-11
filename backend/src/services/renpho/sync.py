"""Renpho sync helpers — analogous to fitbit_sync.py."""

import logging
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import User
from src.services.sync_utils import upsert_metric
from src.services.renpho.client import RenphoAPIError, get_measurements_for_date
from src.services.token_encryption import decrypt_token

logger = logging.getLogger(__name__)


async def sync_renpho_data(
    session: AsyncSession,
    user: User,
    target_date: date,
) -> dict:
    """
    Sync Renpho data for a single date.

    Returns: {"synced_metrics": [...], "errors": [...]}
    """
    synced_metrics = []
    errors = []

    if not user.renpho_email or not user.renpho_session_key:
        return {"synced_metrics": [], "errors": ["Renpho not connected"]}

    email = decrypt_token(user.renpho_email)
    password = decrypt_token(user.renpho_session_key)

    try:
        result = get_measurements_for_date(email, password, target_date)

        for metric_type, metric_data in result["data"].items():
            await upsert_metric(
                session, user.id, target_date, metric_type, metric_data, source="renpho"
            )
            synced_metrics.append(f"renpho:{target_date.isoformat()}#{metric_type}")

        errors.extend(result.get("errors", []))

    except RenphoAPIError as e:
        errors.append(f"renpho: {e}")
        logger.error(f"Renpho sync failed for user {user.id}: {e}")

    except Exception as e:
        errors.append(f"renpho: {e}")
        logger.error(f"Renpho sync failed for user {user.id}: {e}")

    return {"synced_metrics": synced_metrics, "errors": errors}


def disconnect_renpho(user: User) -> None:
    """Clear all Renpho credentials from user."""
    user.renpho_email = None
    user.renpho_session_key = None
