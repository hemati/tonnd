import pytest
from unittest.mock import AsyncMock

from src.services.fitbit.client import FitbitClient
from src.services.fitbit.ranges import parse_range_responses


def test_parse_range_responses_merges_by_date():
    hr = {
        "activities-heart": [
            {
                "dateTime": "2026-05-01",
                "value": {
                    "restingHeartRate": 60,
                    "heartRateZones": [
                        {
                            "name": "Fat Burn",
                            "min": 90,
                            "max": 110,
                            "minutes": 30,
                            "caloriesOut": 200,
                        }
                    ],
                },
            },
            {
                "dateTime": "2026-05-02",
                "value": {"restingHeartRate": 62, "heartRateZones": []},
            },
        ]
    }
    hrv = {
        "hrv": [
            {"dateTime": "2026-05-01", "value": {"dailyRmssd": 45.0, "deepRmssd": 52.0}}
        ]
    }
    spo2 = [
        {"dateTime": "2026-05-01", "value": {"avg": 97.5, "min": 95.0, "max": 99.0}}
    ]
    br = {"br": [{"dateTime": "2026-05-01", "value": {"breathingRate": 15.0}}]}
    vo2 = {"cardioScore": [{"dateTime": "2026-05-01", "value": {"vo2Max": "42"}}]}
    temp = {
        "tempSkin": [{"dateTime": "2026-05-01", "value": {"nightlyRelative": -0.2}}]
    }
    azm = {
        "activities-active-zone-minutes": [
            {
                "dateTime": "2026-05-01",
                "value": {
                    "fatBurnActiveZoneMinutes": 30,
                    "cardioActiveZoneMinutes": 15,
                    "peakActiveZoneMinutes": 5,
                },
            }
        ]
    }
    sleep = {
        "sleep": [
            {
                "logId": 111,
                "dateOfSleep": "2026-05-01",
                "isMainSleep": True,
                "startTime": "2026-05-01T23:00:00.000",
                "endTime": "2026-05-02T07:00:00.000",
                "duration": 28800000,
                "efficiency": 90,
                "minutesToFallAsleep": 10,
                "timeInBed": 500,
                "levels": {
                    "summary": {
                        "deep": {"minutes": 80},
                        "light": {"minutes": 200},
                        "rem": {"minutes": 100},
                        "wake": {"minutes": 20},
                    },
                    "data": [],
                },
            }
        ]
    }
    weight = {
        "weight": [
            {
                "date": "2026-05-01",
                "time": "08:00:00",
                "weight": 80.0,
                "bmi": 25.0,
                "fat": 18.0,
                "logId": 1,
            }
        ]
    }
    activity = {
        "steps": {
            "activities-steps": [
                {"dateTime": "2026-05-01", "value": "10000"},
                {"dateTime": "2026-05-02", "value": "8000"},
            ]
        },
        "calories": {
            "activities-calories": [{"dateTime": "2026-05-01", "value": "2500"}]
        },
        "distance": {
            "activities-distance": [{"dateTime": "2026-05-01", "value": "8.0"}]
        },
        "floors": {"activities-floors": [{"dateTime": "2026-05-01", "value": "10"}]},
        "minutesSedentary": {
            "activities-minutesSedentary": [{"dateTime": "2026-05-01", "value": "600"}]
        },
        "minutesLightlyActive": {
            "activities-minutesLightlyActive": [
                {"dateTime": "2026-05-01", "value": "200"}
            ]
        },
        "minutesFairlyActive": {
            "activities-minutesFairlyActive": [
                {"dateTime": "2026-05-01", "value": "30"}
            ]
        },
        "minutesVeryActive": {
            "activities-minutesVeryActive": [{"dateTime": "2026-05-01", "value": "15"}]
        },
    }

    by_date = parse_range_responses(
        hr, hrv, spo2, br, vo2, temp, azm, sleep, weight, activity
    )

    d1 = by_date["2026-05-01"]
    assert d1["heart_rate"]["resting_heart_rate"] == 60.0
    assert d1["heart_rate"]["zones"]["Fat Burn"]["minutes"] == 30
    assert d1["hrv"] == {"daily_rmssd": 45.0, "deep_rmssd": 52.0}
    assert d1["spo2"] == {"avg": 97.5, "min": 95.0, "max": 99.0}
    assert d1["breathing_rate"] == {"breathing_rate": 15.0}
    assert d1["vo2_max"] == {"vo2_max": 42.0}
    assert d1["temperature"] == {"relative_deviation": -0.2}
    assert d1["active_zone_minutes"]["total_minutes"] == 50
    assert d1["sleep"][0]["external_id"] == "111"
    assert d1["weight"]["weight_kg"] == 80.0
    assert d1["weight"]["body_fat_percent"] == 18.0
    assert d1["activity"]["steps"] == 10000
    assert d1["activity"]["calories_burned"] == 2500.0
    assert d1["activity"]["active_minutes"] == 45  # fairly(30) + very(15)
    assert d1["activity"]["distance_km"] == 8.0
    # 2026-05-02 has only HR + steps
    d2 = by_date["2026-05-02"]
    assert d2["heart_rate"]["resting_heart_rate"] == 62.0
    assert d2["activity"]["steps"] == 8000
    assert "hrv" not in d2


def test_parse_range_responses_empty_returns_empty_dict():
    out = parse_range_responses({}, {}, [], {}, {}, {}, {}, {}, {}, {})
    assert out == {}
    assert type(out) is dict


def test_parse_range_responses_skips_entries_without_datetime():
    # One good HR entry, one malformed (no dateTime) — must not abort the batch.
    hr = {
        "activities-heart": [
            {"value": {"restingHeartRate": 61, "heartRateZones": []}},  # no dateTime
            {
                "dateTime": "2026-05-03",
                "value": {"restingHeartRate": 64, "heartRateZones": []},
            },
        ]
    }
    activity = {
        "steps": {
            "activities-steps": [
                {"value": "999"},  # no dateTime
                {"dateTime": "2026-05-03", "value": "5000"},
            ]
        }
    }
    out = parse_range_responses(hr, {}, [], {}, {}, {}, {}, {}, {}, activity)
    assert set(out.keys()) == {"2026-05-03"}
    assert out["2026-05-03"]["heart_rate"]["resting_heart_rate"] == 64.0
    assert out["2026-05-03"]["activity"]["steps"] == 5000


def test_parse_range_responses_multiple_sleep_entries_same_day():
    sleep = {
        "sleep": [
            {
                "logId": 1,
                "dateOfSleep": "2026-05-04",
                "isMainSleep": True,
                "duration": 28800000,
                "levels": {"summary": {}, "data": []},
            },
            {
                "logId": 2,
                "dateOfSleep": "2026-05-04",
                "isMainSleep": False,
                "duration": 1800000,
                "levels": {"summary": {}, "data": []},
            },
        ]
    }
    out = parse_range_responses({}, {}, [], {}, {}, {}, {}, sleep, {}, {})
    entries = out["2026-05-04"]["sleep"]
    assert len(entries) == 2
    assert {e["external_id"] for e in entries} == {"1", "2"}


def test_parse_range_responses_latest_weight_of_day_out_of_order():
    weight = {
        "weight": [
            {
                "date": "2026-05-05",
                "time": "20:00:00",
                "weight": 79.5,
                "bmi": 24.5,
                "fat": 17.0,
            },
            {
                "date": "2026-05-05",
                "time": "08:00:00",
                "weight": 80.5,
                "bmi": 25.0,
                "fat": 18.0,
            },
        ]
    }
    out = parse_range_responses({}, {}, [], {}, {}, {}, {}, {}, weight, {})
    # later time (20:00) wins regardless of list order
    assert out["2026-05-05"]["weight"]["weight_kg"] == 79.5
    assert "_time" not in out["2026-05-05"]["weight"]


@pytest.mark.asyncio
async def test_get_all_data_for_range_request_budget():
    """A 30-day range must cost <= 20 Fitbit requests (not ~330)."""
    client = FitbitClient("token")
    client._make_request = AsyncMock(return_value={})
    await client.get_all_data_for_range("2026-05-01", "2026-05-30")
    # 7 vitals + sleep + weight + 8 activity resources = 17
    assert client._make_request.call_count == 17
    assert client._make_request.call_count <= 20
