"""Server-side paced Fitbit historical backfill (two-phase background job).

Phase 1 (ranges): ~17 requests fill all typed daily tables for the window.
Phase 2 (intraday): per-day (no range API), paced under the 150 req/hour limit
using the Fitbit-Rate-Limit-Remaining/Reset headers captured by FitbitClient.

Runs as an in-process asyncio task — safe because the app is deployed as a
single uvicorn worker (see AGENTS.md Production Constraints).
"""

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_maker
from src.models.backfill_models import BackfillJob
from src.models.db_models import User
from src.scheduler import (
    sync_fitbit_context,
    sync_fitbit_intraday,
    sync_fitbit_range,
)
from src.services.fitbit.client import FitbitClient, RateLimitError, TokenExpiredError
from src.services.fitbit.sync import disconnect_fitbit, ensure_valid_token

logger = logging.getLogger(__name__)

DEFAULT_BACKFILL_DAYS = 30
RATE_LIMIT_PAUSE_THRESHOLD = 10  # pause when fewer than this remain in the hour
RATE_LIMIT_BUFFER_SECONDS = 60  # extra wait past the reset to be safe

_BACKGROUND_TASKS: set = set()


def _window(job: BackfillJob) -> tuple[date, date]:
    """The (start, end) backfill window, anchored at job creation."""
    end = job.anchor_date or date.today()
    return end - timedelta(days=job.days_requested - 1), end


def _spawn(coro) -> None:
    """Launch a background task and hold a strong ref so it isn't GC'd."""
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


async def _active_job(session: AsyncSession, user_id) -> BackfillJob | None:
    result = await session.execute(
        select(BackfillJob)
        .where(BackfillJob.user_id == user_id)
        .where(BackfillJob.state.in_(BackfillJob.ACTIVE_STATES))
        .order_by(BackfillJob.started_at.desc())
    )
    return result.scalars().first()


async def latest_job(session: AsyncSession, user_id) -> BackfillJob | None:
    """Most recent backfill job for a user, any state (for status polling)."""
    result = await session.execute(
        select(BackfillJob)
        .where(BackfillJob.user_id == user_id)
        .order_by(BackfillJob.started_at.desc())
    )
    return result.scalars().first()


async def _pause(session: AsyncSession, job: BackfillJob, client: FitbitClient) -> None:
    """Mark the job paused, sleep until the quota resets, then mark running."""
    reset = client.rate_limit_reset or 3600
    wait = reset + RATE_LIMIT_BUFFER_SECONDS
    job.state = "paused_rate_limited"
    job.next_resume_at = datetime.now(timezone.utc) + timedelta(seconds=wait)
    await session.commit()
    logger.info(f"Backfill {job.id} paused for rate limit; resuming in {wait}s")
    await asyncio.sleep(wait)
    job.state = "running"
    job.next_resume_at = None
    await session.commit()


async def _run_ranges_phase(
    session: AsyncSession, user: User, client: FitbitClient, job: BackfillJob
) -> None:
    """Fetch the whole window via range endpoints. Retried as a unit on 429."""
    job.phase = "ranges"
    await session.commit()
    start, end = _window(job)
    while True:
        try:
            await sync_fitbit_range(session, user, start, end, client)
            await sync_fitbit_context(session, user, client)
            break
        except RateLimitError:
            await _pause(session, job, client)
    job.ranges_done = True
    await session.commit()
    logger.info(
        f"Backfill {job.id}: ranges phase complete for user {user.id} "
        f"(window {start}..{end})"
    )


async def _run_intraday_phase(
    session: AsyncSession, user: User, client: FitbitClient, job: BackfillJob
) -> None:
    """Per-day intraday, paced. Best-effort: 403 disables it via sync_fitbit_intraday."""
    job.phase = "intraday"
    await session.commit()
    start, end = _window(job)

    for i in range(job.days_done, job.days_requested):
        d = start + timedelta(days=i)

        # Proactive pacing: pause before we run out, not after a 429.
        if (
            client.rate_limit_remaining is not None
            and client.rate_limit_remaining <= RATE_LIMIT_PAUSE_THRESHOLD
        ):
            await _pause(session, job, client)

        try:
            await sync_fitbit_intraday(session, user, d, client)
        except RateLimitError:
            # Defensive fallback: pause until reset, then retry the same day.
            await _pause(session, job, client)
            await sync_fitbit_intraday(session, user, d, client)

        job.days_done = i + 1
        await session.commit()


async def run_backfill(user_id) -> None:
    """Entry point for the background task. Resumable from job progress."""
    async with async_session_maker() as session:
        job = await _active_job(session, user_id)
        if job is None:
            logger.warning(f"run_backfill: no active job for user {user_id}")
            return
        user = await session.get(User, user_id)
        if user is None or not user.fitbit_access_token:
            job.state = "failed"
            job.last_error = "no fitbit connection"
            await session.commit()
            return

        job.state = "running"
        await session.commit()
        logger.info(
            f"Backfill {job.id} started for user {user_id} "
            f"(ranges_done={job.ranges_done}, days_done={job.days_done}/{job.days_requested})"
        )

        try:
            token = await ensure_valid_token(user)
            client = FitbitClient(token)

            if not job.ranges_done:
                await _run_ranges_phase(session, user, client, job)

            await _run_intraday_phase(session, user, client, job)

            job.state = "done"
            job.finished_at = datetime.now(timezone.utc)
            await session.commit()
            logger.info(
                f"Backfill {job.id} complete for user {user_id}: "
                f"intraday {job.days_done}/{job.days_requested} days"
            )
        except TokenExpiredError:
            disconnect_fitbit(user)
            job.state = "failed"
            job.last_error = "token expired, disconnected"
            await session.commit()
        except Exception as e:  # noqa: BLE001 — record any failure for the UI
            logger.exception(f"Backfill {job.id} failed: {e}")
            job.state = "failed"
            job.last_error = str(e)
            await session.commit()


async def start_backfill(session: AsyncSession, user: User) -> BackfillJob:
    """Create (or return existing) backfill job and launch the background task."""
    existing = await _active_job(session, user.id)
    if existing is not None:
        return existing

    job = BackfillJob(
        user_id=user.id,
        state="pending",
        phase="ranges",
        days_requested=DEFAULT_BACKFILL_DAYS,
        days_done=0,
        ranges_done=False,
        anchor_date=date.today(),
    )
    session.add(job)
    await session.commit()

    # Own session inside the task — never reuse the request session.
    _spawn(run_backfill(user.id))
    return job


async def resume_incomplete_backfills() -> None:
    """On startup, relaunch any job left running/paused/pending by a restart."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(BackfillJob).where(BackfillJob.state.in_(BackfillJob.ACTIVE_STATES))
        )
        jobs = result.scalars().all()
    for job in jobs:
        logger.info(f"Resuming interrupted backfill {job.id} (user {job.user_id})")
        _spawn(run_backfill(job.user_id))
