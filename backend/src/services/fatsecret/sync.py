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
from src.services.token_encryption import decrypt_token  # used by _decrypt_or_disconnect

logger = logging.getLogger(__name__)

SOURCE = "fatsecret"

# Cap the after-connect backfill so a misconfigured caller cannot pin the
# event loop or hammer the FatSecret API. Routes default to 30; raising past
# this requires editing here intentionally.
MAX_BACKFILL_DAYS = 30


def _decrypt_or_disconnect(encrypted: str | None) -> str:
    """Decrypt a stored token. Convert any failure into a FatSecretAuthError so
    the caller treats it as a permanent token problem (key rotation, tampering,
    or cleared columns) and disconnects the user instead of silently retrying.

    The exception message intentionally omits the underlying error text — Fernet
    failure messages can echo input fragments and we don't want them in logs.
    """
    if not encrypted:
        raise FatSecretAuthError("FatSecret token missing")
    try:
        return decrypt_token(encrypted)
    except Exception as e:
        raise FatSecretAuthError(
            f"FatSecret token decryption failed ({type(e).__name__})"
        )


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
    # Pass decrypted tokens inline to avoid binding them to named locals; the
    # call frame holds them only as args of the called function, mitigating
    # exfiltration via tracebacks captured with locals (Sentry, structlog).
    fetched = await get_food_entries_for_date(
        _decrypt_or_disconnect(user.fatsecret_oauth_token),
        _decrypt_or_disconnect(user.fatsecret_oauth_token_secret),
        target_date, http,
    )

    for entry in fetched["normalized"]:
        external_id = entry.pop("external_id", None)
        if not external_id:
            continue
        await upsert_food_entry(
            session, user.id, external_id, SOURCE, **entry,
        )

    # Soft-delete reconciliation uses `api_external_ids` — the set of ids the
    # API claims exist on this date, INCLUDING entries we couldn't normalize.
    # If we used the upsert set instead, a single malformed API entry (missing
    # food_entry_name, etc.) would silently soft-delete the user's existing
    # data for that id.
    api_ids: set[str] = fetched["api_external_ids"]
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
        if row.external_id not in api_ids:
            row.deleted_at = now


async def sync_fatsecret_for_date(
    session: AsyncSession,
    user: User,
    target_date: date_type,
    http: httpx.AsyncClient,
) -> dict:
    """Sync entries + aggregate daily_nutrition for one date.

    Aggregation runs on success and on entry-sync errors that come AFTER we've
    seen at least one stored row — the recompute against current DB state is
    still meaningful. It is intentionally SKIPPED when entry-sync fails AND
    there is no stored data for the date, to avoid writing a misleading
    "trusted 0 calories" row when the user's diary was simply unreachable.
    """
    errors: list[str] = []
    entry_sync_ok = True
    try:
        await _sync_entries_for_date(session, user, target_date, http)
    except FatSecretAuthError:
        # Re-raise so the scheduler/route disconnects the user.
        raise
    except FatSecretAPIError as e:
        entry_sync_ok = False
        errors.append(f"fatsecret:{target_date}:entries: {e}")
        logger.warning(
            "FatSecret entry sync failed for user=%s date=%s: %s",
            user.id, target_date, e,
        )
    except Exception as e:
        entry_sync_ok = False
        errors.append(f"fatsecret:{target_date}:entries: {e}")
        logger.exception(
            "FatSecret entry sync crashed for user=%s date=%s",
            user.id, target_date,
        )

    should_aggregate = entry_sync_ok or await _has_existing_entries(
        session, user.id, target_date,
    )
    if should_aggregate:
        try:
            await aggregate_daily_nutrition(session, user.id, target_date, source=SOURCE)
        except Exception as e:
            errors.append(f"fatsecret:{target_date}:aggregate: {e}")
            logger.exception(
                "FatSecret aggregation failed for user=%s date=%s",
                user.id, target_date,
            )

    return {"errors": errors}


async def _has_existing_entries(
    session: AsyncSession, user_id, target_date: date_type,
) -> bool:
    """Cheap existence check used to gate aggregation when entry-sync fails."""
    from sqlalchemy import exists, select
    stmt = select(exists().where(
        FoodEntry.user_id == user_id,
        FoodEntry.source == SOURCE,
        FoodEntry.date == target_date,
        FoodEntry.deleted_at.is_(None),
    ))
    return bool((await session.execute(stmt)).scalar())


async def backfill_fatsecret(
    session: AsyncSession,
    user: User,
    num_days: int,
    http: httpx.AsyncClient,
) -> dict:
    """Sync the last `num_days` days (today inclusive). Used after first connect.

    `num_days` is clamped to [0, MAX_BACKFILL_DAYS] — the caller can never
    push past the cap by passing a huge or negative value.
    """
    num_days = max(0, min(num_days, MAX_BACKFILL_DAYS))
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
