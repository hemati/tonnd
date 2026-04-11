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
        """When measurements contain a matching date, weight + body_composition are returned."""
        target = date(2026, 4, 7)
        # timestamp for 2026-04-07 00:00:00 UTC
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
            }
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", target)

        assert result["errors"] == []
        assert result["data"]["weight"]["weight_kg"] == 75.5
        assert result["data"]["weight"]["bmi"] == 23.1
        assert result["data"]["weight"]["body_fat_percent"] == 17.5
        assert result["data"]["body_composition"]["body_fat_percent"] == 17.5
        assert result["data"]["body_composition"]["muscle_mass_percent"] == 42.0
        assert result["data"]["body_composition"]["heart_rate"] == 68

    @patch("src.services.renpho.client.RenphoClient")
    def test_non_matching_date_returns_empty(self, MockRenphoClient):
        """Measurements from a different date are not included."""
        target = date(2026, 4, 7)
        # Timestamp for a different day
        wrong_ts = int(datetime(2026, 4, 6, 10, 0, 0, tzinfo=timezone.utc).timestamp())

        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = [
            {"timeStamp": wrong_ts, "weight": 75.0}
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", target)

        assert result["data"] == {}
        assert result["errors"] == []

    @patch("src.services.renpho.client.RenphoClient")
    def test_empty_measurements(self, MockRenphoClient):
        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = []
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", date(2026, 4, 7))

        assert result["data"] == {}
        assert result["errors"] == []

    @patch("src.services.renpho.client.RenphoClient")
    def test_api_error_collected_in_errors(self, MockRenphoClient):
        """When RenphoClient raises, error is added to result['errors']."""
        MockRenphoClient.side_effect = Exception("network failure")

        result = get_measurements_for_date("u@test.com", "pw", date(2026, 4, 7))

        assert len(result["errors"]) == 1
        assert "renpho" in result["errors"][0]
        assert result["data"] == {}

    @patch("src.services.renpho.client.RenphoClient")
    def test_measurement_without_timestamp_skipped(self, MockRenphoClient):
        """Measurements missing both timeStamp and time_stamp are skipped."""
        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = [
            {"weight": 80.0}  # no timestamp at all
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", date(2026, 4, 7))
        assert result["data"] == {}

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
        assert result["data"]["weight"]["weight_kg"] == 82.0

    @patch("src.services.renpho.client.RenphoClient")
    def test_zero_weight_not_added(self, MockRenphoClient):
        """Weight of 0 should not be added to data."""
        target = date(2026, 4, 7)
        ts = int(datetime(2026, 4, 7, 10, 0, 0, tzinfo=timezone.utc).timestamp())

        mock_instance = MagicMock()
        mock_instance.get_all_measurements.return_value = [
            {"timeStamp": ts, "weight": 0, "bodyfat": 20.0}
        ]
        MockRenphoClient.return_value = mock_instance

        result = get_measurements_for_date("u@test.com", "pw", target)
        # body_composition should still be present, but weight should not
        assert "weight" not in result["data"]
        assert "body_composition" in result["data"]
