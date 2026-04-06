"""
Renpho smart scale client.

Uses the renpho-api PyPI package (reverse-engineered Renpho cloud API).
Caveats:
  - Logging in via API logs user out of the Renpho mobile app.
  - API is not official and can break without notice.
  - Body composition (fat %, muscle %, etc.) comes from the server, not BLE.
"""

import logging
from datetime import date, datetime, timezone

from renpho import RenphoClient

logger = logging.getLogger(__name__)


class RenphoAPIError(Exception):
    pass


class SessionExpiredError(RenphoAPIError):
    pass


def renpho_login(email: str, password: str) -> dict:
    """
    Login to Renpho and return session info.

    Returns:
        {"session_key": str, "user_id": str}

    Raises:
        RenphoAPIError on login failure.
    """
    try:
        client = RenphoClient(email, password)
        result = client.login()
        return {
            "session_key": client.token,
            "user_id": str(client.user_id),
        }
    except Exception as e:
        raise RenphoAPIError(f"Renpho login failed: {e}")


def get_measurements_for_date(email: str, password: str, target_date: date) -> dict:
    """
    Fetch Renpho measurements for a specific date.

    Returns:
        {
            "weight": {"weight_kg": ..., "bmi": ..., "body_fat_percent": ..., ...},
            "body_composition": {"body_fat_percent": ..., "muscle_mass_percent": ..., ...},
            "errors": [],
        }
    """
    result = {"data": {}, "errors": []}

    try:
        client = RenphoClient(email, password)
        measurements = client.get_all_measurements()

        for m in measurements:
            ts = m.get("timeStamp") or m.get("time_stamp")
            if not ts:
                continue

            m_date = datetime.fromtimestamp(ts, tz=timezone.utc).date()
            if m_date != target_date:
                continue

            weight = m.get("weight")
            if weight and weight > 0:
                result["data"]["weight"] = {
                    "weight_kg": weight,
                    "bmi": m.get("bmi"),
                    "body_fat_percent": m.get("bodyfat"),
                }

            result["data"]["body_composition"] = {
                "body_fat_percent": m.get("bodyfat"),
                "body_water_percent": m.get("water"),
                "muscle_mass_percent": m.get("muscle"),
                "bone_mass_kg": m.get("bone"),
                "bmr_kcal": m.get("bmr"),
                "visceral_fat": m.get("visfat"),
                "subcutaneous_fat_percent": m.get("subfat"),
                "protein_percent": m.get("protein"),
                "body_age": m.get("bodyage"),
                "lean_body_mass_kg": m.get("sinew"),
                "fat_free_weight_kg": m.get("fatFreeWeight"),
                "heart_rate": m.get("heartRate"),
            }
            break  # one measurement per date

    except Exception as e:
        result["errors"].append(f"renpho: {e}")
        logger.error(f"Renpho fetch failed: {e}")

    return result
