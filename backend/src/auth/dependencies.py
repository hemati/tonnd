"""Dual authentication: JWT (fastapi-users) or Personal Access Token."""

import logging
import uuid

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.scopes import has_scope
from src.database import get_async_session
from src.models.api_models import APIToken
from src.models.db_models import User
from src.services.token_service import TOKEN_PREFIX, verify_token
from src.services.user_service import JWT_SECRET

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


class AuthResult:
    """Carries the authenticated user and optional API token."""

    __slots__ = ("user", "token")

    def __init__(self, user: User, token: APIToken | None = None):
        self.user = user
        self.token = token


async def get_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> AuthResult:
    """Authenticate via JWT or PAT. Returns AuthResult with user + optional token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    raw = credentials.credentials

    # PAT path
    if raw.startswith(TOKEN_PREFIX):
        api_token = await verify_token(session, raw)
        if not api_token:
            raise HTTPException(status_code=401, detail="Invalid, expired, or revoked token")

        user = (
            await session.execute(select(User).where(User.id == api_token.user_id))
        ).unique().scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User inactive")

        request.state.audit_user_id = user.id
        request.state.audit_token_id = api_token.id

        return AuthResult(user=user, token=api_token)

    # JWT path — decode with PyJWT directly, extract user_id from "sub" claim
    try:
        payload = jwt.decode(
            raw, JWT_SECRET, algorithms=["HS256"],
            audience=["fastapi-users:auth"],
        )
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired JWT")

    user = (
        await session.execute(select(User).where(User.id == user_id))
    ).unique().scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive")

    request.state.audit_user_id = user.id
    request.state.audit_token_id = None

    return AuthResult(user=user)


def require_scope(scope: str):
    """Dependency factory that enforces a specific scope on PAT-authenticated requests.

    JWT-authenticated users (no token) get full access — they are the user themselves.
    """

    async def _check(auth: AuthResult = Depends(get_auth)) -> AuthResult:
        if auth.token is not None:
            if not has_scope(auth.token.scopes, scope):
                raise HTTPException(
                    status_code=403,
                    detail=f"Token missing required scope: {scope}",
                )
        return auth

    return _check
