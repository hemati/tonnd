"""Renpho sync pipeline — writes to body_measurements typed table."""

import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import User
from src.services.body_sync_utils import upsert_body_measurement
from src.services.renpho.client import get_measurements_for_date
from src.services.token_encryption import decrypt_token

logger = logging.getLogger(__name__)


async def sync_renpho_data(
    session: AsyncSession, user: User, target_date: date,
) -> dict:
    """Sync Renpho measurements into body_measurements table."""
    synced_metrics: list[str] = []
    errors: list[str] = []

    if not user.renpho_email or not user.renpho_session_key:
        errors.append("renpho: not connected")
        return {"synced_metrics": synced_metrics, "errors": errors}

    email = decrypt_token(user.renpho_email)
    password = decrypt_token(user.renpho_session_key)

    result = get_measurements_for_date(email, password, target_date)
    errors.extend(result.get("errors", []))

    for measurement in result.get("data", []):
        measured_at = measurement.pop("measured_at")
        measurement_date = measurement.pop("date")
        await upsert_body_measurement(
            session, user.id, "renpho", measured_at,
            date=measurement_date, **measurement,
        )
        synced_metrics.append(f"renpho:{target_date.isoformat()}#body")

    return {"synced_metrics": synced_metrics, "errors": errors}


def disconnect_renpho(user: User) -> None:
    """Clear Renpho credentials from user."""
    user.renpho_email = None
    user.renpho_session_key = None
