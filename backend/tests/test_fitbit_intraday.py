"""Tests for intraday aggregation logic."""

from src.services.fitbit.intraday import aggregate_to_hourly


class TestAggregateToHourly:
    def test_groups_by_hour(self):
        datapoints = [
            {"time": "14:00:00", "value": 70},
            {"time": "14:01:00", "value": 80},
            {"time": "14:02:00", "value": 75},
            {"time": "15:00:00", "value": 90},
            {"time": "15:30:00", "value": 85},
        ]
        result = aggregate_to_hourly(datapoints, value_key="value")
        assert len(result) == 2
        h14 = result[14]
        assert h14["avg"] == 75.0
        assert h14["min"] == 70
        assert h14["max"] == 80
        assert h14["sample_count"] == 3
        h15 = result[15]
        assert h15["avg"] == 87.5
        assert h15["sample_count"] == 2

    def test_empty_input(self):
        assert aggregate_to_hourly([], value_key="value") == {}

    def test_steps_uses_sum_for_avg(self):
        datapoints = [
            {"time": "10:00:00", "value": 100},
            {"time": "10:01:00", "value": 50},
            {"time": "10:02:00", "value": 200},
        ]
        result = aggregate_to_hourly(datapoints, value_key="value", use_sum=True)
        assert result[10]["avg"] == 350
        assert result[10]["min"] == 50
        assert result[10]["max"] == 200
