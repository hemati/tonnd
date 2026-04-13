"""Tests for the shared data service (compute_recovery_score)."""

from src.services.data_service import compute_recovery_score


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
