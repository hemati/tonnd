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
from src.services.fitbit.context import parse_devices, parse_profile
from src.services.fitbit.exercise_logs import parse_exercise_logs
from src.services.fitbit.intraday import INTRADAY_ENDPOINTS, aggregate_to_hourly
from src.services.fitbit.sync import disconnect_fitbit, ensure_valid_token
from src.services.fitbit_sync_utils import (
    upsert_daily_activity,
    upsert_daily_activity_azm,
    upsert_daily_sleep,
    upsert_daily_vitals,
    upsert_exercise_log,
    upsert_hourly_intraday,
    upsert_user_context,
)
from src.services.hevy.sync import sync_hevy_workouts, sync_hevy_routines
from src.services.renpho.sync import sync_renpho_data

logger = logging.getLogger(__name__)

DELAY_BETWEEN_USERS = 2  # Fitbit allows ~150 req/hour


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO datetime string to a datetime object. Returns None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None

# Vitals metric keys from get_all_data_for_date result
VITALS_KEYS = {"heart_rate", "hrv", "spo2", "breathing_rate", "vo2_max", "temperature"}


async def sync_fitbit_daily(
    session: AsyncSession, user: User, sync_date: date, client: FitbitClient
) -> None:
    """Distribute get_all_data_for_date() results to typed tables."""
    result = await client.get_all_data_for_date(sync_date.isoformat())
    data = result["data"]

    # --- Vitals ---
    vitals_fields = {}
    hr = data.get("heart_rate")
    if hr:
        vitals_fields["resting_heart_rate"] = hr.get("resting_heart_rate")
        vitals_fields["hr_zones"] = hr.get("zones")

    hrv = data.get("hrv")
    if hrv:
        vitals_fields["daily_rmssd"] = hrv.get("daily_rmssd")
        vitals_fields["deep_rmssd"] = hrv.get("deep_rmssd")

    spo2 = data.get("spo2")
    if spo2:
        vitals_fields["spo2_avg"] = spo2.get("avg")
        vitals_fields["spo2_min"] = spo2.get("min")
        vitals_fields["spo2_max"] = spo2.get("max")

    br = data.get("breathing_rate")
    if br:
        vitals_fields["breathing_rate"] = br.get("breathing_rate")

    vo2 = data.get("vo2_max")
    if vo2:
        vitals_fields["vo2_max"] = vo2.get("vo2_max")

    temp = data.get("temperature")
    if temp:
        vitals_fields["temp_relative_deviation"] = temp.get("relative_deviation")

    if vitals_fields:
        await upsert_daily_vitals(
            session, user.id, sync_date, source="fitbit", **vitals_fields
        )

    # --- Sleep ---
    sleep_entries = data.get("sleep", [])
    for entry in sleep_entries:
        entry = dict(entry)  # don't mutate original
        external_id = entry.pop("external_id", None)
        date_of_sleep_str = entry.pop("date_of_sleep", None)

        if not external_id:
            continue

        if date_of_sleep_str:
            try:
                sleep_date = date.fromisoformat(date_of_sleep_str)
            except (ValueError, TypeError):
                sleep_date = sync_date
        else:
            sleep_date = sync_date

        # Convert datetime strings to objects for SQLAlchemy
        if "start_time" in entry:
            entry["start_time"] = _parse_dt(entry["start_time"])
        if "end_time" in entry:
            entry["end_time"] = _parse_dt(entry["end_time"])

        await upsert_daily_sleep(
            session,
            user.id,
            external_id=external_id,
            source="fitbit",
            date=sleep_date,
            **entry,
        )

    # --- Activity ---
    activity = data.get("activity")
    if activity:
        await upsert_daily_activity(
            session, user.id, sync_date, source="fitbit", **activity
        )

    # --- Active Zone Minutes ---
    azm = data.get("active_zone_minutes")
    if azm:
        azm_fields = {
            "fat_burn_azm": azm.get("fat_burn_minutes"),
            "cardio_azm": azm.get("cardio_minutes"),
            "peak_azm": azm.get("peak_minutes"),
            "total_azm": azm.get("total_minutes"),
        }
        await upsert_daily_activity_azm(
            session, user.id, sync_date, source="fitbit", **azm_fields
        )

    # --- Weight / Body ---
    weight = data.get("weight")
    if weight:
        measured_at = weight.pop("measured_at", None)
        if not measured_at:
            measured_at = datetime(sync_date.year, sync_date.month, sync_date.day, tzinfo=timezone.utc)
        from src.services.sync_utils import upsert_body_measurement
        await upsert_body_measurement(
            session, user.id, "fitbit", measured_at,
            date=sync_date, **weight,
        )


async def sync_fitbit_exercise_logs(
    session: AsyncSession, user: User, sync_date: date, client: FitbitClient
) -> None:
    """Fetch and upsert Fitbit exercise logs for the given date."""
    raw = await client.get_exercise_logs(after_date=sync_date.isoformat())
    logs = parse_exercise_logs(raw)

    for log in logs:
        log = dict(log)  # don't mutate original
        external_id = log.pop("external_id", None)
        if not external_id:
            continue

        # Derive date from started_at if available
        started_at_str = log.get("started_at")
        if started_at_str:
            try:
                log_date = datetime.fromisoformat(started_at_str).date()
            except (ValueError, TypeError):
                log_date = sync_date
        else:
            log_date = sync_date

        # Convert datetime strings to objects for SQLAlchemy
        if "started_at" in log:
            log["started_at"] = _parse_dt(log["started_at"])
        if "ended_at" in log:
            log["ended_at"] = _parse_dt(log["ended_at"])

        await upsert_exercise_log(
            session,
            user.id,
            external_id=external_id,
            source="fitbit",
            date=log_date,
            **log,
        )


async def sync_fitbit_intraday(
    session: AsyncSession, user: User, sync_date: date, client: FitbitClient
) -> None:
    """Fetch intraday data, aggregate to hourly, upsert. Handle 403 gracefully."""
    # If previously flagged as unavailable, skip
    if user.fitbit_intraday_available is False:
        return

    for metric_type, endpoint_cfg in INTRADAY_ENDPOINTS.items():
        url = endpoint_cfg["url"].format(date=sync_date.isoformat())
        try:
            raw = await client._make_request(url)
        except Exception as e:
            err_str = str(e)
            if "403" in err_str or "Forbidden" in err_str:
                logger.info(
                    f"Intraday 403 for user {user.id} — disabling intraday"
                )
                user.fitbit_intraday_available = False
                return
            raise

        intraday_data = raw.get(endpoint_cfg["response_key"], {})
        datapoints = intraday_data.get(endpoint_cfg["dataset_key"], [])

        hourly = aggregate_to_hourly(
            datapoints,
            value_key=endpoint_cfg["value_key"],
            use_sum=endpoint_cfg.get("use_sum", False),
        )

        for hour, stats in hourly.items():
            await upsert_hourly_intraday(
                session,
                user.id,
                sync_date,
                hour=hour,
                metric_type=metric_type,
                source="fitbit",
                avg_value=stats["avg"],
                min_value=stats["min"],
                max_value=stats["max"],
                sample_count=stats["sample_count"],
            )

    # If we got here without 403 and flag was None, mark as available
    if user.fitbit_intraday_available is None:
        user.fitbit_intraday_available = True


async def sync_fitbit_context(
    session: AsyncSession, user: User, client: FitbitClient
) -> None:
    """Fetch profile + devices, parse, upsert user_context."""
    context_fields = {}

    # Profile
    profile_raw = await client.get_profile()
    profile = parse_profile(profile_raw)

    # Convert date_of_birth string to date object
    dob_str = profile.pop("date_of_birth", None)
    if dob_str:
        try:
            profile["date_of_birth"] = date.fromisoformat(dob_str)
        except (ValueError, TypeError):
            pass

    context_fields.update(profile)

    # Devices — 403 is caught and skipped
    try:
        devices_raw = await client.get_devices()
        devices = parse_devices(devices_raw)
        # Convert last_device_sync string to datetime
        if "last_device_sync" in devices:
            devices["last_device_sync"] = _parse_dt(devices["last_device_sync"])
        context_fields.update(devices)
    except Exception as e:
        err_str = str(e)
        if "403" in err_str or "Forbidden" in err_str:
            logger.info(f"Devices 403 for user {user.id} — skipping")
        else:
            raise

    if context_fields:
        await upsert_user_context(
            session, user.id, source="fitbit", **context_fields
        )


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
                await sync_fitbit_daily(session, user, sync_date, client)
                await sync_fitbit_exercise_logs(session, user, sync_date, client)
                await sync_fitbit_intraday(session, user, sync_date, client)

            # Context only needs to run once per sync (not per day)
            await sync_fitbit_context(session, user, client)

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

    # Hevy — typed pipeline
    if user.hevy_api_key:
        try:
            from src.services.hevy.client import get_client
            from src.services.token_encryption import decrypt_token as _dt
            hevy_api_key = _dt(user.hevy_api_key)
            hevy_client = get_client(hevy_api_key)
            template_cache: dict = {}
            for days_ago in [1, 0]:
                sync_date = date.today() - timedelta(days=days_ago)
                hevy_errors = await sync_hevy_workouts(session, user, sync_date, hevy_api_key, hevy_client, template_cache)
                if hevy_errors:
                    logger.warning(f"Hevy workout errors for user {user.id}: {hevy_errors}")
            routine_errors = await sync_hevy_routines(session, user, hevy_api_key)
            if routine_errors:
                logger.warning(f"Hevy routine errors for user {user.id}: {routine_errors}")
        except Exception as e:
            logger.error(f"Hevy sync failed for user {user.id}: {e}")

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
