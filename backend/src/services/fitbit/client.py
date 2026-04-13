"""
Fitbit API client for OAuth and data retrieval.
"""

import base64
import logging
import os
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = "https://api.fitbit.com"


def _safe_float(val) -> float | None:
    """Fitbit API sometimes returns numeric values as strings."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"

# Fitbit API scopes required
SCOPES = [
    "activity",
    "heartrate",
    "sleep",
    "weight",
    "profile",
    "respiratory_rate",  # For breathing rate
    "oxygen_saturation",  # For SpO2
    "cardio_fitness",  # For VO2 Max
    "temperature",  # For skin temperature
    "settings",  # For device settings & user preferences
]

CURRENT_SCOPES_VERSION = 2

# Get environment from Lambda env var
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")


def get_fitbit_credentials() -> tuple[str, str]:
    """Get Fitbit OAuth credentials from environment variables."""
    client_id = os.environ.get("FITBIT_CLIENT_ID", "")
    client_secret = os.environ.get("FITBIT_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        raise RuntimeError(
            "FITBIT_CLIENT_ID and FITBIT_CLIENT_SECRET must be set. "
            "See .env.example for details."
        )

    return client_id, client_secret


def get_authorization_url(redirect_uri: str, state: str) -> str:
    """Generate Fitbit OAuth authorization URL."""
    client_id, _ = get_fitbit_credentials()

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "state": state,
        "prompt": "consent",
    }

    return f"{AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for access and refresh tokens."""
    client_id, client_secret = get_fitbit_credentials()

    # Fitbit requires Basic Auth with client_id:client_secret
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, headers=headers, data=data)

        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            raise Exception(f"Failed to exchange code: {response.text}")

        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Refresh an expired access token."""
    client_id, client_secret = get_fitbit_credentials()

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, headers=headers, data=data)

        if response.status_code == 401 or "invalid_grant" in response.text:
            raise TokenExpiredError("Refresh token is invalid or expired")

        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.text}")
            raise FitbitAPIError(f"Failed to refresh token: {response.status_code}")

        return response.json()


async def revoke_token(access_token: str) -> bool:
    """Revoke a Fitbit access token."""
    client_id, client_secret = get_fitbit_credentials()
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {"token": access_token}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.fitbit.com/oauth2/revoke", headers=headers, data=data
        )
        return response.status_code == 200


class FitbitClient:
    """Client for interacting with Fitbit API."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    async def _make_request(self, endpoint: str) -> dict:
        """Make an authenticated request to Fitbit API."""
        url = f"{BASE_URL}{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)

            if response.status_code == 401:
                raise TokenExpiredError("Access token is expired or invalid")

            if response.status_code == 429:
                raise RateLimitError("Fitbit API rate limit exceeded")

            if response.status_code != 200:
                logger.error(
                    f"Fitbit API error: {response.status_code} - {response.text}"
                )
                raise FitbitAPIError(f"API request failed: {response.text}")

            return response.json()

    async def get_profile(self) -> dict:
        """Get user profile information."""
        return await self._make_request("/1/user/-/profile.json")

    async def get_weight(self, date: str) -> dict:
        """
        Get weight data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Weight log entries for the date
        """
        return await self._make_request(f"/1/user/-/body/log/weight/date/{date}.json")

    async def get_weight_range(self, start_date: str, end_date: str) -> dict:
        """
        Get weight data for a date range (max 31 days).

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        return await self._make_request(
            f"/1/user/-/body/log/weight/date/{start_date}/{end_date}.json"
        )

    async def get_body_fat(self, date: str) -> dict:
        """Get body fat percentage for a specific date."""
        return await self._make_request(f"/1/user/-/body/log/fat/date/{date}.json")

    async def get_activity(self, date: str) -> dict:
        """
        Get activity summary for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Activity summary including steps, calories, distance
        """
        return await self._make_request(f"/1/user/-/activities/date/{date}.json")

    async def get_sleep(self, date: str) -> dict:
        """
        Get sleep data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Sleep log entries for the date
        """
        return await self._make_request(f"/1.2/user/-/sleep/date/{date}.json")

    async def get_heart_rate(self, date: str) -> dict:
        """
        Get heart rate data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Heart rate summary and zones for the date
        """
        return await self._make_request(
            f"/1/user/-/activities/heart/date/{date}/1d.json"
        )

    async def get_hrv(self, date: str) -> dict:
        """
        Get heart rate variability (HRV) data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            HRV summary including RMSSD and coverage
        """
        return await self._make_request(f"/1/user/-/hrv/date/{date}.json")

    async def get_spo2(self, date: str) -> dict:
        """
        Get blood oxygen saturation (SpO2) data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            SpO2 values (min, max, avg) recorded during sleep
        """
        return await self._make_request(f"/1/user/-/spo2/date/{date}.json")

    async def get_breathing_rate(self, date: str) -> dict:
        """
        Get breathing rate data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Breathing rate summary (breaths per minute during sleep)
        """
        return await self._make_request(f"/1/user/-/br/date/{date}.json")

    async def get_vo2_max(self, date: str) -> dict:
        """
        Get VO2 Max (cardio fitness score) data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            VO2 Max value indicating cardiovascular fitness level
        """
        return await self._make_request(f"/1/user/-/cardioscore/date/{date}.json")

    async def get_skin_temperature(self, date: str) -> dict:
        """
        Get skin temperature variation data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Skin temperature deviation from baseline during sleep
        """
        return await self._make_request(f"/1/user/-/temp/skin/date/{date}.json")

    async def get_active_zone_minutes(self, date: str) -> dict:
        """
        Get active zone minutes data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Active Zone Minutes breakdown (fat burn, cardio, peak)
        """
        return await self._make_request(
            f"/1/user/-/activities/active-zone-minutes/date/{date}/1d.json"
        )

    async def get_exercise_logs(self, after_date: str, limit: int = 20) -> dict:
        """GET /1/user/-/activities/list.json — per-exercise sessions."""
        return await self._make_request(
            f"/1/user/-/activities/list.json?afterDate={after_date}&sort=asc&limit={limit}&offset=0"
        )

    async def get_devices(self) -> list:
        """GET /1/user/-/devices.json — device info."""
        return await self._make_request("/1/user/-/devices.json")

    async def get_all_data_for_date(self, date: str) -> dict:
        """
        Fetch all fitness data for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Dict containing all metric types
        """
        data = {}
        errors = []

        # Fetch all metrics, collecting errors but not failing completely
        try:
            weight_data = await self.get_weight(date)
            if weight_data.get("weight"):
                # Get the most recent weight entry for the day
                latest = weight_data["weight"][-1] if weight_data["weight"] else None
                if latest:
                    weight_date = latest.get("date", date)
                    weight_time = latest.get("time", "00:00:00")
                    try:
                        from datetime import datetime as dt_cls
                        from datetime import timezone as tz

                        measured_at = dt_cls.strptime(
                            f"{weight_date} {weight_time}", "%Y-%m-%d %H:%M:%S"
                        ).replace(tzinfo=tz.utc)
                    except (ValueError, TypeError):
                        from datetime import datetime as dt_cls
                        from datetime import timezone as tz

                        measured_at = dt_cls.strptime(
                            str(weight_date), "%Y-%m-%d"
                        ).replace(tzinfo=tz.utc)

                    data["weight"] = {
                        "weight_kg": _safe_float(latest.get("weight")),
                        "body_fat_percent": _safe_float(latest.get("fat")),
                        "bmi": _safe_float(latest.get("bmi")),
                        "measured_at": measured_at,
                    }
        except Exception as e:
            errors.append(f"weight: {str(e)}")
            logger.warning(f"Failed to fetch weight data: {e}")

        try:
            activity_data = await self.get_activity(date)
            summary = activity_data.get("summary", {})
            data["activity"] = {
                "steps": summary.get("steps", 0),
                "calories_burned": summary.get("caloriesOut"),
                "distance_km": None,
                "active_minutes": (
                    summary.get("veryActiveMinutes", 0)
                    + summary.get("fairlyActiveMinutes", 0)
                ),
                "sedentary_minutes": summary.get("sedentaryMinutes"),
                "lightly_active_minutes": summary.get("lightlyActiveMinutes"),
                "floors": summary.get("floors"),
                "calories_bmr": summary.get("caloriesBMR"),
            }
            distances = summary.get("distances", [])
            for d in distances:
                if d.get("activity") == "total":
                    data["activity"]["distance_km"] = _safe_float(d.get("distance"))
                    break
        except Exception as e:
            errors.append(f"activity: {str(e)}")
            logger.warning(f"Failed to fetch activity data: {e}")

        try:
            sleep_data = await self.get_sleep(date)
            if sleep_data.get("sleep"):
                from src.services.fitbit.stages import compute_stages_summary

                sleep_entries = []
                for s in sleep_data["sleep"]:
                    levels = s.get("levels", {}).get("summary", {})
                    levels_data = s.get("levels", {}).get("data", [])
                    sleep_entries.append({
                        "external_id": str(s.get("logId", "")),
                        "date_of_sleep": s.get("dateOfSleep"),
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
                    })
                data["sleep"] = sleep_entries
        except Exception as e:
            errors.append(f"sleep: {str(e)}")
            logger.warning(f"Failed to fetch sleep data: {e}")

        try:
            hr_data = await self.get_heart_rate(date)
            hr_value = hr_data.get("activities-heart", [{}])[0].get("value", {})
            data["heart_rate"] = {
                "resting_heart_rate": _safe_float(hr_value.get("restingHeartRate")),
                "zones": {
                    zone["name"]: {
                        "min": zone.get("min"),
                        "max": zone.get("max"),
                        "minutes": zone.get("minutes"),
                        "caloriesOut": zone.get("caloriesOut"),
                    }
                    for zone in hr_value.get("heartRateZones", [])
                },
            }
        except Exception as e:
            errors.append(f"heart_rate: {str(e)}")
            logger.warning(f"Failed to fetch heart rate data: {e}")

        # HRV, SpO2, Breathing Rate, VO2 Max, Temperature, AZM
        try:
            hrv_data = await self.get_hrv(date)
            if hrv_data.get("hrv") and len(hrv_data["hrv"]) > 0:
                hrv_entry = hrv_data["hrv"][0].get("value", {})
                data["hrv"] = {
                    "daily_rmssd": _safe_float(hrv_entry.get("dailyRmssd")),
                    "deep_rmssd": _safe_float(hrv_entry.get("deepRmssd")),
                }
        except Exception as e:
            errors.append(f"hrv: {str(e)}")
            logger.warning(f"Failed to fetch HRV data: {e}")

        try:
            spo2_data = await self.get_spo2(date)
            if spo2_data.get("value"):
                data["spo2"] = {
                    "avg": _safe_float(spo2_data["value"].get("avg")),
                    "min": _safe_float(spo2_data["value"].get("min")),
                    "max": _safe_float(spo2_data["value"].get("max")),
                }
        except Exception as e:
            errors.append(f"spo2: {str(e)}")
            logger.warning(f"Failed to fetch SpO2 data: {e}")

        try:
            br_data = await self.get_breathing_rate(date)
            if br_data.get("br") and len(br_data["br"]) > 0:
                br_value = br_data["br"][0].get("value", {})
                data["breathing_rate"] = {
                    "breathing_rate": _safe_float(br_value.get("breathingRate")),
                }
        except Exception as e:
            errors.append(f"breathing_rate: {str(e)}")
            logger.warning(f"Failed to fetch breathing rate data: {e}")

        try:
            vo2_data = await self.get_vo2_max(date)
            if vo2_data.get("cardioScore") and len(vo2_data["cardioScore"]) > 0:
                vo2_entry = vo2_data["cardioScore"][0].get("value", {})
                data["vo2_max"] = {
                    "vo2_max": _safe_float(vo2_entry.get("vo2Max")),
                }
        except Exception as e:
            errors.append(f"vo2_max: {str(e)}")
            logger.warning(f"Failed to fetch VO2 Max data: {e}")

        try:
            temp_data = await self.get_skin_temperature(date)
            if temp_data.get("tempSkin") and len(temp_data["tempSkin"]) > 0:
                temp_value = temp_data["tempSkin"][0].get("value", {})
                data["temperature"] = {
                    "relative_deviation": _safe_float(temp_value.get("nightlyRelative")),
                }
        except Exception as e:
            errors.append(f"temperature: {str(e)}")
            logger.warning(f"Failed to fetch temperature data: {e}")

        try:
            azm_data = await self.get_active_zone_minutes(date)
            if (
                azm_data.get("activities-active-zone-minutes")
                and len(azm_data["activities-active-zone-minutes"]) > 0
            ):
                azm_value = azm_data["activities-active-zone-minutes"][0].get(
                    "value", {}
                )
                data["active_zone_minutes"] = {
                    "fat_burn_minutes": azm_value.get("fatBurnActiveZoneMinutes", 0),
                    "cardio_minutes": azm_value.get("cardioActiveZoneMinutes", 0),
                    "peak_minutes": azm_value.get("peakActiveZoneMinutes", 0),
                    "total_minutes": (
                        azm_value.get("fatBurnActiveZoneMinutes", 0)
                        + azm_value.get("cardioActiveZoneMinutes", 0)
                        + azm_value.get("peakActiveZoneMinutes", 0)
                    ),
                }
        except Exception as e:
            errors.append(f"active_zone_minutes: {str(e)}")
            logger.warning(f"Failed to fetch Active Zone Minutes data: {e}")

        return {
            "data": data,
            "errors": errors,
            "date": date,
        }


class FitbitAPIError(Exception):
    """General Fitbit API error."""

    pass


class TokenExpiredError(FitbitAPIError):
    """Token has expired and needs refresh."""

    pass


class RateLimitError(FitbitAPIError):
    """Fitbit rate limit has been exceeded."""

    pass
