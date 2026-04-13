from datetime import datetime, timezone

from fastapi_users.db import (
    SQLAlchemyBaseOAuthAccountTableUUID,
    SQLAlchemyBaseUserTableUUID,
)
from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    """Stores Google OAuth account links."""

    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model — extends fastapi-users base with Fitbit fields."""

    # Google OAuth accounts
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship("OAuthAccount", lazy="joined")

    # Fitbit OAuth
    fitbit_user_id: Mapped[str | None] = mapped_column(String(64), default=None)
    fitbit_access_token: Mapped[str | None] = mapped_column(Text, default=None)
    fitbit_refresh_token: Mapped[str | None] = mapped_column(Text, default=None)
    fitbit_token_expires: Mapped[int | None] = mapped_column(default=None)

    # Renpho (reverse-engineered cloud API)
    renpho_email: Mapped[str | None] = mapped_column(Text, default=None)
    renpho_session_key: Mapped[str | None] = mapped_column(Text, default=None)

    # Hevy (workout tracking — user provides their own API key)
    hevy_api_key: Mapped[str | None] = mapped_column(Text, default=None)  # Fernet-encrypted

    # Fitbit capability flags
    fitbit_intraday_available: Mapped[bool | None] = mapped_column(Boolean, default=None)
    fitbit_scopes_version: Mapped[int | None] = mapped_column(Integer, default=1)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # Relationships
    api_tokens: Mapped[list["APIToken"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )


