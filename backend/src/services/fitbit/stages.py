"""Compute sleep stages 30s summary from Fitbit levels.data[]."""

from collections import defaultdict


def compute_stages_summary(levels_data: list[dict]) -> dict:
    """Summarize 30-second sleep stage data into analytics-ready metrics.

    Args:
        levels_data: list of {dateTime, level, seconds} from Fitbit sleep API

    Returns:
        {transition_count, avg_stage_duration_minutes, longest_uninterrupted_deep_minutes,
         longest_uninterrupted_rem_minutes}
    """
    if not levels_data:
        return {
            "transition_count": 0,
            "avg_stage_duration_minutes": {},
            "longest_uninterrupted_deep_minutes": 0,
            "longest_uninterrupted_rem_minutes": 0,
        }

    stage_durations: dict[str, list[float]] = defaultdict(list)
    longest_deep_s = 0
    longest_rem_s = 0

    for entry in levels_data:
        stage = entry.get("level", "unknown")
        seconds = entry.get("seconds", 0)
        stage_durations[stage].append(seconds)

        if stage == "deep" and seconds > longest_deep_s:
            longest_deep_s = seconds
        if stage == "rem" and seconds > longest_rem_s:
            longest_rem_s = seconds

    avg_durations = {}
    for stage, durations in stage_durations.items():
        avg_durations[stage] = round(sum(durations) / len(durations) / 60, 1)

    return {
        "transition_count": len(levels_data),
        "avg_stage_duration_minutes": avg_durations,
        "longest_uninterrupted_deep_minutes": round(longest_deep_s / 60, 1),
        "longest_uninterrupted_rem_minutes": round(longest_rem_s / 60, 1),
    }
