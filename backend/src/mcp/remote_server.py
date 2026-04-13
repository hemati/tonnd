"""TONND Remote MCP Server — HTTP transport with OAuth 2.1 for claude.ai.

This server is mounted inside the main FastAPI app at /mcp.
Tools query the database directly (no HTTP overhead).
"""

import os
import uuid
from datetime import date

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token

from src.auth.scopes import SCOPE_METRICS, has_scope
from src.database import async_session_maker
from src.mcp.oauth_provider import TONNDOAuthProvider
from src.services.data_service import (
    compute_recovery_score,
    metric_to_dict,
    query_daily_activity,
    query_daily_body,
    query_daily_sleep,
    query_daily_vitals,
    query_exercise_logs,
    query_hourly_intraday,
    query_metrics,
    query_user_context,
)

BASE_URL = os.environ.get("MCP_BASE_URL", os.environ.get("FRONTEND_URL", "http://localhost:8080"))

oauth = TONNDOAuthProvider(base_url=BASE_URL + "/mcp")

mcp = FastMCP(
    "TONND Health Data",
    auth=oauth,
    instructions=(
        "TONND is a personal health tracking platform. Use these tools to access "
        "the user's fitness data from Fitbit (vitals, sleep, activity), "
        "Renpho (weight, body composition), and Hevy (workouts, muscle groups). "
        "Data is read-only and scoped to the authenticated user."
    ),
)


def _get_user_id(required_scope: str | None = None) -> uuid.UUID:
    """Extract user_id from the authenticated token's claims.

    Optionally enforce a required scope — raises ValueError if the token
    doesn't have the scope (prevents accessing data beyond the token's grant).
    """
    token = get_access_token()
    if not token or "sub" not in token.claims:
        raise ValueError("Not authenticated")
    if required_scope and not has_scope(token.scopes, required_scope):
        raise ValueError(f"Token missing required scope: {required_scope}")
    return uuid.UUID(token.claims["sub"])


MAX_LIMIT = 365


def _parse_dates(start_date: str | None, end_date: str | None) -> tuple[date | None, date | None]:
    sd = date.fromisoformat(start_date) if start_date else None
    ed = date.fromisoformat(end_date) if end_date else None
    return sd, ed


def _clamp_limit(limit: int) -> int:
    return max(1, min(limit, MAX_LIMIT))


@mcp.tool()
async def get_vitals(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 30,
) -> dict:
    """Get vital signs: heart rate, HRV (RMSSD), SpO2, breathing rate, VO2 max, skin temperature.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 30 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.
        limit: Max results (default 30).
    """
    user_id = _get_user_id("read:vitals")
    sd, ed = _parse_dates(start_date, end_date)
    async with async_session_maker() as session:
        rows = await query_daily_vitals(
            session, user_id, start_date=sd, end_date=ed, limit=_clamp_limit(limit),
        )
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}


@mcp.tool()
async def get_sleep(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 14,
) -> dict:
    """Get sleep data: duration, stages (deep/light/REM/awake), efficiency %, start/end times.

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        limit: Max results (default 14 = 2 weeks).
    """
    user_id = _get_user_id("read:sleep")
    sd, ed = _parse_dates(start_date, end_date)
    async with async_session_maker() as session:
        rows = await query_daily_sleep(
            session, user_id, start_date=sd, end_date=ed, limit=_clamp_limit(limit),
        )
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}


@mcp.tool()
async def get_body_composition(
    start_date: str | None = None,
    end_date: str | None = None,
    source: str | None = None,
    limit: int = 30,
) -> dict:
    """Get body composition: weight (kg), BMI, body fat %, muscle mass.

    Sources: fitbit (weight only from typed table), renpho (full body composition from legacy table).

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        source: Filter by source (fitbit or renpho).
        limit: Max results (default 30).
    """
    user_id = _get_user_id("read:body")
    sd, ed = _parse_dates(start_date, end_date)
    clamped = _clamp_limit(limit)
    results: list[dict] = []

    async with async_session_maker() as session:
        # Fitbit weight from typed table
        if source is None or source == "fitbit":
            body_rows = await query_daily_body(
                session, user_id, start_date=sd, end_date=ed,
                source="fitbit", limit=clamped,
            )
            results.extend(
                {
                    "date": r.date.isoformat(),
                    "source": r.source,
                    "weight_kg": r.weight_kg,
                    "bmi": r.bmi,
                    "body_fat_percent": r.body_fat_percent,
                }
                for r in body_rows
            )

        # Renpho body composition from legacy fitness_metrics table
        if source is None or source == "renpho":
            renpho_rows = await query_metrics(
                session, user_id, metric_types=["body_composition"],
                start_date=sd, end_date=ed, source="renpho", limit=clamped,
            )
            results.extend(metric_to_dict(r) for r in renpho_rows)

    # Sort combined results by date descending and trim to limit
    results.sort(key=lambda d: d.get("date", ""), reverse=True)
    results = results[:clamped]

    return {"count": len(results), "data": results}


@mcp.tool()
async def get_workouts(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 20,
) -> dict:
    """Get workout history from Hevy: exercises, sets/reps/weight, volume, muscle groups.

    Each workout includes a weighted muscle group breakdown (primary muscles = 1.0x, secondary = 0.4x).

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        limit: Max results (default 20).
    """
    user_id = _get_user_id("read:workouts")
    sd, ed = _parse_dates(start_date, end_date)
    async with async_session_maker() as session:
        rows = await query_metrics(session, user_id, metric_types=SCOPE_METRICS["read:workouts"], start_date=sd, end_date=ed, limit=_clamp_limit(limit))
    return {"count": len(rows), "data": [metric_to_dict(r) for r in rows]}


@mcp.tool()
async def get_activity(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 14,
) -> dict:
    """Get daily activity: steps, calories, distance, active minutes, active zone minutes.

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        limit: Max results (default 14).
    """
    user_id = _get_user_id("read:activity")
    sd, ed = _parse_dates(start_date, end_date)
    async with async_session_maker() as session:
        rows = await query_daily_activity(
            session, user_id, start_date=sd, end_date=ed, limit=_clamp_limit(limit),
        )
    return {"count": len(rows), "data": [r.to_dict() for r in rows]}


@mcp.tool()
async def get_recovery_score() -> dict:
    """Get current recovery score (0-100) based on latest HRV, sleep efficiency, and resting heart rate.

    Formula: 40% HRV + 35% sleep efficiency + 25% resting HR.
    Returns the score plus individual component values.
    """
    user_id = _get_user_id("read:recovery")
    async with async_session_maker() as session:
        vitals_rows = await query_daily_vitals(
            session, user_id, limit=1,
        )
        sleep_rows = await query_daily_sleep(
            session, user_id, limit=1,
        )

    # Build dicts compatible with compute_recovery_score
    latest_hrv = {"daily_rmssd": vitals_rows[0].daily_rmssd} if vitals_rows else None
    latest_hr = {"resting_heart_rate": vitals_rows[0].resting_heart_rate} if vitals_rows else None
    latest_sleep = {"efficiency": sleep_rows[0].efficiency} if sleep_rows else None

    return compute_recovery_score(latest_hrv, latest_sleep, latest_hr)


@mcp.tool()
async def get_all_metrics(
    start_date: str | None = None,
    end_date: str | None = None,
    metric_type: str | None = None,
    source: str | None = None,
    limit: int = 50,
) -> dict:
    """Get all raw health metrics with flexible filtering.

    Available metric types: activity, sleep, heart_rate, hrv, spo2, breathing_rate,
    vo2_max, temperature, active_zone_minutes, weight, body_composition, workout.

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        metric_type: Filter to a specific metric type.
        source: Filter by source (fitbit, renpho, hevy).
        limit: Max results (default 50).
    """
    user_id = _get_user_id()  # no scope check — /metrics does its own filtering
    sd, ed = _parse_dates(start_date, end_date)
    types = [metric_type] if metric_type else None
    async with async_session_maker() as session:
        rows = await query_metrics(session, user_id, metric_types=types, start_date=sd, end_date=ed, source=source, limit=_clamp_limit(limit))
    return {"count": len(rows), "data": [metric_to_dict(r) for r in rows]}


@mcp.tool()
async def get_intraday(
    metric_type: str,
    start_date: str | None = None,
    end_date: str | None = None,
    start_hour: int | None = None,
    end_hour: int | None = None,
    limit: int = 100,
) -> dict:
    """Get hourly intraday summaries for a metric type.

    Args:
        metric_type: heart_rate, hrv, spo2, steps, breathing_rate, or azm.
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        start_hour: Filter from this hour (0-23).
        end_hour: Filter to this hour (0-23).
        limit: Max results (default 100).
    """
    user_id = _get_user_id("read:vitals")
    sd, ed = _parse_dates(start_date, end_date)
    async with async_session_maker() as session:
        rows = await query_hourly_intraday(
            session, user_id, metric_type,
            start_date=sd, end_date=ed,
            start_hour=start_hour, end_hour=end_hour,
            limit=_clamp_limit(limit),
        )
    return {
        "count": len(rows),
        "data": [
            {
                "date": r.date.isoformat(),
                "hour": r.hour,
                "metric_type": r.metric_type,
                "source": r.source,
                "avg": r.avg_value,
                "min": r.min_value,
                "max": r.max_value,
                "samples": r.sample_count,
                "extra": r.extra,
            }
            for r in rows
        ],
    }


@mcp.tool()
async def get_exercise_logs(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 20,
) -> dict:
    """Get exercise/cardio session logs with heart rate zones, duration, and calories.

    Includes auto-detected activities (walking, running) and manual logs.

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        limit: Max results (default 20).
    """
    user_id = _get_user_id("read:activity")
    sd, ed = _parse_dates(start_date, end_date)
    async with async_session_maker() as session:
        rows = await query_exercise_logs(
            session, user_id, start_date=sd, end_date=ed, limit=_clamp_limit(limit),
        )
    return {
        "count": len(rows),
        "data": [
            {
                "date": r.date.isoformat(),
                "activity": r.activity_name,
                "duration_min": r.duration_minutes,
                "avg_hr": r.avg_heart_rate,
                "calories": r.calories,
                "distance_km": r.distance_km,
                "speed_kmh": r.speed_kmh,
                "log_type": r.log_type,
                "hr_zones": r.hr_zones,
                "source": r.source,
            }
            for r in rows
        ],
    }


@mcp.tool()
async def get_user_context() -> dict:
    """Get user profile and device context: age, gender, height, timezone, device status.

    Age is computed from date of birth. Device info shows battery level and last sync time.
    """
    user_id = _get_user_id("read:vitals")
    async with async_session_maker() as session:
        rows = await query_user_context(session, user_id)

    return {"count": len(rows), "data": [r.to_dict() for r in rows]}
