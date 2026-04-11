"""Rate limiting configuration for the TONND API."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.services.token_service import TOKEN_PREFIX

_PREFIX_LEN = len("Bearer ") + len(TOKEN_PREFIX)


def _get_key(request) -> str:
    """Rate limit key: token prefix for PATs, IP for others."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith(f"Bearer {TOKEN_PREFIX}"):
        return f"pat:{auth[7:7 + _PREFIX_LEN]}"
    elif auth.startswith("Bearer "):
        return f"jwt:{get_remote_address(request)}"
    return get_remote_address(request)


limiter = Limiter(key_func=_get_key)
