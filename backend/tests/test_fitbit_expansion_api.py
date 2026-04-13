"""Tests for typed-table API endpoints — query + serialization layer."""

import uuid
from datetime import date, datetime, timezone

import pytest

from src.models.fitbit_models import (
    DailyActivity,
    DailyBody,
    DailySleep,
    DailyVitals,
    ExerciseLog,
    HourlyIntraday,
    UserContext,
)
from src.services.data_service import (
    query_daily_activity,
    query_daily_body,
    query_daily_sleep,
    query_daily_vitals,
    query_exercise_logs,
    query_hourly_intraday,
    query_user_context,
)
from tests.conftest import test_session_maker

USER_ID = uuid.uuid4()


@pytest.mark.asyncio
class TestQueryDailyVitals:
    async def test_returns_rows_ordered_by_date_desc(self):
        async with test_session_maker() as session:
            for d in [date(2026, 4, 8), date(2026, 4, 10), date(2026, 4, 9)]:
                session.add(DailyVitals(
                    user_id=USER_ID, date=d, source="fitbit",
                    resting_heart_rate=62.0, spo2_avg=97.5,
                ))
            await session.commit()

            rows = await query_daily_vitals(session, USER_ID, limit=10)
            dates = [r.date for r in rows]
            assert dates == [date(2026, 4, 10), date(2026, 4, 9), date(2026, 4, 8)]

    async def test_filter_by_date_range(self):
        async with test_session_maker() as session:
            for d in [date(2026, 4, 1), date(2026, 4, 5), date(2026, 4, 10)]:
                session.add(DailyVitals(
                    user_id=USER_ID, date=d, source="fitbit",
                    resting_heart_rate=60.0,
                ))
            await session.commit()

            rows = await query_daily_vitals(
                session, USER_ID,
                start_date=date(2026, 4, 3), end_date=date(2026, 4, 7),
            )
            assert len(rows) == 1
            assert rows[0].date == date(2026, 4, 5)

    async def test_serialization_shape(self):
        async with test_session_maker() as session:
            session.add(DailyVitals(
                user_id=USER_ID, date=date(2026, 4, 10), source="fitbit",
                resting_heart_rate=62.0, daily_rmssd=45.3,
                spo2_avg=97.5, breathing_rate=15.2,
            ))
            await session.commit()

            rows = await query_daily_vitals(session, USER_ID, limit=1)
            r = rows[0]
            # Verify all expected attributes exist and are correct types
            assert r.date.isoformat() == "2026-04-10"
            assert r.source == "fitbit"
            assert r.resting_heart_rate == 62.0
            assert r.daily_rmssd == 45.3
            assert r.spo2_avg == 97.5
            assert r.breathing_rate == 15.2
            assert r.vo2_max is None


@pytest.mark.asyncio
class TestQueryDailySleep:
    async def test_returns_sleep_rows(self):
        async with test_session_maker() as session:
            session.add(DailySleep(
                user_id=USER_ID, date=date(2026, 4, 10), source="fitbit",
                external_id="sleep_main", is_main_sleep=True,
                total_minutes=420, deep_minutes=90, rem_minutes=110,
                efficiency=88,
            ))
            session.add(DailySleep(
                user_id=USER_ID, date=date(2026, 4, 10), source="fitbit",
                external_id="sleep_nap", is_main_sleep=False,
                total_minutes=25, efficiency=70,
            ))
            await session.commit()

            rows = await query_daily_sleep(session, USER_ID, limit=10)
            assert len(rows) == 2
            totals = sorted([r.total_minutes for r in rows], reverse=True)
            assert totals == [420, 25]


@pytest.mark.asyncio
class TestQueryDailyActivity:
    async def test_returns_activity_with_azm(self):
        async with test_session_maker() as session:
            session.add(DailyActivity(
                user_id=USER_ID, date=date(2026, 4, 10), source="fitbit",
                steps=12000, calories_burned=2600, active_minutes=55,
                fat_burn_azm=30, cardio_azm=15, peak_azm=5, total_azm=50,
            ))
            await session.commit()

            rows = await query_daily_activity(session, USER_ID)
            assert len(rows) == 1
            r = rows[0]
            assert r.steps == 12000
            assert r.total_azm == 50


@pytest.mark.asyncio
class TestQueryDailyBody:
    async def test_returns_body_metrics(self):
        async with test_session_maker() as session:
            session.add(DailyBody(
                user_id=USER_ID, date=date(2026, 4, 10), source="fitbit",
                weight_kg=80.5, bmi=24.3, body_fat_percent=18.5,
            ))
            await session.commit()

            rows = await query_daily_body(session, USER_ID)
            assert len(rows) == 1
            assert rows[0].weight_kg == 80.5


@pytest.mark.asyncio
class TestQueryHourlyIntraday:
    async def test_filter_by_metric_type_and_hour_range(self):
        async with test_session_maker() as session:
            for hour in range(0, 24):
                session.add(HourlyIntraday(
                    user_id=USER_ID, date=date(2026, 4, 10), hour=hour,
                    metric_type="heart_rate", source="fitbit",
                    avg_value=70.0 + hour, min_value=60.0, max_value=100.0,
                    sample_count=60,
                ))
            await session.commit()

            rows = await query_hourly_intraday(
                session, USER_ID, "heart_rate",
                start_hour=8, end_hour=12,
            )
            assert len(rows) == 5  # hours 8, 9, 10, 11, 12
            assert all(r.metric_type == "heart_rate" for r in rows)
            assert rows[0].hour == 8


@pytest.mark.asyncio
class TestQueryExerciseLogs:
    async def test_returns_exercise_logs(self):
        async with test_session_maker() as session:
            session.add(ExerciseLog(
                user_id=USER_ID, date=date(2026, 4, 10), source="fitbit",
                external_id="fb_run_1", activity_name="Run",
                duration_minutes=30, avg_heart_rate=155, calories=350,
            ))
            session.add(ExerciseLog(
                user_id=USER_ID, date=date(2026, 4, 9), source="fitbit",
                external_id="fb_bike_1", activity_name="Bike",
                duration_minutes=45, avg_heart_rate=140, calories=500,
            ))
            await session.commit()

            rows = await query_exercise_logs(session, USER_ID, limit=10)
            assert len(rows) == 2
            # desc order: most recent first
            assert rows[0].activity_name == "Run"
            assert rows[1].activity_name == "Bike"


@pytest.mark.asyncio
class TestQueryUserContext:
    async def test_returns_context_with_age_computation(self):
        async with test_session_maker() as session:
            session.add(UserContext(
                user_id=USER_ID, source="fitbit",
                date_of_birth=date(1990, 5, 15), gender="male",
                height_cm=180.0, timezone="America/New_York",
            ))
            await session.commit()

            rows = await query_user_context(session, USER_ID)
            assert len(rows) == 1
            r = rows[0]
            assert r.gender == "male"
            assert r.height_cm == 180.0

            # Test age computation via to_dict()
            d = r.to_dict()
            assert d["age"] is not None
            assert 35 <= d["age"] <= 36  # born 1990-05-15, test in 2026

    async def test_to_dict_age_none_when_no_dob(self):
        async with test_session_maker() as session:
            session.add(UserContext(
                user_id=USER_ID, source="fitbit", gender="male",
            ))
            await session.commit()
            rows = await query_user_context(session, USER_ID)
            assert rows[0].to_dict()["age"] is None

    async def test_filter_by_source(self):
        async with test_session_maker() as session:
            session.add(UserContext(
                user_id=USER_ID, source="fitbit",
                height_cm=180.0,
            ))
            session.add(UserContext(
                user_id=USER_ID, source="whoop",
                height_cm=180.5,
            ))
            await session.commit()

            rows = await query_user_context(session, USER_ID, source="fitbit")
            assert len(rows) == 1
            assert rows[0].source == "fitbit"
