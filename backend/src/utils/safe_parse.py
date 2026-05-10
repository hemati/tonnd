"""Defensive parsing helpers for external API payloads."""


def _safe_float(val) -> float | None:
    """Coerce a value to float. Returns None on None/empty-string/parse-failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    """Coerce a value to int. Returns None on None/empty-string/parse-failure."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None
