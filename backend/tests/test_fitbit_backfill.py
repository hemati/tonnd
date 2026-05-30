import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from src.models.db_models import User
from src.models.backfill_models import BackfillJob
from src.services.fitbit.client import RateLimitError
from tests.conftest import test_session_maker


def _make_user(**kw):
    d = {"id": uuid.uuid4(), "email": "b@test.com", "hashed_password": "x",
         "fitbit_access_token": "tok"}
    d.update(kw)
    return User(**d)


@pytest.mark.asyncio
async def test_backfill_job_persists_and_to_dict():
    user = _make_user()
    async with test_session_maker() as session:
        session.add(user)
        await session.flush()
        job = BackfillJob(
            user_id=user.id, state="pending", phase="ranges",
            days_requested=30, days_done=0, ranges_done=False,
            started_at=datetime(2026, 5, 30, tzinfo=timezone.utc),
        )
        session.add(job)
        await session.commit()
        d = job.to_dict()
    assert d["state"] == "pending"
    assert d["days_requested"] == 30
    assert d["days_done"] == 0
    assert d["ranges_done"] is False
    assert d["next_resume_at"] is None


def _client_ok():
    c = AsyncMock()
    c.rate_limit_remaining = 100
    c.rate_limit_reset = 3600
    c.get_all_data_for_range = AsyncMock(return_value={})
    c.get_exercise_logs = AsyncMock(return_value={})
    return c


@pytest.mark.asyncio
async def test_run_intraday_phase_pauses_when_remaining_low():
    """When Remaining <= threshold the pacer sleeps and marks paused, then resumes."""
    from src.services.fitbit import backfill

    user = _make_user()
    job = BackfillJob(user_id=user.id, state="running", phase="intraday",
                      days_requested=2, days_done=0, ranges_done=True)
    client = _client_ok()
    client.rate_limit_remaining = backfill.RATE_LIMIT_PAUSE_THRESHOLD  # trip pause
    client.rate_limit_reset = 5
    slept = []

    async def fake_sleep(secs):
        slept.append(secs)
        client.rate_limit_remaining = 100  # quota restored after the wait

    async with test_session_maker() as session:
        session.add_all([user, job])
        await session.flush()
        with patch("src.services.fitbit.backfill.asyncio.sleep", fake_sleep), \
             patch("src.services.fitbit.backfill.sync_fitbit_intraday",
                   new=AsyncMock()):
            await backfill._run_intraday_phase(session, user, client, job)

    assert slept and slept[0] >= 5  # paused at least until reset
    assert job.days_done == 2
    assert job.state == "running"


@pytest.mark.asyncio
async def test_run_intraday_phase_429_pauses_and_retries():
    """A 429 on a day pauses, then retries the same day (never aborts)."""
    from src.services.fitbit import backfill

    user = _make_user()
    job = BackfillJob(user_id=user.id, state="running", phase="intraday",
                      days_requested=1, days_done=0, ranges_done=True)
    client = _client_ok()
    client.rate_limit_reset = 3
    calls = {"n": 0}

    async def flaky(session, u, d, c):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RateLimitError("429")

    async with test_session_maker() as session:
        session.add_all([user, job])
        await session.flush()
        with patch("src.services.fitbit.backfill.asyncio.sleep", new=AsyncMock()), \
             patch("src.services.fitbit.backfill.sync_fitbit_intraday", new=flaky):
            await backfill._run_intraday_phase(session, user, client, job)

    assert calls["n"] == 2  # failed once, retried once
    assert job.days_done == 1


@pytest.mark.asyncio
async def test_run_backfill_full_state_transition():
    """run_backfill: pending -> running -> done, ranges then intraday."""
    from src.services.fitbit import backfill

    user = _make_user()
    job = BackfillJob(user_id=user.id, state="pending", phase="ranges",
                      days_requested=30, days_done=0, ranges_done=False)
    client = _client_ok()

    async with test_session_maker() as session:
        session.add_all([user, job])
        await session.commit()

    with patch("src.services.fitbit.backfill.async_session_maker", test_session_maker), \
         patch("src.services.fitbit.backfill.ensure_valid_token",
               new=AsyncMock(return_value="tok")), \
         patch("src.services.fitbit.backfill.FitbitClient", return_value=client), \
         patch("src.services.fitbit.backfill.sync_fitbit_range", new=AsyncMock()), \
         patch("src.services.fitbit.backfill.sync_fitbit_intraday", new=AsyncMock()), \
         patch("src.services.fitbit.backfill.sync_fitbit_context", new=AsyncMock()):
        await backfill.run_backfill(user.id)

    async with test_session_maker() as session:
        refreshed = (await session.execute(
            select(BackfillJob).where(BackfillJob.user_id == user.id)
        )).scalars().one()
    assert refreshed.state == "done"
    assert refreshed.ranges_done is True
    assert refreshed.days_done == 30
    assert refreshed.finished_at is not None
