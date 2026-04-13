"""Tests for typed Fitbit tables — schema, constraints, and basic CRUD."""

import uuid
from datetime import date, datetime, timezone

import pytest

from src.models.fitbit_models import (
    DailyActivity,
    DailyNutrition,
    DailySleep,
    DailyVitals,
    ExerciseLog,
    HourlyIntraday,
    UserContext,
)
from src.services.fitbit_sync_utils import (
    upsert_daily_activity,
    upsert_daily_activity_azm,
    upsert_daily_sleep,
    upsert_daily_vitals,
    upsert_exercise_log,
    upsert_hourly_intraday,
    upsert_user_context,
)

from tests.conftest import test_session_maker


@pytest.mark.asyncio
class TestDailyVitals:
    async def test_insert_and_read(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            row = DailyVitals(
                user_id=uid,
                date=date(2026, 4, 10),
                source="fitbit",
                resting_heart_rate=62.0,
                daily_rmssd=45.3,
                spo2_avg=97.5,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            assert row.resting_heart_rate == 62.0
            assert row.source == "fitbit"

    async def test_unique_constraint_user_date_source(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 4, 10)
            session.add(DailyVitals(user_id=uid, date=d, source="fitbit", resting_heart_rate=60))
            await session.commit()
            session.add(DailyVitals(user_id=uid, date=d, source="fitbit", resting_heart_rate=62))
            with pytest.raises(Exception):  # IntegrityError
                await session.commit()

    async def test_different_sources_same_date_ok(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 4, 10)
            session.add(DailyVitals(user_id=uid, date=d, source="fitbit", resting_heart_rate=60))
            session.add(DailyVitals(user_id=uid, date=d, source="whoop", resting_heart_rate=61))
            await session.commit()  # Should not raise


@pytest.mark.asyncio
class TestDailySleep:
    async def test_multiple_sleeps_per_day(self):
        """Main sleep + nap should both be stored."""
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 4, 10)
            session.add(DailySleep(
                user_id=uid, date=d, source="fitbit", external_id="log_main",
                is_main_sleep=True, total_minutes=420, efficiency=88,
            ))
            session.add(DailySleep(
                user_id=uid, date=d, source="fitbit", external_id="log_nap1",
                is_main_sleep=False, total_minutes=25, efficiency=70,
            ))
            session.add(DailySleep(
                user_id=uid, date=d, source="fitbit", external_id="log_nap2",
                is_main_sleep=False, total_minutes=20, efficiency=65,
            ))
            await session.commit()  # 3 entries — no constraint violation


@pytest.mark.asyncio
class TestHourlyIntraday:
    async def test_insert_hourly_data(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 4, 10)
            session.add(HourlyIntraday(
                user_id=uid, date=d, hour=14, metric_type="heart_rate",
                source="fitbit", avg_value=85.0, min_value=62.0,
                max_value=145.0, sample_count=60,
            ))
            await session.commit()

    async def test_extra_jsonb_for_hrv(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            session.add(HourlyIntraday(
                user_id=uid, date=date(2026, 4, 10), hour=3,
                metric_type="hrv", source="fitbit",
                avg_value=42.0, min_value=30.0, max_value=55.0,
                sample_count=12,
                extra={"avg_hf": 120.5, "avg_lf": 85.3},
            ))
            await session.commit()


@pytest.mark.asyncio
class TestExerciseLog:
    async def test_dedup_by_external_id(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            session.add(ExerciseLog(
                user_id=uid, date=date(2026, 4, 10), source="fitbit",
                external_id="fitbit_123", activity_name="Run",
                duration_minutes=30,
            ))
            await session.commit()
            session.add(ExerciseLog(
                user_id=uid, date=date(2026, 4, 10), source="fitbit",
                external_id="fitbit_123", activity_name="Run Updated",
                duration_minutes=31,
            ))
            with pytest.raises(Exception):
                await session.commit()


@pytest.mark.asyncio
class TestUserContext:
    async def test_one_per_user_per_source(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            session.add(UserContext(
                user_id=uid, source="fitbit",
                date_of_birth=date(1990, 5, 15), gender="male",
                height_cm=180.0, timezone="Europe/Berlin",
            ))
            await session.commit()


# ─── Upsert function tests ───────────────────────────────────────────


@pytest.mark.asyncio
class TestUpsertDailyVitals:
    async def test_insert_new(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            await upsert_daily_vitals(session, uid, date(2026, 4, 10), "fitbit",
                                      resting_heart_rate=62.0, daily_rmssd=45.0)
            await session.commit()
            from sqlalchemy import select
            row = (await session.execute(
                select(DailyVitals).where(DailyVitals.user_id == uid)
            )).scalar_one()
            assert row.resting_heart_rate == 62.0
            assert row.daily_rmssd == 45.0

    async def test_update_existing(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            await upsert_daily_vitals(session, uid, date(2026, 4, 10), "fitbit",
                                      resting_heart_rate=62.0)
            await session.commit()
            await upsert_daily_vitals(session, uid, date(2026, 4, 10), "fitbit",
                                      resting_heart_rate=64.0, spo2_avg=97.0)
            await session.commit()
            from sqlalchemy import select
            row = (await session.execute(
                select(DailyVitals).where(DailyVitals.user_id == uid)
            )).scalar_one()
            assert row.resting_heart_rate == 64.0
            assert row.spo2_avg == 97.0


@pytest.mark.asyncio
class TestUpsertDailyActivitySeparate:
    async def test_activity_and_azm_write_same_row(self):
        """Activity upsert + AZM upsert target same row without overwriting each other."""
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 4, 10)
            await upsert_daily_activity(session, uid, d, "fitbit",
                                        steps=10000, calories_burned=2500)
            await session.commit()
            await upsert_daily_activity_azm(session, uid, d, "fitbit",
                                            fat_burn_azm=30, cardio_azm=15,
                                            peak_azm=5, total_azm=50)
            await session.commit()
            from sqlalchemy import select
            row = (await session.execute(
                select(DailyActivity).where(DailyActivity.user_id == uid)
            )).scalar_one()
            assert row.steps == 10000
            assert row.fat_burn_azm == 30

    async def test_azm_failure_leaves_activity_intact(self):
        """If AZM never runs, activity fields are still present."""
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 4, 10)
            await upsert_daily_activity(session, uid, d, "fitbit",
                                        steps=8000, active_minutes=45)
            await session.commit()
            from sqlalchemy import select
            row = (await session.execute(
                select(DailyActivity).where(DailyActivity.user_id == uid)
            )).scalar_one()
            assert row.steps == 8000
            assert row.fat_burn_azm is None


@pytest.mark.asyncio
class TestUpsertExerciseLog:
    async def test_upsert_by_external_id(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            await upsert_exercise_log(session, uid, "fb_123", "fitbit",
                                      date=date(2026, 4, 10),
                                      activity_name="Run", duration_minutes=30)
            await session.commit()
            await upsert_exercise_log(session, uid, "fb_123", "fitbit",
                                      date=date(2026, 4, 10),
                                      activity_name="Run", duration_minutes=32,
                                      avg_heart_rate=155)
            await session.commit()
            from sqlalchemy import select
            rows = (await session.execute(
                select(ExerciseLog).where(ExerciseLog.user_id == uid)
            )).scalars().all()
            assert len(rows) == 1
            assert rows[0].duration_minutes == 32
            assert rows[0].avg_heart_rate == 155
