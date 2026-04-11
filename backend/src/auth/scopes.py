"""API scope definitions for TONND public API."""

# Metric types that belong to each scope
SCOPE_METRICS: dict[str, list[str]] = {
    "read:vitals": [
        "heart_rate",
        "hrv",
        "spo2",
        "breathing_rate",
        "vo2_max",
        "temperature",
    ],
    "read:body": ["weight", "body_composition"],
    "read:sleep": ["sleep"],
    "read:activity": ["activity", "active_zone_minutes"],
    "read:workouts": ["workout"],
    "read:recovery": [],  # computed, not a metric_type
}

ALL_SCOPES = list(SCOPE_METRICS.keys())

# read:all expands to all individual scopes
SCOPE_EXPANSION = {"read:all": ALL_SCOPES}


def expand_scopes(scopes: list[str]) -> set[str]:
    """Expand shorthand scopes (read:all) into individual scopes."""
    result: set[str] = set()
    for s in scopes:
        if s in SCOPE_EXPANSION:
            result.update(SCOPE_EXPANSION[s])
        else:
            result.add(s)
    return result


def has_scope(token_scopes: list[str], required: str) -> bool:
    """Check if a token's scopes include the required scope."""
    expanded = expand_scopes(token_scopes)
    return required in expanded


def metric_types_for_scopes(scopes: list[str]) -> set[str]:
    """Return the set of metric_types a token is allowed to access."""
    expanded = expand_scopes(scopes)
    types: set[str] = set()
    for scope in expanded:
        types.update(SCOPE_METRICS.get(scope, []))
    return types
