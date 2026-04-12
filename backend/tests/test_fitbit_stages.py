"""Tests for sleep stages 30s summary computation."""

from src.services.fitbit.stages import compute_stages_summary


class TestComputeStagesSummary:
    def test_basic_summary(self):
        levels_data = [
            {"dateTime": "2026-04-10T23:00:00", "level": "light", "seconds": 600},
            {"dateTime": "2026-04-10T23:10:00", "level": "deep", "seconds": 1800},
            {"dateTime": "2026-04-10T23:40:00", "level": "light", "seconds": 300},
            {"dateTime": "2026-04-10T23:45:00", "level": "rem", "seconds": 1200},
            {"dateTime": "2026-04-11T00:05:00", "level": "wake", "seconds": 120},
            {"dateTime": "2026-04-11T00:07:00", "level": "deep", "seconds": 900},
            {"dateTime": "2026-04-11T00:22:00", "level": "rem", "seconds": 600},
        ]
        result = compute_stages_summary(levels_data)
        assert result["transition_count"] == 7
        assert result["longest_uninterrupted_deep_minutes"] == 30.0  # 1800s
        assert result["longest_uninterrupted_rem_minutes"] == 20.0  # 1200s
        assert "deep" in result["avg_stage_duration_minutes"]
        assert result["avg_stage_duration_minutes"]["deep"] == 22.5  # (1800+900)/2 / 60

    def test_empty_data(self):
        result = compute_stages_summary([])
        assert result["transition_count"] == 0
        assert result["longest_uninterrupted_deep_minutes"] == 0
        assert result["longest_uninterrupted_rem_minutes"] == 0

    def test_no_deep_sleep(self):
        levels_data = [
            {"dateTime": "2026-04-10T23:00:00", "level": "light", "seconds": 600},
            {"dateTime": "2026-04-10T23:10:00", "level": "rem", "seconds": 1200},
        ]
        result = compute_stages_summary(levels_data)
        assert result["longest_uninterrupted_deep_minutes"] == 0
        assert result["longest_uninterrupted_rem_minutes"] == 20.0
