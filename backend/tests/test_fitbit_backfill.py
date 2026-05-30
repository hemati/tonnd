import uuid
from datetime import datetime, timezone

import pytest

from src.models.db_models import User
from src.models.backfill_models import BackfillJob
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
