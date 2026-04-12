"""Fitbit user profile + device info parsing."""


def parse_profile(api_response: dict) -> dict:
    """Parse GET /1/user/-/profile.json into user_context fields."""
    user = api_response.get("user", {})
    return {
        "date_of_birth": user.get("dateOfBirth"),
        "gender": user.get("gender"),
        "height_cm": user.get("height"),
        "timezone": user.get("timezone"),
        "utc_offset_ms": user.get("offsetFromUTCMillis"),
        "stride_length_walking": user.get("strideLengthWalking"),
        "stride_length_running": user.get("strideLengthRunning"),
    }


def parse_devices(api_response: list) -> dict:
    """Parse GET /1/user/-/devices.json — pick most recently synced device."""
    if not api_response:
        return {}

    most_recent = max(api_response, key=lambda d: d.get("lastSyncTime", ""))
    return {
        "device_model": most_recent.get("deviceVersion"),
        "device_battery": most_recent.get("batteryLevel"),
        "last_device_sync": most_recent.get("lastSyncTime"),
    }
