"""Shared helpers for Fitbit token management and metric upsert."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import FitnessMetric, User
from src.services.fitbit_client import refresh_access_token
from src.services.token_encryption import decrypt_token, encrypt_token


async def ensure_valid_token(user: User) -> str:
    """Return a valid access token, refreshing if needed. Mutates user in-place."""
    access_token = decrypt_token(user.fitbit_access_token)

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if user.fitbit_token_expires and user.fitbit_token_expires < now_ts + 300:
        refresh_tok = decrypt_token(user.fitbit_refresh_token)
        new_tokens = await refresh_access_token(refresh_tok)
        access_token = new_tokens["access_token"]
        user.fitbit_access_token = encrypt_token(new_tokens["access_token"])
        user.fitbit_refresh_token = encrypt_token(new_tokens["refresh_token"])
        user.fitbit_token_expires = now_ts + new_tokens.get("expires_in", 3600)

    return access_token


def disconnect_fitbit(user: User) -> None:
    """Clear all Fitbit tokens from user."""
    user.fitbit_access_token = None
    user.fitbit_refresh_token = None
    user.fitbit_token_expires = None


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
