"""Tests for Hevy API client — validation, workout fetching, and metric conversion."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.services.hevy.client import (
    HevyAPIError,
    UNKNOWN_MUSCLE_GROUP,
    _workout_to_metrics,
    get_workouts_for_date,
    validate_hevy_api_key,
)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------
class TestExceptionHierarchy:
    def test_hevy_api_error_is_exception(self):
        assert issubclass(HevyAPIError, Exception)


# ---------------------------------------------------------------------------
# _workout_to_metrics (with mocked template fetching)
# ---------------------------------------------------------------------------
class TestWorkoutToMetrics:
    def _make_workout(self, **overrides):
        mock = MagicMock()
        mock.title = overrides.get("title", "Push Day")
        mock.start_time = overrides.get("start_time", datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc))
        mock.end_time = overrides.get("end_time", datetime(2026, 4, 7, 11, 15, tzinfo=timezone.utc))
        mock.exercises = overrides.get("exercises", [])
        return mock

    def _make_exercise(self, title="Bench Press", template_id="abc123", sets=None):
        ex = MagicMock()
        ex.title = title
        ex.exercise_template_id = template_id
        if sets is None:
            s = MagicMock()
            s.type = "normal"
            s.weight_kg = 80.0
            s.reps = 10
            s.rpe = 8.0
            s.distance_meters = None
            s.duration_seconds = None
            sets = [s]
        ex.sets = sets
        return ex

    def _make_mock_client(self, primary="chest", secondary=None):
        client = MagicMock()
        resp = MagicMock()
        resp.exercise_template.primary_muscle_group = primary
        resp.exercise_template.secondary_muscle_groups = secondary or []
        client.get_exercise_template.return_value = resp
        return client

    def test_empty_workout(self):
        client = self._make_mock_client()
        result = _workout_to_metrics(self._make_workout(), {}, client)
        wd = result["workout"]
        assert wd["title"] == "Push Day"
        assert wd["duration_minutes"] == 75
        assert wd["total_volume_kg"] == 0
        assert wd["total_sets"] == 0
        assert wd["exercises"] == []

    def test_workout_with_exercises(self):
        client = self._make_mock_client(primary="chest", secondary=["triceps", "shoulders"])
        ex = self._make_exercise("Barbell Bench Press")
        result = _workout_to_metrics(self._make_workout(exercises=[ex]), {}, client)
        wd = result["workout"]
        assert wd["total_sets"] == 1
        assert wd["total_reps"] == 10
        assert wd["total_volume_kg"] == 800.0
        assert len(wd["exercises"]) == 1
        assert wd["exercises"][0]["primary_muscle"] == "chest"
        assert "triceps" in wd["exercises"][0]["secondary_muscles"]
        assert wd["muscle_groups"]["chest"] == 1

    def test_duration_calculation(self):
        client = self._make_mock_client()
        workout = self._make_workout(
            start_time=datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 4, 7, 10, 30, tzinfo=timezone.utc),
        )
        result = _workout_to_metrics(workout, {}, client)
        assert result["workout"]["duration_minutes"] == 90

    def test_zero_weight_sets(self):
        client = self._make_mock_client(primary="chest")
        s = MagicMock()
        s.type = "normal"
        s.weight_kg = 0
        s.reps = 15
        s.rpe = None
        s.distance_meters = None
        s.duration_seconds = None
        ex = self._make_exercise("Push-up", sets=[s])
        result = _workout_to_metrics(self._make_workout(exercises=[ex]), {}, client)
        assert result["workout"]["total_volume_kg"] == 0
        assert result["workout"]["total_reps"] == 15

    def test_none_weight_treated_as_zero(self):
        client = self._make_mock_client(primary="core")
        s = MagicMock()
        s.type = "normal"
        s.weight_kg = None
        s.reps = None
        s.rpe = None
        s.distance_meters = None
        s.duration_seconds = None
        ex = self._make_exercise("Plank", sets=[s])
        result = _workout_to_metrics(self._make_workout(exercises=[ex]), {}, client)
        assert result["workout"]["total_volume_kg"] == 0

    def test_template_cache_reused(self):
        client = self._make_mock_client(primary="chest")
        cache: dict = {}
        ex1 = self._make_exercise("Bench Press", template_id="T1")
        ex2 = self._make_exercise("Bench Press", template_id="T1")
        _workout_to_metrics(self._make_workout(exercises=[ex1, ex2]), cache, client)
        # Template should only be fetched once despite two exercises with same ID
        assert client.get_exercise_template.call_count == 1
        assert "T1" in cache


# ---------------------------------------------------------------------------
# validate_hevy_api_key
# ---------------------------------------------------------------------------
class TestValidateHevyApiKey:
    @pytest.mark.asyncio
    async def test_valid_key(self):
        with patch("src.services.hevy.client.get_client") as mock_get:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.is_success = True
            mock_client.get_workout_count.return_value = mock_response
            mock_get.return_value = mock_client

            assert await validate_hevy_api_key("valid-key") is True

    @pytest.mark.asyncio
    async def test_invalid_key(self):
        with patch("src.services.hevy.client.get_client") as mock_get:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.is_success = False
            mock_client.get_workout_count.return_value = mock_response
            mock_get.return_value = mock_client

            assert await validate_hevy_api_key("bad-key") is False

    @pytest.mark.asyncio
    async def test_exception_returns_false(self):
        with patch("src.services.hevy.client.get_client", side_effect=Exception("network")):
            assert await validate_hevy_api_key("any-key") is False


# ---------------------------------------------------------------------------
# get_workouts_for_date
# ---------------------------------------------------------------------------
class TestGetWorkoutsForDate:
    @pytest.mark.asyncio
    async def test_no_workouts_returns_empty(self):
        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[]):
            result = await get_workouts_for_date("key", date(2026, 4, 7))
            assert result["data"] == {}
            assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_exception_caught_in_errors(self):
        with patch("src.services.hevy.client._fetch_workouts_for_date", side_effect=Exception("API down")):
            result = await get_workouts_for_date("key", date(2026, 4, 7))
            assert result["data"] == {}
            assert any("hevy" in e for e in result["errors"])
