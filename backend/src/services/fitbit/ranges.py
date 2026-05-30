"""Parse Fitbit range/time-series responses into per-date data dicts.

The output mirrors the shape of FitbitClient.get_all_data_for_date()["data"],
so scheduler._distribute_daily_data can consume both paths identically.
"""

from collections import defaultdict

from src.services.fitbit.stages import compute_stages_summary
from src.utils.safe_parse import safe_float

# Activity time-series resources fetched for the range path.
# caloriesBMR has no time-series resource -> calories_bmr stays null for backfill.
ACTIVITY_RESOURCES = [
    "steps",
    "calories",
    "distance",
    "floors",
    "minutesSedentary",
    "minutesLightlyActive",
    "minutesFairlyActive",
    "minutesVeryActive",
]


def _entries(payload, key):
    """Range payloads are usually {key: [..]} but SpO2 is a bare list."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get(key, []) or []
    return []


def _heart_rate(v):
    return {
        "resting_heart_rate": safe_float(v.get("restingHeartRate")),
        "zones": {
            z["name"]: {
                "min": z.get("min"),
                "max": z.get("max"),
                "minutes": z.get("minutes"),
                "caloriesOut": z.get("caloriesOut"),
            }
            for z in v.get("heartRateZones", [])
        },
    }


def _active_zone_minutes(v):
    fb = v.get("fatBurnActiveZoneMinutes", 0)
    ca = v.get("cardioActiveZoneMinutes", 0)
    pk = v.get("peakActiveZoneMinutes", 0)
    return {
        "fat_burn_minutes": fb,
        "cardio_minutes": ca,
        "peak_minutes": pk,
        "total_minutes": fb + ca + pk,
    }


def parse_range_responses(hr, hrv, spo2, br, vo2, temp, azm, sleep, weight, activity):
    """Merge all range responses into {date_iso: data_dict}."""
    by_date: dict[str, dict] = defaultdict(dict)

    # One-value-per-day metrics: (payload, response_key, out_key, value_builder).
    simple_metrics = (
        (hr, "activities-heart", "heart_rate", _heart_rate),
        (
            hrv,
            "hrv",
            "hrv",
            lambda v: {
                "daily_rmssd": safe_float(v.get("dailyRmssd")),
                "deep_rmssd": safe_float(v.get("deepRmssd")),
            },
        ),
        (
            spo2,
            "spo2",
            "spo2",
            lambda v: {
                "avg": safe_float(v.get("avg")),
                "min": safe_float(v.get("min")),
                "max": safe_float(v.get("max")),
            },
        ),
        (
            br,
            "br",
            "breathing_rate",
            lambda v: {
                "breathing_rate": safe_float(v.get("breathingRate")),
            },
        ),
        (
            vo2,
            "cardioScore",
            "vo2_max",
            lambda v: {
                "vo2_max": safe_float(v.get("vo2Max")),
            },
        ),
        (
            temp,
            "tempSkin",
            "temperature",
            lambda v: {
                "relative_deviation": safe_float(v.get("nightlyRelative")),
            },
        ),
        (
            azm,
            "activities-active-zone-minutes",
            "active_zone_minutes",
            _active_zone_minutes,
        ),
    )
    for payload, response_key, out_key, build in simple_metrics:
        for e in _entries(payload, response_key):
            dt = e.get("dateTime")
            if not dt:
                continue
            by_date[dt][out_key] = build(e.get("value", {}))

    # Sleep (group entries by dateOfSleep; multiple naps per day allowed).
    for s in _entries(sleep, "sleep"):
        d = s.get("dateOfSleep")
        if not d:
            continue
        levels = s.get("levels", {}).get("summary", {})
        levels_data = s.get("levels", {}).get("data", [])
        by_date[d].setdefault("sleep", []).append(
            {
                "external_id": str(s.get("logId", "")),
                "date_of_sleep": d,
                "is_main_sleep": s.get("isMainSleep", False),
                "start_time": s.get("startTime"),
                "end_time": s.get("endTime"),
                "total_minutes": s.get("duration", 0) // 60000,
                "deep_minutes": levels.get("deep", {}).get("minutes"),
                "light_minutes": levels.get("light", {}).get("minutes"),
                "rem_minutes": levels.get("rem", {}).get("minutes"),
                "awake_minutes": levels.get("wake", {}).get("minutes"),
                "efficiency": s.get("efficiency"),
                "minutes_to_fall_asleep": s.get("minutesToFallAsleep"),
                "time_in_bed": s.get("timeInBed"),
                "stages_30s_summary": compute_stages_summary(levels_data),
            }
        )

    # Weight / body (fat comes from the weight log entry, matching the daily
    # path). Keep the latest entry of the day; track its time locally so no
    # helper key leaks into the output.
    weight_time: dict[str, str] = {}
    for w in _entries(weight, "weight"):
        d = w.get("date")
        if not d:
            continue
        t = w.get("time", "00:00:00")
        if d not in weight_time or t >= weight_time[d]:
            weight_time[d] = t
            by_date[d]["weight"] = {
                "weight_kg": safe_float(w.get("weight")),
                "body_fat_percent": safe_float(w.get("fat")),
                "bmi": safe_float(w.get("bmi")),
            }

    # Activity time-series (one resource per call). active_minutes accumulates
    # fairly + very; calories_bmr has no range resource, so it stays None.
    for resource in ACTIVITY_RESOURCES:
        for e in _entries(activity.get(resource, {}), f"activities-{resource}"):
            dt = e.get("dateTime")
            if not dt:
                continue
            act = by_date[dt].setdefault(
                "activity", {"active_minutes": 0, "calories_bmr": None}
            )
            val = e.get("value")
            if resource == "steps":
                act["steps"] = int(safe_float(val) or 0)
            elif resource == "calories":
                act["calories_burned"] = safe_float(val)
            elif resource == "distance":
                act["distance_km"] = safe_float(val)
            elif resource == "floors":
                act["floors"] = int(safe_float(val) or 0)
            elif resource == "minutesSedentary":
                act["sedentary_minutes"] = int(safe_float(val) or 0)
            elif resource == "minutesLightlyActive":
                act["lightly_active_minutes"] = int(safe_float(val) or 0)
            elif resource in ("minutesFairlyActive", "minutesVeryActive"):
                act["active_minutes"] += int(safe_float(val) or 0)

    return dict(by_date)
