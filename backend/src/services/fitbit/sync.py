"""Fitbit-specific sync helpers — token refresh and disconnect."""

from datetime import datetime, timezone

from src.models.db_models import User
from src.services.fitbit.client import refresh_access_token
from src.services.token_encryption import decrypt_token, encrypt_token


async def ensure_valid_token(user: User) -> str:
    """Return a valid access token, refreshing if needed. Mutates user in-place."""
    access_token = decrypt_token(user.fitbit_access_token)

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if user.fitbit_token_expires and user.fitbit_token_expires < now_ts + 300:
        refresh_tok = decrypt_token(user.fitbit_refresh_token)
        new_tokens = await refresh_access_token(refresh_tok)
        access_token = new_tokens["access_token"]
        user.fitbit_access_token = encrypt_token(new_tokens["access_token"])
        user.fitbit_refresh_token = encrypt_token(new_tokens["refresh_token"])
        user.fitbit_token_expires = now_ts + new_tokens.get("expires_in", 3600)

    return access_token


def disconnect_fitbit(user: User) -> None:
    """Clear all Fitbit tokens from user."""
    user.fitbit_access_token = None
    user.fitbit_refresh_token = None
    user.fitbit_token_expires = None
