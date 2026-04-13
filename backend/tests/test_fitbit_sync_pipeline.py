"""Tests for the Fitbit sync pipeline (scheduler.py typed-table distribution)."""

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from src.models.db_models import User
from src.models.fitbit_models import (
    DailyActivity,
    DailyBody,
    DailySleep,
    DailyVitals,
    HourlyIntraday,
    UserContext,
)
from src.scheduler import (
    sync_fitbit_context,
    sync_fitbit_daily,
    sync_fitbit_exercise_logs,
    sync_fitbit_intraday,
)
from tests.conftest import test_session_maker


def _make_user(**kwargs) -> User:
    defaults = {
        "id": uuid.uuid4(),
        "email": "test@test.com",
        "hashed_password": "hashed",
        "fitbit_access_token": "encrypted_token",
        "fitbit_refresh_token": "encrypted_refresh",
        "fitbit_token_expires": 9999999999,
    }
    defaults.update(kwargs)
    return User(**defaults)


def _mock_client_result():
    return {
        "data": {
            "heart_rate": {"resting_heart_rate": 62, "zones": {}},
            "hrv": {"daily_rmssd": 45.0, "deep_rmssd": 52.0},
            "spo2": {"avg": 97.5, "min": 95.0, "max": 99.0},
            "breathing_rate": {"breathing_rate": 15.0},
            "vo2_max": {"vo2_max": 42.0},
            "temperature": {"relative_deviation": -0.2},
            "sleep": [
                {
                    "external_id": "log_1",
                    "date_of_sleep": "2026-04-10",
                    "is_main_sleep": True,
                    "start_time": "2026-04-10T23:00:00",
                    "end_time": "2026-04-11T07:00:00",
                    "total_minutes": 480,
                    "deep_minutes": 80,
                    "light_minutes": 200,
                    "rem_minutes": 100,
                    "awake_minutes": 20,
                    "efficiency": 90,
                    "minutes_to_fall_asleep": 10,
                    "time_in_bed": 500,
                    "stages_30s_summary": {"transition_count": 30},
                },
            ],
            "activity": {
                "steps": 10000,
                "calories_burned": 2500,
                "distance_km": 8.0,
                "active_minutes": 45,
                "sedentary_minutes": 600,
                "lightly_active_minutes": 200,
                "floors": 10,
                "calories_bmr": 1600,
            },
            "active_zone_minutes": {
                "fat_burn_minutes": 30,
                "cardio_minutes": 15,
                "peak_minutes": 5,
                "total_minutes": 50,
            },
            "weight": {"weight_kg": 80.0, "bmi": 25.0, "body_fat_percent": 18.0},
        },
        "errors": [],
        "date": "2026-04-10",
    }


def _make_mock_client(result=None):
    """Create a mock FitbitClient with get_all_data_for_date returning result."""
    client = AsyncMock()
    client.get_all_data_for_date = AsyncMock(
        return_value=result or _mock_client_result()
    )
    return client


class TestSyncFitbitDaily:
    """Test sync_fitbit_daily distributes data to typed tables."""

    @pytest.mark.asyncio
    async def test_vitals_upserted(self):
        user = _make_user()
        sync_date = date(2026, 4, 10)
        client = _make_mock_client()

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            with patch("src.scheduler.upsert_metric", new_callable=AsyncMock):
                await sync_fitbit_daily(session, user, sync_date, client)

            from sqlalchemy import select

            row = (
                await session.execute(
                    select(DailyVitals).where(DailyVitals.user_id == user.id)
                )
            ).scalar_one()

            assert row.resting_heart_rate == 62
            assert row.daily_rmssd == 45.0
            assert row.deep_rmssd == 52.0
            assert row.spo2_avg == 97.5
            assert row.spo2_min == 95.0
            assert row.spo2_max == 99.0
            assert row.breathing_rate == 15.0
            assert row.vo2_max == 42.0
            assert row.temp_relative_deviation == -0.2

    @pytest.mark.asyncio
    async def test_sleep_upserted_with_date_of_sleep(self):
        user = _make_user()
        sync_date = date(2026, 4, 10)
        client = _make_mock_client()

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            with patch("src.scheduler.upsert_metric", new_callable=AsyncMock):
                await sync_fitbit_daily(session, user, sync_date, client)

            from sqlalchemy import select

            row = (
                await session.execute(
                    select(DailySleep).where(DailySleep.user_id == user.id)
                )
            ).scalar_one()

            assert row.external_id == "log_1"
            assert row.date == date(2026, 4, 10)
            assert row.total_minutes == 480
            assert row.is_main_sleep is True
            assert row.efficiency == 90

    @pytest.mark.asyncio
    async def test_activity_upserted(self):
        user = _make_user()
        sync_date = date(2026, 4, 10)
        client = _make_mock_client()

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            with patch("src.scheduler.upsert_metric", new_callable=AsyncMock):
                await sync_fitbit_daily(session, user, sync_date, client)

            from sqlalchemy import select

            row = (
                await session.execute(
                    select(DailyActivity).where(DailyActivity.user_id == user.id)
                )
            ).scalar_one()

            assert row.steps == 10000
            assert row.calories_burned == 2500
            assert row.distance_km == 8.0
            assert row.active_minutes == 45
            # AZM fields should also be set
            assert row.fat_burn_azm == 30
            assert row.cardio_azm == 15
            assert row.peak_azm == 5
            assert row.total_azm == 50

    @pytest.mark.asyncio
    async def test_body_upserted(self):
        user = _make_user()
        sync_date = date(2026, 4, 10)
        client = _make_mock_client()

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            with patch("src.scheduler.upsert_metric", new_callable=AsyncMock):
                await sync_fitbit_daily(session, user, sync_date, client)

            from sqlalchemy import select

            row = (
                await session.execute(
                    select(DailyBody).where(DailyBody.user_id == user.id)
                )
            ).scalar_one()

            assert row.weight_kg == 80.0
            assert row.bmi == 25.0
            assert row.body_fat_percent == 18.0

    @pytest.mark.asyncio
    async def test_sleep_fallback_to_sync_date(self):
        """If date_of_sleep is missing, use sync_date."""
        result = _mock_client_result()
        result["data"]["sleep"][0].pop("date_of_sleep")
        user = _make_user()
        sync_date = date(2026, 4, 11)
        client = _make_mock_client(result)

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            with patch("src.scheduler.upsert_metric", new_callable=AsyncMock):
                await sync_fitbit_daily(session, user, sync_date, client)

            from sqlalchemy import select

            row = (
                await session.execute(
                    select(DailySleep).where(DailySleep.user_id == user.id)
                )
            ).scalar_one()

            assert row.date == date(2026, 4, 11)

    @pytest.mark.asyncio
    async def test_empty_data_no_crash(self):
        """Empty result should not crash."""
        result = {"data": {}, "errors": [], "date": "2026-04-10"}
        user = _make_user()
        sync_date = date(2026, 4, 10)
        client = _make_mock_client(result)

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            with patch("src.scheduler.upsert_metric", new_callable=AsyncMock):
                await sync_fitbit_daily(session, user, sync_date, client)

            # Should complete without errors — no rows created
            from sqlalchemy import select

            vitals = (
                await session.execute(
                    select(DailyVitals).where(DailyVitals.user_id == user.id)
                )
            ).scalars().all()
            assert len(vitals) == 0


class TestSyncFitbitIntraday:
    """Test intraday sync with 403 handling."""

    @pytest.mark.asyncio
    async def test_403_flags_user(self):
        """On 403, user.fitbit_intraday_available should be set to False."""
        user = _make_user(fitbit_intraday_available=None)
        sync_date = date(2026, 4, 10)

        client = AsyncMock()
        client._make_request = AsyncMock(
            side_effect=Exception("API request failed: 403 Forbidden")
        )

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            await sync_fitbit_intraday(session, user, sync_date, client)

            assert user.fitbit_intraday_available is False

    @pytest.mark.asyncio
    async def test_pre_flagged_user_skipped(self):
        """If fitbit_intraday_available is False, skip entirely."""
        user = _make_user(fitbit_intraday_available=False)
        sync_date = date(2026, 4, 10)
        client = AsyncMock()

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            await sync_fitbit_intraday(session, user, sync_date, client)

            # _make_request should never be called
            client._make_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_success_sets_flag_true(self):
        """If intraday succeeds and flag was None, set to True."""
        user = _make_user(fitbit_intraday_available=None)
        sync_date = date(2026, 4, 10)

        # Return valid intraday data for each endpoint
        client = AsyncMock()
        client._make_request = AsyncMock(
            return_value={
                "activities-heart-intraday": {
                    "dataset": [
                        {"time": "08:00:00", "value": 72},
                        {"time": "08:01:00", "value": 75},
                    ]
                },
                "activities-steps-intraday": {
                    "dataset": [
                        {"time": "08:00:00", "value": 10},
                    ]
                },
                "activities-active-zone-minutes-intraday": {
                    "dataset": [
                        {"time": "08:00:00", "value": 1},
                    ]
                },
            }
        )

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            await sync_fitbit_intraday(session, user, sync_date, client)

            assert user.fitbit_intraday_available is True

    @pytest.mark.asyncio
    async def test_intraday_data_upserted(self):
        """Verify hourly data actually lands in hourly_intraday table."""
        user = _make_user(fitbit_intraday_available=True)
        sync_date = date(2026, 4, 10)

        # Return data only for the heart_rate key (first endpoint called)
        async def mock_request(url):
            if "heart" in url:
                return {
                    "activities-heart-intraday": {
                        "dataset": [
                            {"time": "10:00:00", "value": 65},
                            {"time": "10:30:00", "value": 70},
                            {"time": "11:00:00", "value": 80},
                        ]
                    }
                }
            return {}

        client = AsyncMock()
        client._make_request = AsyncMock(side_effect=mock_request)

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            await sync_fitbit_intraday(session, user, sync_date, client)

            from sqlalchemy import select

            rows = (
                await session.execute(
                    select(HourlyIntraday).where(
                        HourlyIntraday.user_id == user.id,
                        HourlyIntraday.metric_type == "heart_rate",
                    )
                )
            ).scalars().all()

            # Should have hour 10 and hour 11
            hours = {r.hour for r in rows}
            assert 10 in hours
            assert 11 in hours

    @pytest.mark.asyncio
    async def test_non_403_error_raises(self):
        """Non-403 errors should propagate."""
        user = _make_user(fitbit_intraday_available=None)
        sync_date = date(2026, 4, 10)

        client = AsyncMock()
        client._make_request = AsyncMock(
            side_effect=Exception("API request failed: 500 Internal Server Error")
        )

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            with pytest.raises(Exception, match="500"):
                await sync_fitbit_intraday(session, user, sync_date, client)


class TestSyncFitbitContext:
    """Test profile + device context sync."""

    @pytest.mark.asyncio
    async def test_context_upserted(self):
        user = _make_user()
        client = AsyncMock()
        client.get_profile = AsyncMock(
            return_value={
                "user": {
                    "dateOfBirth": "1990-05-15",
                    "gender": "MALE",
                    "height": 180.0,
                    "timezone": "America/New_York",
                    "offsetFromUTCMillis": -18000000,
                    "strideLengthWalking": 72.5,
                    "strideLengthRunning": 95.0,
                }
            }
        )
        client.get_devices = AsyncMock(
            return_value=[
                {
                    "deviceVersion": "Charge 5",
                    "batteryLevel": 85,
                    "lastSyncTime": "2026-04-10T10:00:00",
                }
            ]
        )

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            await sync_fitbit_context(session, user, client)

            from sqlalchemy import select

            row = (
                await session.execute(
                    select(UserContext).where(UserContext.user_id == user.id)
                )
            ).scalar_one()

            assert row.date_of_birth == date(1990, 5, 15)
            assert row.gender == "MALE"
            assert row.height_cm == 180.0
            assert row.device_model == "Charge 5"
            assert row.device_battery == 85

    @pytest.mark.asyncio
    async def test_devices_403_skipped(self):
        """Devices 403 should be caught, profile still saved."""
        user = _make_user()
        client = AsyncMock()
        client.get_profile = AsyncMock(
            return_value={
                "user": {
                    "dateOfBirth": "1990-05-15",
                    "gender": "FEMALE",
                }
            }
        )
        client.get_devices = AsyncMock(
            side_effect=Exception("API request failed: 403 Forbidden")
        )

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            await sync_fitbit_context(session, user, client)

            from sqlalchemy import select

            row = (
                await session.execute(
                    select(UserContext).where(UserContext.user_id == user.id)
                )
            ).scalar_one()

            assert row.gender == "FEMALE"
            assert row.device_model is None


class TestSyncFitbitExerciseLogs:
    """Test exercise log sync."""

    @pytest.mark.asyncio
    async def test_exercise_logs_upserted(self):
        user = _make_user()
        sync_date = date(2026, 4, 10)
        client = AsyncMock()
        client.get_exercise_logs = AsyncMock(
            return_value={
                "activities": [
                    {
                        "logId": 12345,
                        "activityName": "Run",
                        "startTime": "2026-04-10T07:00:00",
                        "activeDuration": 1800000,
                        "averageHeartRate": 145,
                        "calories": 350,
                        "distance": 5.5,
                        "elevationGain": 20.0,
                        "speed": 11.0,
                        "logType": "auto_detected",
                        "heartRateZones": [],
                    }
                ]
            }
        )

        async with test_session_maker() as session:
            session.add(user)
            await session.flush()

            await sync_fitbit_exercise_logs(session, user, sync_date, client)

            from sqlalchemy import select
            from src.models.fitbit_models import ExerciseLog

            row = (
                await session.execute(
                    select(ExerciseLog).where(ExerciseLog.user_id == user.id)
                )
            ).scalar_one()

            assert row.external_id == "12345"
            assert row.activity_name == "Run"
            assert row.duration_minutes == 30
            assert row.calories == 350
