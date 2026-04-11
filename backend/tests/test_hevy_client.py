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
# _fetch_workouts_for_date
# ---------------------------------------------------------------------------
class TestFetchWorkoutsForDate:
    def _make_workout(self, dt):
        w = MagicMock()
        w.start_time = dt
        return w

    def test_matches_target_date(self):
        w1 = self._make_workout(datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc))
        w2 = self._make_workout(datetime(2026, 4, 6, 10, 0, tzinfo=timezone.utc))  # older → stops

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.workouts = [w1, w2]

        with patch("src.services.hevy.client.get_client") as mock_get:
            mock_get.return_value.get_workouts.return_value = mock_response
            from src.services.hevy.client import _fetch_workouts_for_date
            result = _fetch_workouts_for_date("key", date(2026, 4, 7))

        assert len(result) == 1
        assert result[0] is w1

    def test_empty_response(self):
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.workouts = []

        with patch("src.services.hevy.client.get_client") as mock_get:
            mock_get.return_value.get_workouts.return_value = mock_response
            from src.services.hevy.client import _fetch_workouts_for_date
            result = _fetch_workouts_for_date("key", date(2026, 4, 7))

        assert result == []

    def test_failed_response(self):
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.workouts = None

        with patch("src.services.hevy.client.get_client") as mock_get:
            mock_get.return_value.get_workouts.return_value = mock_response
            from src.services.hevy.client import _fetch_workouts_for_date
            result = _fetch_workouts_for_date("key", date(2026, 4, 7))

        assert result == []


# ---------------------------------------------------------------------------
# _fetch_template_muscles
# ---------------------------------------------------------------------------
class TestFetchTemplateMuscles:
    def test_cache_hit(self):
        from src.services.hevy.client import _fetch_template_muscles
        cache = {"T1": ("chest", ["triceps"])}
        client = MagicMock()
        result = _fetch_template_muscles(client, "T1", cache)
        assert result == ("chest", ["triceps"])
        client.get_exercise_template.assert_not_called()

    def test_cache_miss_fetches(self):
        from src.services.hevy.client import _fetch_template_muscles
        client = MagicMock()
        resp = MagicMock()
        resp.exercise_template.primary_muscle_group = "quadriceps"
        resp.exercise_template.secondary_muscle_groups = ["glutes", "hamstrings"]
        client.get_exercise_template.return_value = resp

        cache: dict = {}
        result = _fetch_template_muscles(client, "T2", cache)
        assert result == ("quadriceps", ["glutes", "hamstrings"])
        assert "T2" in cache

    def test_exception_returns_unknown(self):
        from src.services.hevy.client import _fetch_template_muscles, UNKNOWN_MUSCLE_GROUP
        client = MagicMock()
        client.get_exercise_template.side_effect = Exception("API error")

        cache: dict = {}
        result = _fetch_template_muscles(client, "T3", cache)
        assert result == (UNKNOWN_MUSCLE_GROUP, [])
        assert "T3" in cache


# ---------------------------------------------------------------------------
# _process_workouts (integration: fetches workouts + enriches with templates)
# ---------------------------------------------------------------------------
class TestProcessWorkouts:
    def _make_workout(self, title="Push Day", exercises=None):
        w = MagicMock()
        w.title = title
        w.start_time = datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc)
        w.end_time = datetime(2026, 4, 7, 11, 0, tzinfo=timezone.utc)
        w.exercises = exercises or []
        return w

    def _make_exercise(self, title="Bench Press", template_id="T1", weight=80, reps=10):
        ex = MagicMock()
        ex.title = title
        ex.exercise_template_id = template_id
        s = MagicMock()
        s.type = "normal"
        s.weight_kg = weight
        s.reps = reps
        s.rpe = None
        s.distance_meters = None
        s.duration_seconds = None
        ex.sets = [s]
        return ex

    def test_no_workouts_returns_empty(self):
        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[]):
            from src.services.hevy.client import _process_workouts
            result = _process_workouts("key", date(2026, 4, 7))
        assert result["data"] == {}

    def test_single_workout_with_template_enrichment(self):
        ex = self._make_exercise("Bench Press", "T1", 80, 10)
        workout = self._make_workout(exercises=[ex])

        mock_client = MagicMock()
        resp = MagicMock()
        resp.exercise_template.primary_muscle_group = "chest"
        resp.exercise_template.secondary_muscle_groups = ["triceps", "shoulders"]
        mock_client.get_exercise_template.return_value = resp

        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[workout]):
            from src.services.hevy.client import _process_workouts
            result = _process_workouts("key", date(2026, 4, 7), mock_client, {})

        wd = result["data"]["workout"]
        assert wd["total_volume_kg"] == 800.0
        assert wd["muscle_groups"]["chest"] == 1
        assert wd["muscle_groups"]["triceps"] == 0.4
        assert wd["exercises"][0]["primary_muscle"] == "chest"

    def test_multiple_workouts_merged(self):
        w1 = self._make_workout("Morning", exercises=[self._make_exercise("Squat", "T2")])
        w2 = self._make_workout("Evening", exercises=[self._make_exercise("Bench", "T3")])
        w2.start_time = datetime(2026, 4, 7, 18, 0, tzinfo=timezone.utc)
        w2.end_time = datetime(2026, 4, 7, 19, 0, tzinfo=timezone.utc)

        mock_client = MagicMock()
        resp = MagicMock()
        resp.exercise_template.primary_muscle_group = "chest"
        resp.exercise_template.secondary_muscle_groups = []
        mock_client.get_exercise_template.return_value = resp

        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[w1, w2]):
            from src.services.hevy.client import _process_workouts
            result = _process_workouts("key", date(2026, 4, 7), mock_client, {})

        wd = result["data"]["workout"]
        assert wd["workout_count"] == 2
        assert wd["title"] == "2 workouts"
        assert wd["duration_minutes"] == 120
        assert len(wd["exercises"]) == 2

    def test_shared_cache_avoids_duplicate_fetches(self):
        ex1 = self._make_exercise("Bench 1", "T1")
        ex2 = self._make_exercise("Bench 2", "T1")  # same template
        workout = self._make_workout(exercises=[ex1, ex2])

        mock_client = MagicMock()
        resp = MagicMock()
        resp.exercise_template.primary_muscle_group = "chest"
        resp.exercise_template.secondary_muscle_groups = []
        mock_client.get_exercise_template.return_value = resp

        cache: dict = {}
        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[workout]):
            from src.services.hevy.client import _process_workouts
            _process_workouts("key", date(2026, 4, 7), mock_client, cache)

        assert mock_client.get_exercise_template.call_count == 1


# ---------------------------------------------------------------------------
# get_workouts_for_date (async wrapper)
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

    @pytest.mark.asyncio
    async def test_with_workout_returns_enriched_data(self):
        mock_workout = MagicMock()
        mock_workout.title = "Leg Day"
        mock_workout.start_time = datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc)
        mock_workout.end_time = datetime(2026, 4, 7, 11, 0, tzinfo=timezone.utc)

        ex = MagicMock()
        ex.title = "Squat"
        ex.exercise_template_id = "SQ1"
        s = MagicMock()
        s.type = "normal"
        s.weight_kg = 100
        s.reps = 5
        s.rpe = None
        s.distance_meters = None
        s.duration_seconds = None
        ex.sets = [s]
        mock_workout.exercises = [ex]

        mock_client = MagicMock()
        resp = MagicMock()
        resp.exercise_template.primary_muscle_group = "quadriceps"
        resp.exercise_template.secondary_muscle_groups = ["glutes"]
        mock_client.get_exercise_template.return_value = resp

        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[mock_workout]):
            result = await get_workouts_for_date("key", date(2026, 4, 7), mock_client, {})

        wd = result["data"]["workout"]
        assert wd["title"] == "Leg Day"
        assert wd["total_volume_kg"] == 500.0
        assert wd["muscle_groups"]["quadriceps"] == 1
        assert wd["exercises"][0]["primary_muscle"] == "quadriceps"
