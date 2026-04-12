import uuid
from datetime import date, datetime, timezone

from fastapi_users.db import (
    SQLAlchemyBaseOAuthAccountTableUUID,
    SQLAlchemyBaseUserTableUUID,
)
from sqlalchemy import (
    Boolean,
    Integer,
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
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
    fitness_metrics: Mapped[list["FitnessMetric"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    api_tokens: Mapped[list["APIToken"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )


class FitnessMetric(Base):
    """Fitness data — one row per user/date/metric_type combination."""

    __tablename__ = "fitness_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    metric_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="fitbit")
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="fitness_metrics")

    __table_args__ = (
        UniqueConstraint("user_id", "date", "metric_type", "source", name="uq_user_date_metric_source"),
        Index("ix_user_date", "user_id", "date"),
        Index("ix_user_metric_date", "user_id", "metric_type", "date"),
    )
