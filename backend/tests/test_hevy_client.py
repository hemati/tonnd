"""Tests for Hevy API client — validation, workout fetching, and metric conversion."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.services.hevy.client import (
    HevyAPIError,
    _guess_muscle_group,
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
# _guess_muscle_group
# ---------------------------------------------------------------------------
class TestGuessMuscleGroup:
    @pytest.mark.parametrize("title,expected", [
        ("Barbell Bench Press", "chest"),
        ("Incline Dumbbell Fly", "chest"),
        ("Barbell Row", "back"),
        ("Pull-up", "back"),
        ("Lat Pulldown", "back"),
        ("Overhead Press", "shoulders"),
        ("Lateral Raise", "shoulders"),
        ("Barbell Curl", "biceps"),
        ("Tricep Pushdown", "triceps"),
        ("Barbell Squat", "legs"),
        ("Leg Press", "legs"),
        ("Romanian Deadlift", "back"),
        ("Plank", "core"),
        ("Ab Crunch", "core"),
        ("Treadmill Run", "cardio"),
        ("Cable Crossover", "other"),
    ])
    def test_mapping(self, title, expected):
        assert _guess_muscle_group(title.lower()) == expected


# ---------------------------------------------------------------------------
# _workout_to_metrics
# ---------------------------------------------------------------------------
class TestWorkoutToMetrics:
    def _make_workout(self, **overrides):
        mock = MagicMock()
        mock.title = overrides.get("title", "Push Day")
        mock.start_time = overrides.get("start_time", datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc))
        mock.end_time = overrides.get("end_time", datetime(2026, 4, 7, 11, 15, tzinfo=timezone.utc))
        mock.exercises = overrides.get("exercises", [])
        return mock

    def _make_exercise(self, title="Bench Press", sets=None):
        ex = MagicMock()
        ex.title = title
        ex.exercise_template_id = "abc123"
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

    def test_empty_workout(self):
        workout = self._make_workout()
        result = _workout_to_metrics(workout)
        wd = result["workout"]
        assert wd["title"] == "Push Day"
        assert wd["duration_minutes"] == 75
        assert wd["total_volume_kg"] == 0
        assert wd["total_sets"] == 0
        assert wd["exercises"] == []

    def test_workout_with_exercises(self):
        ex = self._make_exercise("Barbell Bench Press")
        workout = self._make_workout(exercises=[ex])
        result = _workout_to_metrics(workout)
        wd = result["workout"]
        assert wd["total_sets"] == 1
        assert wd["total_reps"] == 10
        assert wd["total_volume_kg"] == 800.0
        assert len(wd["exercises"]) == 1
        assert wd["exercises"][0]["title"] == "Barbell Bench Press"
        assert wd["muscle_groups"]["chest"] == 1

    def test_duration_calculation(self):
        workout = self._make_workout(
            start_time=datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 4, 7, 10, 30, tzinfo=timezone.utc),
        )
        result = _workout_to_metrics(workout)
        assert result["workout"]["duration_minutes"] == 90

    def test_zero_weight_sets(self):
        s = MagicMock()
        s.type = "normal"
        s.weight_kg = 0
        s.reps = 15
        s.rpe = None
        s.distance_meters = None
        s.duration_seconds = None
        ex = self._make_exercise("Push-up", sets=[s])
        workout = self._make_workout(exercises=[ex])
        result = _workout_to_metrics(workout)
        assert result["workout"]["total_volume_kg"] == 0
        assert result["workout"]["total_reps"] == 15

    def test_none_weight_treated_as_zero(self):
        s = MagicMock()
        s.type = "normal"
        s.weight_kg = None
        s.reps = None
        s.rpe = None
        s.distance_meters = None
        s.duration_seconds = None
        ex = self._make_exercise("Plank", sets=[s])
        workout = self._make_workout(exercises=[ex])
        result = _workout_to_metrics(workout)
        assert result["workout"]["total_volume_kg"] == 0


# ---------------------------------------------------------------------------
# validate_hevy_api_key
# ---------------------------------------------------------------------------
class TestValidateHevyApiKey:
    @pytest.mark.asyncio
    async def test_valid_key(self):
        with patch("src.services.hevy.client._get_client") as mock_get:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.is_success = True
            mock_client.get_workout_count.return_value = mock_response
            mock_get.return_value = mock_client

            assert await validate_hevy_api_key("valid-key") is True

    @pytest.mark.asyncio
    async def test_invalid_key(self):
        with patch("src.services.hevy.client._get_client") as mock_get:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.is_success = False
            mock_client.get_workout_count.return_value = mock_response
            mock_get.return_value = mock_client

            assert await validate_hevy_api_key("bad-key") is False

    @pytest.mark.asyncio
    async def test_exception_returns_false(self):
        with patch("src.services.hevy.client._get_client", side_effect=Exception("network")):
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
    async def test_with_workout_returns_data(self):
        mock_workout = MagicMock()
        mock_workout.title = "Leg Day"
        mock_workout.start_time = datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc)
        mock_workout.end_time = datetime(2026, 4, 7, 11, 0, tzinfo=timezone.utc)

        ex = MagicMock()
        ex.title = "Barbell Squat"
        ex.exercise_template_id = "sq1"
        s = MagicMock()
        s.type = "normal"
        s.weight_kg = 100
        s.reps = 5
        s.rpe = 9
        s.distance_meters = None
        s.duration_seconds = None
        ex.sets = [s]
        mock_workout.exercises = [ex]

        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[mock_workout]):
            result = await get_workouts_for_date("key", date(2026, 4, 7))

        assert "workout" in result["data"]
        wd = result["data"]["workout"]
        assert wd["title"] == "Leg Day"
        assert wd["total_volume_kg"] == 500.0
        assert wd["total_sets"] == 1
        assert wd["muscle_groups"]["legs"] == 1

    @pytest.mark.asyncio
    async def test_exception_caught_in_errors(self):
        with patch("src.services.hevy.client._fetch_workouts_for_date", side_effect=Exception("API down")):
            result = await get_workouts_for_date("key", date(2026, 4, 7))
            assert result["data"] == {}
            assert any("hevy" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_multiple_workouts_merged(self):
        w1 = MagicMock()
        w1.title = "Morning"
        w1.start_time = datetime(2026, 4, 7, 8, 0, tzinfo=timezone.utc)
        w1.end_time = datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc)
        w1.exercises = []

        w2 = MagicMock()
        w2.title = "Evening"
        w2.start_time = datetime(2026, 4, 7, 18, 0, tzinfo=timezone.utc)
        w2.end_time = datetime(2026, 4, 7, 19, 0, tzinfo=timezone.utc)
        w2.exercises = []

        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[w1, w2]):
            result = await get_workouts_for_date("key", date(2026, 4, 7))

        assert result["data"]["workout"]["workout_count"] == 2
        assert result["data"]["workout"]["title"] == "2 workouts"
        assert result["data"]["workout"]["duration_minutes"] == 120
