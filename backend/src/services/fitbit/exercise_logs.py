"""Fitbit Activity Log List parsing."""

from datetime import datetime, timedelta


def parse_exercise_logs(api_response: dict) -> list[dict]:
    """Parse GET /1/user/-/activities/list.json response into exercise log dicts."""
    activities = api_response.get("activities", [])
    logs = []

    for a in activities:
        duration_ms = a.get("activeDuration", 0)
        duration_minutes = duration_ms // 60000

        started_at = a.get("startTime")
        ended_at = None
        if started_at and duration_ms:
            try:
                start_dt = datetime.fromisoformat(started_at)
                ended_at = (start_dt + timedelta(milliseconds=duration_ms)).isoformat()
            except (ValueError, TypeError):
                pass

        hr_zones = None
        raw_zones = a.get("heartRateZones", [])
        if raw_zones:
            hr_zones = [
                {"name": z.get("name"), "min": z.get("min"),
                 "max": z.get("max"), "minutes": z.get("minutes")}
                for z in raw_zones
            ]

        logs.append({
            "external_id": str(a.get("logId", "")),
            "activity_name": a.get("activityName"),
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_minutes": duration_minutes,
            "avg_heart_rate": a.get("averageHeartRate"),
            "calories": a.get("calories"),
            "distance_km": a.get("distance"),
            "elevation_gain": a.get("elevationGain"),
            "speed_kmh": a.get("speed"),
            "log_type": a.get("logType"),
            "hr_zones": hr_zones,
        })

    return logs
