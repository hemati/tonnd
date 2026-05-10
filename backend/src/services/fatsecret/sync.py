"""FatSecret sync pipeline — typed food_entries + aggregated daily_nutrition."""

import logging
from datetime import date as date_type
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import User
from src.models.food_models import FoodEntry
from src.services.fatsecret.client import (
    FatSecretAPIError,
    FatSecretAuthError,
    get_food_entries_for_date,
)
from src.services.fatsecret_sync_utils import (
    aggregate_daily_nutrition,
    upsert_food_entry,
)
from src.services.token_encryption import decrypt_token

logger = logging.getLogger(__name__)

SOURCE = "fatsecret"


async def _sync_entries_for_date(
    session: AsyncSession,
    user: User,
    target_date: date_type,
    http: httpx.AsyncClient,
) -> None:
    """Fetch FatSecret entries for `target_date`, upsert + soft-delete reconciliation.

    Known limitation: only detects deletions within the synced date range.
    FatSecret has no event-feed endpoint (food_entries.get is date-scoped),
    so older deletions (>2 days) stay in DB as not-deleted. Acceptable for v1
    since aggregation only re-runs for the sync window.
    """
    oauth_token = decrypt_token(user.fatsecret_oauth_token)
    oauth_secret = decrypt_token(user.fatsecret_oauth_token_secret)

    raw_entries = await get_food_entries_for_date(
        oauth_token, oauth_secret, target_date, http,
    )

    synced_external_ids: set[str] = set()
    for entry in raw_entries:
        external_id = entry.pop("external_id", None)
        if not external_id:
            continue
        await upsert_food_entry(
            session, user.id, external_id, SOURCE, **entry,
        )
        synced_external_ids.add(external_id)

    # Soft-delete reconciliation: any active row for this date+user not in
    # the API response is now considered deleted in FatSecret.
    stored = (await session.execute(
        select(FoodEntry).where(
            FoodEntry.user_id == user.id,
            FoodEntry.source == SOURCE,
            FoodEntry.date == target_date,
            FoodEntry.deleted_at.is_(None),
        )
    )).scalars().all()
    now = datetime.now(timezone.utc)
    for row in stored:
        if row.external_id not in synced_external_ids:
            row.deleted_at = now


async def sync_fatsecret_for_date(
    session: AsyncSession,
    user: User,
    target_date: date_type,
    http: httpx.AsyncClient,
) -> dict:
    """Sync entries + aggregate daily_nutrition for one date. Always aggregates."""
    errors: list[str] = []
    try:
        await _sync_entries_for_date(session, user, target_date, http)
    except FatSecretAuthError:
        # Re-raise to let the scheduler/route disconnect the user.
        raise
    except FatSecretAPIError as e:
        errors.append(f"fatsecret:{target_date}:entries: {e}")
        logger.warning(
            "FatSecret entry sync failed for user=%s date=%s: %s",
            user.id, target_date, e,
        )
    except Exception as e:
        errors.append(f"fatsecret:{target_date}:entries: {e}")
        logger.exception(
            "FatSecret entry sync crashed for user=%s date=%s",
            user.id, target_date,
        )

    # Always re-aggregate, even on entry-sync failure or empty day. This is
    # what makes a fully-deleted day correctly zero out — see Step 2 docstring.
    try:
        await aggregate_daily_nutrition(session, user.id, target_date, source=SOURCE)
    except Exception as e:
        errors.append(f"fatsecret:{target_date}:aggregate: {e}")
        logger.exception(
            "FatSecret aggregation failed for user=%s date=%s",
            user.id, target_date,
        )

    return {"errors": errors}


async def backfill_fatsecret(
    session: AsyncSession,
    user: User,
    num_days: int,
    http: httpx.AsyncClient,
) -> dict:
    """Sync the last `num_days` days (today inclusive). Used after first connect."""
    today = datetime.now(timezone.utc).date()
    all_errors: list[str] = []
    for i in range(num_days):
        d = today - timedelta(days=i)
        try:
            result = await sync_fatsecret_for_date(session, user, d, http)
            all_errors.extend(result["errors"])
        except FatSecretAuthError as e:
            all_errors.append(f"fatsecret:{d}:auth: {e}")
            logger.warning("FatSecret token rejected mid-backfill at user=%s", user.id)
            break
    return {"errors": all_errors}


def disconnect_fatsecret(user: User) -> None:
    """Clear FatSecret tokens. Called on disconnect or auth failure."""
    user.fatsecret_oauth_token = None
    user.fatsecret_oauth_token_secret = None
