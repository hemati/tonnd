import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from src.models.db_models import User
from src.models.backfill_models import BackfillJob
from src.services.fitbit.client import RateLimitError
from tests.conftest import test_session_maker


def _make_user(**kw):
    d = {
        "id": uuid.uuid4(),
        "email": "b@test.com",
        "hashed_password": "x",
        "fitbit_access_token": "tok",
    }
    d.update(kw)
    return User(**d)


@pytest.mark.asyncio
async def test_backfill_job_persists_and_to_dict():
    user = _make_user()
    async with test_session_maker() as session:
        session.add(user)
        await session.flush()
        job = BackfillJob(
            user_id=user.id,
            state="pending",
            phase="ranges",
            days_requested=30,
            days_done=0,
            ranges_done=False,
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
    job = BackfillJob(
        user_id=user.id,
        state="running",
        phase="intraday",
        days_requested=2,
        days_done=0,
        ranges_done=True,
    )
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
        with (
            patch("src.services.fitbit.backfill.asyncio.sleep", fake_sleep),
            patch("src.services.fitbit.backfill.sync_fitbit_intraday", new=AsyncMock()),
        ):
            await backfill._run_intraday_phase(session, user, client, job)

    assert slept and slept[0] >= 5  # paused at least until reset
    assert job.days_done == 2
    assert job.state == "running"


@pytest.mark.asyncio
async def test_run_intraday_phase_429_pauses_and_retries():
    """A 429 on a day pauses, then retries the same day (never aborts)."""
    from src.services.fitbit import backfill

    user = _make_user()
    job = BackfillJob(
        user_id=user.id,
        state="running",
        phase="intraday",
        days_requested=1,
        days_done=0,
        ranges_done=True,
    )
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
        with (
            patch("src.services.fitbit.backfill.asyncio.sleep", new=AsyncMock()),
            patch("src.services.fitbit.backfill.sync_fitbit_intraday", new=flaky),
        ):
            await backfill._run_intraday_phase(session, user, client, job)

    assert calls["n"] == 2  # failed once, retried once
    assert job.days_done == 1


@pytest.mark.asyncio
async def test_run_backfill_full_state_transition():
    """run_backfill: pending -> running -> done, ranges then intraday."""
    from src.services.fitbit import backfill

    user = _make_user()
    job = BackfillJob(
        user_id=user.id,
        state="pending",
        phase="ranges",
        days_requested=30,
        days_done=0,
        ranges_done=False,
    )
    client = _client_ok()

    async with test_session_maker() as session:
        session.add_all([user, job])
        await session.commit()

    with (
        patch("src.services.fitbit.backfill.async_session_maker", test_session_maker),
        patch(
            "src.services.fitbit.backfill.ensure_valid_token",
            new=AsyncMock(return_value="tok"),
        ),
        patch("src.services.fitbit.backfill.FitbitClient", return_value=client),
        patch("src.services.fitbit.backfill.sync_fitbit_range", new=AsyncMock()),
        patch("src.services.fitbit.backfill.sync_fitbit_intraday", new=AsyncMock()),
        patch("src.services.fitbit.backfill.sync_fitbit_context", new=AsyncMock()),
    ):
        await backfill.run_backfill(user.id)

    async with test_session_maker() as session:
        refreshed = (
            (
                await session.execute(
                    select(BackfillJob).where(BackfillJob.user_id == user.id)
                )
            )
            .scalars()
            .one()
        )
    assert refreshed.state == "done"
    assert refreshed.ranges_done is True
    assert refreshed.days_done == 30
    assert refreshed.finished_at is not None


@pytest.mark.asyncio
async def test_intraday_phase_window_uses_anchor_date():
    """Resume maps day-index to the anchored window, not date.today()."""
    from src.services.fitbit import backfill

    user = _make_user()
    anchor = date(2026, 1, 10)
    job = BackfillJob(
        user_id=user.id,
        state="running",
        phase="intraday",
        days_requested=2,
        days_done=0,
        ranges_done=True,
        anchor_date=anchor,
    )
    client = _client_ok()
    seen = []

    async def capture(session, u, d, c):
        seen.append(d)

    async with test_session_maker() as session:
        session.add_all([user, job])
        await session.flush()
        with patch("src.services.fitbit.backfill.sync_fitbit_intraday", new=capture):
            await backfill._run_intraday_phase(session, user, client, job)

    assert seen == [date(2026, 1, 9), date(2026, 1, 10)]  # anchor-1 .. anchor


@pytest.mark.asyncio
async def test_backfill_endpoints(client, monkeypatch):
    """POST returns 202 + job; a second POST returns the same job; GET reflects state."""
    from app import app
    from src.services.user_service import current_active_user  # same object app.py uses
    import src.services.fitbit.backfill as bf

    # Don't actually launch the background task in the endpoint test.
    monkeypatch.setattr(bf, "_spawn", lambda coro: coro.close())

    user = _make_user()
    async with test_session_maker() as session:
        session.add(user)
        await session.commit()

    app.dependency_overrides[current_active_user] = lambda: user
    try:
        r1 = await client.post("/api/fitbit/backfill")
        assert r1.status_code == 202
        body1 = r1.json()
        assert body1["state"] in ("pending", "running")
        assert body1["days_requested"] == 30

        r2 = await client.post("/api/fitbit/backfill")
        assert r2.json()["id"] == body1["id"]  # no duplicate job

        g = await client.get("/api/fitbit/backfill")
        assert g.status_code == 200
        assert g.json()["id"] == body1["id"]
    finally:
        app.dependency_overrides.pop(current_active_user, None)


@pytest.mark.asyncio
async def test_resume_incomplete_backfills_relaunches(monkeypatch):
    from src.services.fitbit import backfill

    user = _make_user()
    job = BackfillJob(user_id=user.id, state="paused_rate_limited",
                      phase="intraday", days_requested=30, days_done=12,
                      ranges_done=True)
    async with test_session_maker() as session:
        session.add_all([user, job])
        await session.commit()

    launched = []
    # Patch the spawn helper: capture the coro and close it (no real task).
    monkeypatch.setattr(backfill, "_spawn",
                        lambda coro: launched.append(coro) or coro.close())
    monkeypatch.setattr(backfill, "async_session_maker", test_session_maker)

    await backfill.resume_incomplete_backfills()
    assert len(launched) == 1  # the paused job was relaunched
