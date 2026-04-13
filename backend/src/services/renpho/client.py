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
    """Fetch all Renpho measurements for a specific date.

    Returns: {"data": [measurement_dict, ...], "errors": []}
    """
    result: dict = {"data": [], "errors": []}

    try:
        client = RenphoClient(email, password)
        measurements = client.get_all_measurements()

        for m in measurements:
            ts = m.get("timeStamp") or m.get("time_stamp")
            if not ts:
                continue

            measured_at = datetime.fromtimestamp(ts, tz=timezone.utc)
            m_date = measured_at.date()
            if m_date != target_date:
                continue

            weight = m.get("weight")
            if not weight or weight <= 0:
                continue

            result["data"].append({
                "date": m_date,
                "measured_at": measured_at,
                "weight_kg": weight,
                "bmi": m.get("bmi"),
                "body_fat_percent": m.get("bodyfat"),
                "body_water_percent": m.get("water"),
                "muscle_mass_percent": m.get("muscle"),
                "bone_mass_kg": m.get("bone"),
                "bmr_kcal": int(m["bmr"]) if m.get("bmr") else None,
                "visceral_fat": m.get("visfat"),
                "subcutaneous_fat_percent": m.get("subfat"),
                "protein_percent": m.get("protein"),
                "body_age": int(m["bodyage"]) if m.get("bodyage") else None,
                "lean_body_mass_kg": m.get("sinew"),
                "fat_free_weight_kg": m.get("fatFreeWeight"),
                "heart_rate": int(m["heartRate"]) if m.get("heartRate") else None,
                "cardiac_index": m.get("cardiacIndex"),
                "body_shape": int(m["bodyShape"]) if m.get("bodyShape") else None,
                "sport_flag": bool(m.get("sport_flag")) if m.get("sport_flag") is not None else None,
            })

    except Exception as e:
        result["errors"].append(f"renpho: {e}")
        logger.error(f"Renpho fetch failed: {e}")

    return result
