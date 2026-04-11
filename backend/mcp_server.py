"""TONND MCP Server — expose health data as tools for Claude Desktop.

Usage (stdio transport):
    python mcp_server.py

Claude Desktop config (~/.claude.ai/claude_desktop_config.json):
    {
      "mcpServers": {
        "tonnd": {
          "command": "python",
          "args": ["/path/to/backend/mcp_server.py"],
          "env": {
            "TONND_API_URL": "http://localhost:8080",
            "TONND_API_TOKEN": "tonnd_your_personal_access_token"
          }
        }
      }
    }
"""

import os

import httpx
from fastmcp import FastMCP

TONND_API_URL = os.environ.get("TONND_API_URL", "http://localhost:8080")
TONND_API_TOKEN = os.environ.get("TONND_API_TOKEN", "")

if not TONND_API_TOKEN:
    raise RuntimeError(
        "TONND_API_TOKEN environment variable is required. "
        "Create a token at /settings in the TONND dashboard."
    )

mcp = FastMCP(
    "TONND Health Data",
    instructions=(
        "TONND is a personal health tracking platform. Use these tools to access "
        "the user's fitness data from Fitbit (vitals, sleep, activity), "
        "Renpho (weight, body composition), and Hevy (workouts, muscle groups). "
        "Data is read-only and scoped to the authenticated user."
    ),
)

# Reuse a single client for connection pooling / HTTP keep-alive
_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=TONND_API_URL, timeout=30, follow_redirects=False
        )
    return _client


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TONND_API_TOKEN}"}


def _params(
    start_date: str | None = None,
    end_date: str | None = None,
    source: str | None = None,
    limit: int = 50,
) -> dict:
    p: dict = {"limit": limit, "order": "desc"}
    if start_date:
        p["start_date"] = start_date
    if end_date:
        p["end_date"] = end_date
    if source:
        p["source"] = source
    return p


async def _get(path: str, **kwargs) -> dict:
    client = await _get_client()
    resp = await client.get(path, headers=_headers(), params=_params(**kwargs))
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
async def get_vitals(
    start_date: str | None = None,
    end_date: str | None = None,
    metric_type: str | None = None,
    limit: int = 30,
) -> dict:
    """Get vital signs: heart rate, HRV (RMSSD), SpO2, breathing rate, VO2 max, skin temperature.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 30 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.
        metric_type: Filter to a specific vital (heart_rate, hrv, spo2, breathing_rate, vo2_max, temperature).
        limit: Max results (default 30).
    """
    path = f"/api/v1/vitals/{metric_type}" if metric_type else "/api/v1/vitals"
    return await _get(path, start_date=start_date, end_date=end_date, limit=limit)


@mcp.tool()
async def get_sleep(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 14,
) -> dict:
    """Get sleep data: duration, stages (deep/light/REM/awake), efficiency %.

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        limit: Max results (default 14 = 2 weeks).
    """
    return await _get("/api/v1/sleep", start_date=start_date, end_date=end_date, limit=limit)


@mcp.tool()
async def get_body_composition(
    start_date: str | None = None,
    end_date: str | None = None,
    source: str | None = None,
    limit: int = 30,
) -> dict:
    """Get body composition: weight (kg), BMI, body fat %, muscle mass.

    Sources: fitbit (weight only), renpho (full body composition).

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        source: Filter by source (fitbit or renpho).
        limit: Max results (default 30).
    """
    return await _get("/api/v1/body", start_date=start_date, end_date=end_date, source=source, limit=limit)


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
    return await _get("/api/v1/workouts", start_date=start_date, end_date=end_date, limit=limit)


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
    return await _get("/api/v1/activity", start_date=start_date, end_date=end_date, limit=limit)


@mcp.tool()
async def get_recovery_score() -> dict:
    """Get current recovery score (0-100) based on latest HRV, sleep efficiency, and resting heart rate.

    Formula: 40% HRV + 35% sleep efficiency + 25% resting HR.
    Returns the score plus individual component values.
    """
    return await _get("/api/v1/recovery")


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
    params = _params(start_date=start_date, end_date=end_date, source=source, limit=limit)
    if metric_type:
        params["metric_type"] = metric_type
    client = await _get_client()
    resp = await client.get("/api/v1/metrics", headers=_headers(), params=params)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    mcp.run()
