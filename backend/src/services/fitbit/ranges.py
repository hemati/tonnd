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


def parse_range_responses(hr, hrv, spo2, br, vo2, temp, azm, sleep, weight, activity):
    """Merge all range responses into {date_iso: data_dict}."""
    by_date: dict[str, dict] = defaultdict(dict)

    # Heart rate
    for e in _entries(hr, "activities-heart"):
        v = e.get("value", {})
        by_date[e["dateTime"]]["heart_rate"] = {
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

    # HRV
    for e in _entries(hrv, "hrv"):
        v = e.get("value", {})
        by_date[e["dateTime"]]["hrv"] = {
            "daily_rmssd": safe_float(v.get("dailyRmssd")),
            "deep_rmssd": safe_float(v.get("deepRmssd")),
        }

    # SpO2 (bare list)
    for e in _entries(spo2, "spo2"):
        v = e.get("value", {})
        by_date[e["dateTime"]]["spo2"] = {
            "avg": safe_float(v.get("avg")),
            "min": safe_float(v.get("min")),
            "max": safe_float(v.get("max")),
        }

    # Breathing rate
    for e in _entries(br, "br"):
        v = e.get("value", {})
        by_date[e["dateTime"]]["breathing_rate"] = {
            "breathing_rate": safe_float(v.get("breathingRate")),
        }

    # VO2 max
    for e in _entries(vo2, "cardioScore"):
        v = e.get("value", {})
        by_date[e["dateTime"]]["vo2_max"] = {"vo2_max": safe_float(v.get("vo2Max"))}

    # Skin temperature
    for e in _entries(temp, "tempSkin"):
        v = e.get("value", {})
        by_date[e["dateTime"]]["temperature"] = {
            "relative_deviation": safe_float(v.get("nightlyRelative")),
        }

    # Active Zone Minutes
    for e in _entries(azm, "activities-active-zone-minutes"):
        v = e.get("value", {})
        fb = v.get("fatBurnActiveZoneMinutes", 0)
        ca = v.get("cardioActiveZoneMinutes", 0)
        pk = v.get("peakActiveZoneMinutes", 0)
        by_date[e["dateTime"]]["active_zone_minutes"] = {
            "fat_burn_minutes": fb,
            "cardio_minutes": ca,
            "peak_minutes": pk,
            "total_minutes": fb + ca + pk,
        }

    # Sleep (group entries by dateOfSleep)
    sleep_by_date: dict[str, list] = defaultdict(list)
    for s in _entries(sleep, "sleep"):
        levels = s.get("levels", {}).get("summary", {})
        levels_data = s.get("levels", {}).get("data", [])
        d = s.get("dateOfSleep")
        if not d:
            continue
        sleep_by_date[d].append(
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
    for d, entries in sleep_by_date.items():
        by_date[d]["sleep"] = entries

    # Weight / body (fat comes from the weight log entry, matching the daily path)
    for w in _entries(weight, "weight"):
        d = w.get("date")
        if not d:
            continue
        existing = by_date[d].get("weight")
        candidate = {
            "weight_kg": safe_float(w.get("weight")),
            "body_fat_percent": safe_float(w.get("fat")),
            "bmi": safe_float(w.get("bmi")),
            "_time": w.get("time", "00:00:00"),
        }
        # keep the latest entry of the day
        if existing is None or candidate["_time"] >= existing.get("_time", ""):
            by_date[d]["weight"] = candidate

    # Activity time-series (one resource per call)
    for resource in ACTIVITY_RESOURCES:
        payload = activity.get(resource, {})
        for e in _entries(payload, f"activities-{resource}"):
            d = e["dateTime"]
            act = by_date[d].setdefault("activity", {})
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
            elif resource == "minutesFairlyActive":
                act["_fairly"] = int(safe_float(val) or 0)
            elif resource == "minutesVeryActive":
                act["_very"] = int(safe_float(val) or 0)

    # Finalize activity: derive active_minutes, drop helpers, add null bmr
    for d, data in by_date.items():
        act = data.get("activity")
        if act is not None:
            fairly = act.pop("_fairly", 0)
            very = act.pop("_very", 0)
            act["active_minutes"] = fairly + very
            act.setdefault("calories_bmr", None)

    # Strip the internal _time helper from weight
    for data in by_date.values():
        if "weight" in data:
            data["weight"].pop("_time", None)

    return dict(by_date)
