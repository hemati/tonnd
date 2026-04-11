"""Personal Access Token (PAT) service — generate, hash, validate, revoke."""

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.scopes import ALL_SCOPES, expand_scopes
from src.models.api_models import APIToken

TOKEN_PREFIX = "tonnd_"
TOKEN_BYTES = 32  # 256 bits of entropy
MAX_TOKENS_PER_USER = 25


def generate_raw_token() -> str:
    """Generate a new raw PAT. This value is shown to the user once."""
    return TOKEN_PREFIX + secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(raw_token: str) -> str:
    """SHA-256 hash of the raw token for storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def token_display_prefix(raw_token: str) -> str:
    """First 12 characters for identification (tonnd_XXXX)."""
    return raw_token[:12]


def validate_scopes(scopes: list[str]) -> list[str]:
    """Validate that all scopes are recognized. Returns cleaned list."""
    valid = set(ALL_SCOPES) | {"read:all"}
    invalid = [s for s in scopes if s not in valid]
    if invalid:
        raise ValueError(f"Invalid scopes: {', '.join(invalid)}")
    return sorted(set(scopes))


async def create_token(
    session: AsyncSession,
    user_id,
    name: str,
    scopes: list[str],
    expires_at: datetime | None = None,
) -> tuple[APIToken, str]:
    """Create a new PAT. Returns (db_record, raw_token).

    The raw_token is only available at creation time.
    """
    # Enforce per-user token limit to prevent DoS
    count_stmt = select(APIToken).where(
        APIToken.user_id == user_id,
        APIToken.is_active == True,  # noqa: E712
    )
    active_count = len((await session.execute(count_stmt)).scalars().all())
    if active_count >= MAX_TOKENS_PER_USER:
        raise ValueError(f"Maximum of {MAX_TOKENS_PER_USER} active tokens per user")

    cleaned_scopes = validate_scopes(scopes)
    raw_token = generate_raw_token()

    token = APIToken(
        user_id=user_id,
        name=name,
        token_hash=hash_token(raw_token),
        token_prefix=token_display_prefix(raw_token),
        scopes=cleaned_scopes,
        expires_at=expires_at,
    )
    session.add(token)
    await session.flush()
    return token, raw_token


async def verify_token(session: AsyncSession, raw_token: str) -> APIToken | None:
    """Look up and validate a raw PAT. Returns the token record or None."""
    if not raw_token.startswith(TOKEN_PREFIX):
        return None

    token_h = hash_token(raw_token)
    stmt = select(APIToken).where(
        APIToken.token_hash == token_h,
        APIToken.is_active == True,  # noqa: E712
        APIToken.revoked_at == None,  # noqa: E711
    )
    token = (await session.execute(stmt)).scalar_one_or_none()
    if not token:
        return None

    if token.expires_at and token.expires_at < datetime.now(timezone.utc):
        return None

    # Update last_used_at
    token.last_used_at = datetime.now(timezone.utc)
    return token


async def revoke_token(session: AsyncSession, token_id, user_id) -> bool:
    """Revoke a token. Returns True if found and revoked."""
    stmt = select(APIToken).where(
        APIToken.id == token_id,
        APIToken.user_id == user_id,
        APIToken.is_active == True,  # noqa: E712
    )
    token = (await session.execute(stmt)).scalar_one_or_none()
    if not token:
        return False

    token.is_active = False
    token.revoked_at = datetime.now(timezone.utc)
    return True


async def list_user_tokens(session: AsyncSession, user_id) -> list[APIToken]:
    """List all tokens for a user (active and revoked)."""
    stmt = (
        select(APIToken)
        .where(APIToken.user_id == user_id)
        .order_by(APIToken.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
