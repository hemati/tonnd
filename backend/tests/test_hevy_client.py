"""Tests for Hevy API client — validation, workout fetching, and metric conversion."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.services.hevy.client import (
    HevyAPIError,
    UNKNOWN_MUSCLE_GROUP,
    _fetch_template_info,
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
        mock.id = overrides.get("id", "workout-001")
        mock.title = overrides.get("title", "Push Day")
        mock.description = overrides.get("description", None)
        mock.start_time = overrides.get("start_time", datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc))
        mock.end_time = overrides.get("end_time", datetime(2026, 4, 7, 11, 15, tzinfo=timezone.utc))
        mock.exercises = overrides.get("exercises", [])
        return mock

    def _make_exercise(self, title="Bench Press", template_id="abc123", sets=None,
                       index=0, notes=None, supersets_id=None):
        ex = MagicMock()
        ex.title = title
        ex.exercise_template_id = template_id
        ex.index = index
        ex.notes = notes
        ex.supersets_id = supersets_id
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
        resp.exercise_template.type = "weight_reps"
        resp.exercise_template.is_custom = False
        client.get_exercise_template.return_value = resp
        return client

    def test_empty_workout(self):
        client = self._make_mock_client()
        result = _workout_to_metrics(self._make_workout(), {}, client)
        wd = result["workout"]
        assert wd["external_id"] == "workout-001"
        assert wd["title"] == "Push Day"
        assert wd["description"] is None
        assert wd["duration_minutes"] == 75
        assert wd["total_volume_kg"] == 0
        assert wd["total_sets"] == 0
        assert wd["exercises"] == []
        assert wd["started_at"] is not None
        assert wd["ended_at"] is not None

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
        assert wd["exercises"][0]["exercise_type"] == "weight_reps"
        assert wd["exercises"][0]["is_custom"] is False
        assert wd["exercises"][0]["exercise_index"] == 0
        assert wd["exercises"][0]["external_exercise_id"] == "abc123"
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
# _fetch_template_info
# ---------------------------------------------------------------------------
class TestFetchTemplateInfo:
    def test_cache_hit(self):
        cache = {"T1": {"primary_muscle": "chest", "secondary_muscles": ["triceps"],
                        "exercise_type": "weight_reps", "is_custom": False}}
        client = MagicMock()
        result = _fetch_template_info(client, "T1", cache)
        assert result["primary_muscle"] == "chest"
        assert result["secondary_muscles"] == ["triceps"]
        assert result["exercise_type"] == "weight_reps"
        assert result["is_custom"] is False
        client.get_exercise_template.assert_not_called()

    def test_cache_miss_fetches(self):
        client = MagicMock()
        resp = MagicMock()
        resp.exercise_template.primary_muscle_group = "quadriceps"
        resp.exercise_template.secondary_muscle_groups = ["glutes", "hamstrings"]
        resp.exercise_template.type = "weight_reps"
        resp.exercise_template.is_custom = True
        client.get_exercise_template.return_value = resp

        cache: dict = {}
        result = _fetch_template_info(client, "T2", cache)
        assert result["primary_muscle"] == "quadriceps"
        assert result["secondary_muscles"] == ["glutes", "hamstrings"]
        assert result["exercise_type"] == "weight_reps"
        assert result["is_custom"] is True
        assert "T2" in cache

    def test_exception_returns_unknown(self):
        client = MagicMock()
        client.get_exercise_template.side_effect = Exception("API error")

        cache: dict = {}
        result = _fetch_template_info(client, "T3", cache)
        assert result["primary_muscle"] == UNKNOWN_MUSCLE_GROUP
        assert result["secondary_muscles"] == []
        assert result["exercise_type"] is None
        assert result["is_custom"] is None
        assert "T3" in cache


# ---------------------------------------------------------------------------
# _process_workouts (integration: fetches workouts + enriches with templates)
# ---------------------------------------------------------------------------
class TestProcessWorkouts:
    def _make_workout(self, title="Push Day", exercises=None):
        w = MagicMock()
        w.id = "pw-001"
        w.title = title
        w.description = None
        w.start_time = datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc)
        w.end_time = datetime(2026, 4, 7, 11, 0, tzinfo=timezone.utc)
        w.exercises = exercises or []
        return w

    def _make_exercise(self, title="Bench Press", template_id="T1", weight=80, reps=10):
        ex = MagicMock()
        ex.title = title
        ex.exercise_template_id = template_id
        ex.index = 0
        ex.notes = None
        ex.supersets_id = None
        s = MagicMock()
        s.type = "normal"
        s.weight_kg = weight
        s.reps = reps
        s.rpe = None
        s.distance_meters = None
        s.duration_seconds = None
        ex.sets = [s]
        return ex

    def _make_mock_client(self, primary="chest", secondary=None):
        client = MagicMock()
        resp = MagicMock()
        resp.exercise_template.primary_muscle_group = primary
        resp.exercise_template.secondary_muscle_groups = secondary or []
        resp.exercise_template.type = "weight_reps"
        resp.exercise_template.is_custom = False
        client.get_exercise_template.return_value = resp
        return client

    def test_no_workouts_returns_empty(self):
        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[]):
            from src.services.hevy.client import _process_workouts
            result = _process_workouts("key", date(2026, 4, 7))
        assert result["data"] == []

    def test_single_workout_with_template_enrichment(self):
        ex = self._make_exercise("Bench Press", "T1", 80, 10)
        workout = self._make_workout(exercises=[ex])
        mock_client = self._make_mock_client(primary="chest", secondary=["triceps", "shoulders"])

        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[workout]):
            from src.services.hevy.client import _process_workouts
            result = _process_workouts("key", date(2026, 4, 7), mock_client, {})

        assert len(result["data"]) == 1
        wd = result["data"][0]
        assert wd["total_volume_kg"] == 800.0
        assert wd["muscle_groups"]["chest"] == 1
        assert wd["muscle_groups"]["triceps"] == 0.4
        assert wd["exercises"][0]["primary_muscle"] == "chest"

    def test_multiple_workouts_as_list(self):
        w1 = self._make_workout("Morning", exercises=[self._make_exercise("Squat", "T2")])
        w2 = self._make_workout("Evening", exercises=[self._make_exercise("Bench", "T3")])
        w2.id = "pw-002"
        w2.start_time = datetime(2026, 4, 7, 18, 0, tzinfo=timezone.utc)
        w2.end_time = datetime(2026, 4, 7, 19, 0, tzinfo=timezone.utc)

        mock_client = self._make_mock_client(primary="chest")

        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[w1, w2]):
            from src.services.hevy.client import _process_workouts
            result = _process_workouts("key", date(2026, 4, 7), mock_client, {})

        assert len(result["data"]) == 2
        assert result["data"][0]["title"] == "Morning"
        assert result["data"][0]["duration_minutes"] == 60
        assert result["data"][1]["title"] == "Evening"
        assert result["data"][1]["duration_minutes"] == 60

    def test_shared_cache_avoids_duplicate_fetches(self):
        ex1 = self._make_exercise("Bench 1", "T1")
        ex2 = self._make_exercise("Bench 2", "T1")  # same template
        workout = self._make_workout(exercises=[ex1, ex2])

        mock_client = self._make_mock_client(primary="chest")

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
            assert result["data"] == []
            assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_exception_caught_in_errors(self):
        with patch("src.services.hevy.client._fetch_workouts_for_date", side_effect=Exception("API down")):
            result = await get_workouts_for_date("key", date(2026, 4, 7))
            assert result["data"] == []
            assert any("hevy" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_with_workout_returns_enriched_data(self):
        mock_workout = MagicMock()
        mock_workout.id = "wk-leg-1"
        mock_workout.title = "Leg Day"
        mock_workout.description = None
        mock_workout.start_time = datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc)
        mock_workout.end_time = datetime(2026, 4, 7, 11, 0, tzinfo=timezone.utc)

        ex = MagicMock()
        ex.title = "Squat"
        ex.exercise_template_id = "SQ1"
        ex.index = 0
        ex.notes = None
        ex.supersets_id = None
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
        resp.exercise_template.type = "weight_reps"
        resp.exercise_template.is_custom = False
        mock_client.get_exercise_template.return_value = resp

        with patch("src.services.hevy.client._fetch_workouts_for_date", return_value=[mock_workout]):
            result = await get_workouts_for_date("key", date(2026, 4, 7), mock_client, {})

        assert len(result["data"]) == 1
        wd = result["data"][0]
        assert wd["title"] == "Leg Day"
        assert wd["total_volume_kg"] == 500.0
        assert wd["muscle_groups"]["quadriceps"] == 1
        assert wd["exercises"][0]["primary_muscle"] == "quadriceps"


# ---------------------------------------------------------------------------
# Volume calculation — warmup exclusion
# ---------------------------------------------------------------------------
class TestVolumeCalculation:
    """Verify that warmup sets are excluded from volume, while working sets are included."""

    def _make_mock_client(self, primary="chest"):
        client = MagicMock()
        resp = MagicMock()
        resp.exercise_template.primary_muscle_group = primary
        resp.exercise_template.secondary_muscle_groups = []
        resp.exercise_template.type = "weight_reps"
        resp.exercise_template.is_custom = False
        client.get_exercise_template.return_value = resp
        return client

    def _make_set(self, set_type="normal", weight=100.0, reps=10):
        s = MagicMock()
        s.type = set_type
        s.weight_kg = weight
        s.reps = reps
        s.rpe = None
        s.distance_meters = None
        s.duration_seconds = None
        return s

    def _make_exercise(self, title="Bench Press", template_id="T1", sets=None):
        ex = MagicMock()
        ex.title = title
        ex.exercise_template_id = template_id
        ex.index = 0
        ex.notes = None
        ex.supersets_id = None
        ex.sets = sets or []
        return ex

    def _make_workout(self, exercises=None):
        w = MagicMock()
        w.id = "vol-test-001"
        w.title = "Volume Test"
        w.description = None
        w.start_time = datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc)
        w.end_time = datetime(2026, 4, 7, 11, 0, tzinfo=timezone.utc)
        w.exercises = exercises or []
        return w

    def test_warmup_excluded_from_volume(self):
        """Warmup sets should NOT count toward volume."""
        warmup = self._make_set("warmup", 60.0, 10)  # 600 kg should be excluded
        working = self._make_set("normal", 100.0, 10)  # 1000 kg should count
        ex = self._make_exercise(sets=[warmup, working])
        workout = self._make_workout(exercises=[ex])
        client = self._make_mock_client()

        result = _workout_to_metrics(workout, {}, client)
        wd = result["workout"]
        assert wd["total_volume_kg"] == 1000.0
        assert wd["exercises"][0]["volume_kg"] == 1000.0
        # Both sets still counted in total_sets/reps
        assert wd["total_sets"] == 2
        assert wd["total_reps"] == 20

    def test_dropset_included_in_volume(self):
        """Dropset sets should count toward volume."""
        dropset = self._make_set("dropset", 80.0, 12)  # 960
        ex = self._make_exercise(sets=[dropset])
        workout = self._make_workout(exercises=[ex])
        client = self._make_mock_client()

        result = _workout_to_metrics(workout, {}, client)
        assert result["workout"]["total_volume_kg"] == 960.0

    def test_failure_set_included_in_volume(self):
        """Failure sets should count toward volume."""
        failure = self._make_set("failure", 90.0, 6)  # 540
        ex = self._make_exercise(sets=[failure])
        workout = self._make_workout(exercises=[ex])
        client = self._make_mock_client()

        result = _workout_to_metrics(workout, {}, client)
        assert result["workout"]["total_volume_kg"] == 540.0

    def test_mixed_set_types_volume(self):
        """Only working set types count toward volume; warmup does not."""
        warmup = self._make_set("warmup", 40.0, 10)     # 400 excluded
        normal = self._make_set("normal", 100.0, 8)      # 800 included
        dropset = self._make_set("dropset", 80.0, 10)    # 800 included
        failure = self._make_set("failure", 60.0, 6)      # 360 included
        ex = self._make_exercise(sets=[warmup, normal, dropset, failure])
        workout = self._make_workout(exercises=[ex])
        client = self._make_mock_client()

        result = _workout_to_metrics(workout, {}, client)
        wd = result["workout"]
        assert wd["total_volume_kg"] == 1960.0
        assert wd["total_sets"] == 4
        assert wd["total_reps"] == 34


# ---------------------------------------------------------------------------
# New fields parsing — description, notes, supersets_id, exercise_index, etc.
# ---------------------------------------------------------------------------
class TestNewFieldsParsing:
    """Verify new fields (description, notes, supersets_id, exercise_index, exercise_type, is_custom) are parsed."""

    def _make_mock_client(self, exercise_type="weight_reps", is_custom=True):
        client = MagicMock()
        resp = MagicMock()
        resp.exercise_template.primary_muscle_group = "chest"
        resp.exercise_template.secondary_muscle_groups = []
        resp.exercise_template.type = exercise_type
        resp.exercise_template.is_custom = is_custom
        client.get_exercise_template.return_value = resp
        return client

    def _make_set(self, set_type="normal", weight=80.0, reps=10):
        s = MagicMock()
        s.type = set_type
        s.weight_kg = weight
        s.reps = reps
        s.rpe = None
        s.distance_meters = None
        s.duration_seconds = None
        return s

    def test_workout_description_parsed(self):
        w = MagicMock()
        w.id = "desc-001"
        w.title = "Heavy Push"
        w.description = "Focus on progressive overload"
        w.start_time = datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc)
        w.end_time = datetime(2026, 4, 7, 11, 0, tzinfo=timezone.utc)
        w.exercises = []

        client = self._make_mock_client()
        result = _workout_to_metrics(w, {}, client)
        assert result["workout"]["description"] == "Focus on progressive overload"
        assert result["workout"]["external_id"] == "desc-001"

    def test_exercise_notes_and_supersets_id(self):
        w = MagicMock()
        w.id = "notes-001"
        w.title = "Superset Day"
        w.description = None
        w.start_time = datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc)
        w.end_time = datetime(2026, 4, 7, 11, 0, tzinfo=timezone.utc)

        ex = MagicMock()
        ex.title = "Bench Press"
        ex.exercise_template_id = "T1"
        ex.index = 2
        ex.notes = "Felt strong today"
        ex.supersets_id = "SS-42"
        ex.sets = [self._make_set()]
        w.exercises = [ex]

        client = self._make_mock_client()
        result = _workout_to_metrics(w, {}, client)
        exd = result["workout"]["exercises"][0]
        assert exd["exercise_index"] == 2
        assert exd["notes"] == "Felt strong today"
        assert exd["supersets_id"] == "SS-42"

    def test_exercise_type_and_is_custom(self):
        w = MagicMock()
        w.id = "custom-001"
        w.title = "Custom Day"
        w.description = None
        w.start_time = datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc)
        w.end_time = datetime(2026, 4, 7, 11, 0, tzinfo=timezone.utc)

        ex = MagicMock()
        ex.title = "My Custom Lift"
        ex.exercise_template_id = "CUSTOM-T1"
        ex.index = 0
        ex.notes = None
        ex.supersets_id = None
        ex.sets = [self._make_set()]
        w.exercises = [ex]

        client = self._make_mock_client(exercise_type="duration", is_custom=True)
        result = _workout_to_metrics(w, {}, client)
        exd = result["workout"]["exercises"][0]
        assert exd["exercise_type"] == "duration"
        assert exd["is_custom"] is True
        assert exd["external_exercise_id"] == "CUSTOM-T1"

    def test_started_at_and_ended_at_format(self):
        w = MagicMock()
        w.id = "time-001"
        w.title = "Time Test"
        w.description = None
        w.start_time = datetime(2026, 4, 7, 10, 30, tzinfo=timezone.utc)
        w.end_time = datetime(2026, 4, 7, 11, 45, tzinfo=timezone.utc)
        w.exercises = []

        client = self._make_mock_client()
        result = _workout_to_metrics(w, {}, client)
        wd = result["workout"]
        assert "2026-04-07" in wd["started_at"]
        assert "2026-04-07" in wd["ended_at"]
        assert wd["duration_minutes"] == 75
