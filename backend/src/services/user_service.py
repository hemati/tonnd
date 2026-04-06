import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, schemas
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from httpx_oauth.clients.google import GoogleOAuth2
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.models.db_models import OAuthAccount, User

logger = logging.getLogger(__name__)

# --- Secrets ---

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is required."
    )

RESET_PASSWORD_TOKEN_SECRET = os.environ.get("RESET_PASSWORD_TOKEN_SECRET")
if not RESET_PASSWORD_TOKEN_SECRET:
    raise RuntimeError("RESET_PASSWORD_TOKEN_SECRET environment variable is required.")

VERIFICATION_TOKEN_SECRET = os.environ.get("VERIFICATION_TOKEN_SECRET")
if not VERIFICATION_TOKEN_SECRET:
    raise RuntimeError("VERIFICATION_TOKEN_SECRET environment variable is required.")

# --- Google OAuth (optional — works without for email/password login) ---

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

google_oauth_client = (
    GoogleOAuth2(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) if GOOGLE_CLIENT_ID else None
)


# --- Schemas ---


class UserRead(schemas.BaseUser[uuid.UUID]):
    fitbit_user_id: Optional[str] = None
    last_sync: Optional[datetime] = None


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


# --- User DB adapter ---


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


# --- User Manager ---


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = VERIFICATION_TOKEN_SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.info("User %s registered.", user.id)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info("Password reset requested for user %s.", user.id)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


# --- Auth Backend (JWT) ---

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=JWT_SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# --- FastAPIUsers instance ---

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
