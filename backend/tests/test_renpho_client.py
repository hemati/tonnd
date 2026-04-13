"""Tests for Renpho API client — login and measurement retrieval."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.services.renpho.client import (
    RenphoAPIError,
    SessionExpiredError,
    get_measurements_for_date,
    renpho_login,
)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------
class TestExceptionHierarchy:
    def test_session_expired_is_renpho_api_error(self):
        assert issubclass(SessionExpiredError, RenphoAPIError)

    def test_renpho_api_error_is_exception(self):
        assert issubclass(RenphoAPIError, Exception)

    def test_can_raise_and_catch_session_expired(self):
        with pytest.raises(RenphoAPIError):
            raise SessionExpiredError("expired")


# ---------------------------------------------------------------------------
# renpho_login
# ---------------------------------------------------------------------------
class TestRenphoLogin:
    @patch("src.services.renpho.client.RenphoClient")
    def test_success(self, MockRenphoClient):
        mock_instance = MagicMock()
        mock_instance.login.return_value = None
        mock_instance.token = "session-key-abc"
        mock_instance.user_id = 12345
        MockRenphoClient.return_value = mock_instance

        result = renpho_login("user@example.com", "password123")

        MockRenphoClient.assert_called_once_with("user@example.com", "password123")
        mock_instance.login.assert_called_once()
        assert result["session_key"] == "session-key-abc"
        assert result["user_id"] == "12345"

    @patch("src.services.renpho.client.RenphoClient")
    def test_login_failure_raises_renpho_api_error(self, MockRenphoClient):
        mock_instance = MagicMock()
        mock_instance.login.side_effect = Exception("Invalid credentials")
        MockRenphoClient.return_value = mock_instance

        with pytest.raises(RenphoAPIError, match="Renpho login failed"):
            renpho_login("bad@example.com", "wrong")

    @patch("src.services.renpho.client.RenphoClient")
    def test_constructor_failure_raises_renpho_api_error(self, MockRenphoClient):
        MockRenphoClient.side_effect = Exception("connection refused")

        with pytest.raises(RenphoAPIError, match="Renpho login failed"):
            renpho_login("user@example.com", "pw")


# ---------------------------------------------------------------------------
# get_measurements_for_date
# ---------------------------------------------------------------------------
class TestGetMeasurementsForDate:
    @patch("src.services.renpho.client.RenphoClient")
    def test_matching_date_returns_data(self, MockRenphoClient):
        """When measurements contain a matching date, a flat dict with all fields is returned."""
        target = date(2026, 4, 7)
        ts = int(datetime(2026, 4, 7, 10, 0, 0, tzinfo=timezone.utc).timestamp())

        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = [
            {
                "timeStamp": ts,
                "weight": 75.5,
                "bmi": 23.1,
                "bodyfat": 17.5,
                "water": 55.0,
                "muscle": 42.0,
                "bone": 3.1,
                "bmr": 1650,
                "visfat": 8,
                "subfat": 12.0,
                "protein": 18.0,
                "bodyage": 28,
                "sinew": 55.0,
                "fatFreeWeight": 62.0,
                "heartRate": 68,
                "cardiacIndex": 2.5,
                "bodyShape": 3,
                "sport_flag": 1,
            }
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", target)

        assert result["errors"] == []
        assert len(result["data"]) == 1
        m = result["data"][0]
        assert m["weight_kg"] == 75.5
        assert m["bmi"] == 23.1
        assert m["body_fat_percent"] == 17.5
        assert m["body_water_percent"] == 55.0
        assert m["muscle_mass_percent"] == 42.0
        assert m["bone_mass_kg"] == 3.1
        assert m["bmr_kcal"] == 1650
        assert isinstance(m["bmr_kcal"], int)
        assert m["visceral_fat"] == 8
        assert m["subcutaneous_fat_percent"] == 12.0
        assert m["protein_percent"] == 18.0
        assert m["body_age"] == 28
        assert isinstance(m["body_age"], int)
        assert m["lean_body_mass_kg"] == 55.0
        assert m["fat_free_weight_kg"] == 62.0
        assert m["heart_rate"] == 68
        assert isinstance(m["heart_rate"], int)
        assert m["cardiac_index"] == 2.5
        assert m["body_shape"] == 3
        assert isinstance(m["body_shape"], int)
        assert m["sport_flag"] is True
        assert m["date"] == target
        assert m["measured_at"] == datetime(2026, 4, 7, 10, 0, 0, tzinfo=timezone.utc)

    @patch("src.services.renpho.client.RenphoClient")
    def test_non_matching_date_returns_empty(self, MockRenphoClient):
        """Measurements from a different date are not included."""
        target = date(2026, 4, 7)
        wrong_ts = int(datetime(2026, 4, 6, 10, 0, 0, tzinfo=timezone.utc).timestamp())

        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = [
            {"timeStamp": wrong_ts, "weight": 75.0}
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", target)

        assert result["data"] == []
        assert result["errors"] == []

    @patch("src.services.renpho.client.RenphoClient")
    def test_empty_measurements(self, MockRenphoClient):
        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = []
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", date(2026, 4, 7))

        assert result["data"] == []
        assert result["errors"] == []

    @patch("src.services.renpho.client.RenphoClient")
    def test_api_error_collected_in_errors(self, MockRenphoClient):
        """When RenphoClient raises, error is added to result['errors']."""
        MockRenphoClient.side_effect = Exception("network failure")

        result = get_measurements_for_date("u@test.com", "pw", date(2026, 4, 7))

        assert len(result["errors"]) == 1
        assert "renpho" in result["errors"][0]
        assert result["data"] == []

    @patch("src.services.renpho.client.RenphoClient")
    def test_measurement_without_timestamp_skipped(self, MockRenphoClient):
        """Measurements missing both timeStamp and time_stamp are skipped."""
        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = [
            {"weight": 80.0}  # no timestamp at all
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", date(2026, 4, 7))
        assert result["data"] == []

    @patch("src.services.renpho.client.RenphoClient")
    def test_time_stamp_alternative_key(self, MockRenphoClient):
        """The code also checks 'time_stamp' as an alternative key."""
        target = date(2026, 4, 7)
        ts = int(datetime(2026, 4, 7, 12, 0, 0, tzinfo=timezone.utc).timestamp())

        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = [
            {"time_stamp": ts, "weight": 82.0, "bmi": 25.0, "bodyfat": 20.0}
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", target)
        assert len(result["data"]) == 1
        assert result["data"][0]["weight_kg"] == 82.0

    @patch("src.services.renpho.client.RenphoClient")
    def test_zero_weight_skipped(self, MockRenphoClient):
        """Weight of 0 should cause the measurement to be skipped entirely."""
        target = date(2026, 4, 7)
        ts = int(datetime(2026, 4, 7, 10, 0, 0, tzinfo=timezone.utc).timestamp())

        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = [
            {"timeStamp": ts, "weight": 0, "bodyfat": 20.0}
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", target)
        assert result["data"] == []

    @patch("src.services.renpho.client.RenphoClient")
    def test_two_measurements_same_day(self, MockRenphoClient):
        """Two measurements on the same day produce two items in the list."""
        target = date(2026, 4, 7)
        ts_morning = int(datetime(2026, 4, 7, 7, 0, 0, tzinfo=timezone.utc).timestamp())
        ts_evening = int(datetime(2026, 4, 7, 20, 0, 0, tzinfo=timezone.utc).timestamp())

        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = [
            {
                "timeStamp": ts_morning,
                "weight": 80.0,
                "bmi": 24.5,
                "bodyfat": 18.0,
            },
            {
                "timeStamp": ts_evening,
                "weight": 80.5,
                "bmi": 24.7,
                "bodyfat": 18.2,
            },
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", target)

        assert len(result["data"]) == 2
        assert result["data"][0]["weight_kg"] == 80.0
        assert result["data"][0]["measured_at"] == datetime(2026, 4, 7, 7, 0, 0, tzinfo=timezone.utc)
        assert result["data"][1]["weight_kg"] == 80.5
        assert result["data"][1]["measured_at"] == datetime(2026, 4, 7, 20, 0, 0, tzinfo=timezone.utc)

    @patch("src.services.renpho.client.RenphoClient")
    def test_new_fields_none_when_absent(self, MockRenphoClient):
        """New fields (cardiac_index, body_shape, sport_flag) are None when absent from raw data."""
        target = date(2026, 4, 7)
        ts = int(datetime(2026, 4, 7, 10, 0, 0, tzinfo=timezone.utc).timestamp())

        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = [
            {"timeStamp": ts, "weight": 75.0}
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", target)

        assert len(result["data"]) == 1
        m = result["data"][0]
        assert m["cardiac_index"] is None
        assert m["body_shape"] is None
        assert m["sport_flag"] is None
        assert m["bmr_kcal"] is None
        assert m["body_age"] is None
        assert m["heart_rate"] is None
