"""Status record for the Fitbit historical backfill background job."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.db_models import Base
from src.models.fitbit_models import _iso


class BackfillJob(Base):
    __tablename__ = "fitbit_backfill_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    # pending | running | paused_rate_limited | done | failed
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    # ranges | intraday
    phase: Mapped[str] = mapped_column(String(16), nullable=False, default="ranges")
    days_requested: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    anchor_date: Mapped[date | None] = mapped_column(Date, default=None)
    days_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ranges_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    next_resume_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    last_error: Mapped[str | None] = mapped_column(Text, default=None)

    __table_args__ = (Index("ix_fitbit_backfill_jobs_user", "user_id"),)

    ACTIVE_STATES = ("pending", "running", "paused_rate_limited")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "state": self.state,
            "phase": self.phase,
            "days_requested": self.days_requested,
            "anchor_date": _iso(self.anchor_date),
            "days_done": self.days_done,
            "ranges_done": self.ranges_done,
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at),
            "next_resume_at": _iso(self.next_resume_at),
            "last_error": self.last_error,
        }
