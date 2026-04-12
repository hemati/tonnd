"""Fitbit intraday data fetching and hourly aggregation."""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def aggregate_to_hourly(
    datapoints: list[dict],
    value_key: str = "value",
    use_sum: bool = False,
) -> dict[int, dict]:
    """Aggregate minute-level data to hourly summaries.

    Args:
        datapoints: list of {time: "HH:MM:SS", <value_key>: float}
        value_key: key containing the numeric value
        use_sum: if True, avg = sum of values (for steps/calories); else avg = mean

    Returns:
        {hour: {avg, min, max, sample_count}}
    """
    if not datapoints:
        return {}

    buckets: dict[int, list[float]] = defaultdict(list)

    for dp in datapoints:
        time_str = dp.get("time", "")
        value = dp.get(value_key)
        if value is None or not time_str:
            continue
        try:
            hour = int(time_str.split(":")[0])
        except (ValueError, IndexError):
            continue
        buckets[hour].append(float(value))

    result = {}
    for hour, values in sorted(buckets.items()):
        result[hour] = {
            "avg": round(sum(values) if use_sum else sum(values) / len(values), 1),
            "min": min(values),
            "max": max(values),
            "sample_count": len(values),
        }
    return result


# Intraday endpoint definitions — used by sync pipeline
INTRADAY_ENDPOINTS = {
    "heart_rate": {
        "url": "/1/user/-/activities/heart/date/{date}/1d/1min.json",
        "response_key": "activities-heart-intraday",
        "dataset_key": "dataset",
        "value_key": "value",
        "use_sum": False,
    },
    "steps": {
        "url": "/1/user/-/activities/steps/date/{date}/1d/1min.json",
        "response_key": "activities-steps-intraday",
        "dataset_key": "dataset",
        "value_key": "value",
        "use_sum": True,
    },
    "azm": {
        "url": "/1/user/-/activities/active-zone-minutes/date/{date}/1d/1min.json",
        "response_key": "activities-active-zone-minutes-intraday",
        "dataset_key": "dataset",
        "value_key": "value",
        "use_sum": True,
    },
}
