"""In-memory store for FatSecret OAuth1 request-token state.

OAuth1 3-legged needs to round-trip the (request_token, request_token_secret)
pair across the user's browser redirect to FatSecret and back. FatSecret
echoes the oauth_token in the callback query string but NOT the secret, so
we keep the secret server-side keyed by oauth_token.

Single-process assumption: TONND runs uvicorn with one worker (see AGENTS.md
"Production constraints"). A process-local dict is sufficient. Multi-worker
would silently break the OAuth handshake; the worker-count guard in app.py
warns at startup if WEB_CONCURRENCY > 1.
"""

import uuid
from datetime import datetime, timedelta, timezone

TTL = timedelta(minutes=10)

# Sanity bound on FatSecret-supplied oauth_token length. Rejects giant strings
# that could bloat the in-memory store. FatSecret tokens are ~20-40 chars in
# practice; 256 leaves generous headroom without enabling abuse.
MAX_TOKEN_LEN = 256

# Per-user limit on outstanding (un-completed) handshakes. A logged-in user
# spamming Connect could otherwise accumulate one entry per fresh
# request_token FatSecret issues, until TTL.
MAX_INFLIGHT_PER_USER = 5

# oauth_token -> (user_id, request_token_secret, expires_at)
_STORE: dict[str, tuple[uuid.UUID, str, datetime]] = {}


class TokenTooLongError(ValueError):
    """Raised when a put receives an unreasonably long oauth_token."""


class TooManyInFlightError(RuntimeError):
    """Raised when a user has too many outstanding OAuth handshakes."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _drop_expired() -> None:
    """Sweep entries whose TTL has elapsed. Called inline by put/pop_if_valid."""
    now = _now()
    # Materialize keys before deleting so we don't mutate during iteration.
    expired = [k for k, (_, _, exp) in _STORE.items() if exp <= now]
    for k in expired:
        del _STORE[k]


def put(oauth_token: str, user_id: uuid.UUID, request_token_secret: str) -> None:
    """Stash the request_token_secret for `oauth_token`. Overwrites on collision."""
    if len(oauth_token) > MAX_TOKEN_LEN or len(request_token_secret) > MAX_TOKEN_LEN:
        raise TokenTooLongError(f"oauth token exceeds {MAX_TOKEN_LEN} chars")
    _drop_expired()
    in_flight = sum(1 for uid, _, _ in _STORE.values() if uid == user_id)
    if in_flight >= MAX_INFLIGHT_PER_USER and oauth_token not in _STORE:
        raise TooManyInFlightError(
            f"user has {in_flight} unfinished OAuth flows; "
            f"max {MAX_INFLIGHT_PER_USER}"
        )
    _STORE[oauth_token] = (user_id, request_token_secret, _now() + TTL)


def pop_if_valid(oauth_token: str) -> tuple[uuid.UUID, str] | None:
    """Return (user_id, request_token_secret) if present and not expired, else None.

    Always removes the entry on hit (single-use semantics).
    """
    _drop_expired()
    entry = _STORE.pop(oauth_token, None)
    if entry is None:
        return None
    user_id, secret, exp = entry
    if exp <= _now():
        return None
    return user_id, secret


def _clear_for_tests() -> None:
    """Reset the store. Intended for test isolation only."""
    _STORE.clear()
