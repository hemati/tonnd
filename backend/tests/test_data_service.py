"""Tests for the shared data service (query_metrics, compute_recovery_score)."""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import FitnessMetric
from src.services.data_service import (
    compute_recovery_score,
    get_latest,
    metric_to_dict,
    query_metrics,
)

from tests.conftest import test_session_maker


async def _seed_metric(session, user_id, d, metric_type, source, data):
    session.add(FitnessMetric(
        user_id=user_id, date=d, metric_type=metric_type,
        source=source, data=data,
    ))


@pytest.mark.asyncio
class TestQueryMetrics:
    async def test_filters_by_user(self):
        async with test_session_maker() as session:
            u1, u2 = uuid.uuid4(), uuid.uuid4()
            today = date.today()
            await _seed_metric(session, u1, today, "heart_rate", "fitbit", {"resting_heart_rate": 60})
            await _seed_metric(session, u2, today, "heart_rate", "fitbit", {"resting_heart_rate": 70})
            await session.commit()

            rows = await query_metrics(session, u1)
            assert len(rows) == 1
            assert rows[0].data["resting_heart_rate"] == 60

    async def test_filters_by_metric_type(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            today = date.today()
            await _seed_metric(session, uid, today, "heart_rate", "fitbit", {"resting_heart_rate": 60})
            await _seed_metric(session, uid, today, "sleep", "fitbit", {"total_minutes": 420})
            await session.commit()

            rows = await query_metrics(session, uid, metric_types=["sleep"])
            assert len(rows) == 1
            assert rows[0].metric_type == "sleep"

    async def test_filters_by_date_range(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            old = date.today() - timedelta(days=30)
            recent = date.today() - timedelta(days=2)
            await _seed_metric(session, uid, old, "heart_rate", "fitbit", {})
            await _seed_metric(session, uid, recent, "heart_rate", "fitbit", {})
            await session.commit()

            rows = await query_metrics(
                session, uid,
                start_date=date.today() - timedelta(days=7),
            )
            assert len(rows) == 1

    async def test_filters_by_source(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            today = date.today()
            await _seed_metric(session, uid, today, "weight", "fitbit", {"weight_kg": 75})
            await _seed_metric(session, uid, today, "weight", "renpho", {"weight_kg": 74.8})
            await session.commit()

            rows = await query_metrics(session, uid, source="renpho")
            assert len(rows) == 1
            assert rows[0].source == "renpho"

    async def test_pagination(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            for i in range(10):
                d = date.today() - timedelta(days=i)
                await _seed_metric(session, uid, d, "heart_rate", "fitbit", {"rhr": 60 + i})
            await session.commit()

            page1 = await query_metrics(session, uid, limit=3, offset=0)
            page2 = await query_metrics(session, uid, limit=3, offset=3)
            assert len(page1) == 3
            assert len(page2) == 3
            assert page1[0].date != page2[0].date

    async def test_order_asc(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d1 = date.today() - timedelta(days=5)
            d2 = date.today()
            await _seed_metric(session, uid, d1, "heart_rate", "fitbit", {})
            await _seed_metric(session, uid, d2, "heart_rate", "fitbit", {})
            await session.commit()

            rows = await query_metrics(session, uid, order="asc")
            assert rows[0].date < rows[1].date

    async def test_order_desc(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d1 = date.today() - timedelta(days=5)
            d2 = date.today()
            await _seed_metric(session, uid, d1, "heart_rate", "fitbit", {})
            await _seed_metric(session, uid, d2, "heart_rate", "fitbit", {})
            await session.commit()

            rows = await query_metrics(session, uid, order="desc")
            assert rows[0].date > rows[1].date

    async def test_end_date_filter(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            await _seed_metric(session, uid, date.today(), "hrv", "fitbit", {})
            await _seed_metric(session, uid, date.today() - timedelta(days=60), "hrv", "fitbit", {})
            await session.commit()

            rows = await query_metrics(
                session, uid, end_date=date.today() - timedelta(days=30)
            )
            assert len(rows) == 1


class TestMetricToDict:
    def test_basic_conversion(self):
        m = FitnessMetric(
            user_id=uuid.uuid4(),
            date=date(2026, 4, 10),
            metric_type="heart_rate",
            source="fitbit",
            data={"resting_heart_rate": 62},
        )
        result = metric_to_dict(m)
        assert result["date"] == "2026-04-10"
        assert result["metric_type"] == "heart_rate"
        assert result["source"] == "fitbit"
        assert result["resting_heart_rate"] == 62


@pytest.mark.asyncio
class TestGetLatest:
    async def test_returns_latest(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            await _seed_metric(session, uid, date.today() - timedelta(days=3), "hrv", "fitbit", {"daily_rmssd": 30})
            await _seed_metric(session, uid, date.today(), "hrv", "fitbit", {"daily_rmssd": 35})
            await session.commit()

            result = await get_latest(session, uid, "hrv")
            assert result is not None
            assert result["daily_rmssd"] == 35

    async def test_returns_none_when_empty(self):
        async with test_session_maker() as session:
            result = await get_latest(session, uuid.uuid4(), "hrv")
            assert result is None


class TestComputeRecoveryScore:
    def test_all_data_present(self):
        result = compute_recovery_score(
            {"daily_rmssd": 40, "date": "2026-04-10"},
            {"efficiency": 85, "date": "2026-04-10"},
            {"resting_heart_rate": 60, "date": "2026-04-10"},
        )
        assert result["score"] is not None
        assert 0 <= result["score"] <= 100
        assert result["hrv_score"] is not None
        assert result["sleep_score"] == 85.0
        assert result["rhr_score"] is not None

    def test_missing_hrv(self):
        result = compute_recovery_score(
            None,
            {"efficiency": 85},
            {"resting_heart_rate": 60},
        )
        assert result["score"] is None

    def test_missing_sleep(self):
        result = compute_recovery_score(
            {"daily_rmssd": 40},
            None,
            {"resting_heart_rate": 60},
        )
        assert result["score"] is None

    def test_missing_hr(self):
        result = compute_recovery_score(
            {"daily_rmssd": 40},
            {"efficiency": 85},
            None,
        )
        assert result["score"] is None

    def test_missing_fields_in_data(self):
        result = compute_recovery_score(
            {"daily_rmssd": None},
            {"efficiency": 85},
            {"resting_heart_rate": 60},
        )
        assert result["score"] is None

    def test_high_hrv_caps_at_100(self):
        result = compute_recovery_score(
            {"daily_rmssd": 150},
            {"efficiency": 95},
            {"resting_heart_rate": 50},
        )
        assert result["hrv_score"] == 100.0

    def test_high_rhr_floors_at_0(self):
        result = compute_recovery_score(
            {"daily_rmssd": 40},
            {"efficiency": 85},
            {"resting_heart_rate": 110},
        )
        assert result["rhr_score"] == 0.0
