"""Tests for fitbit_sync — token management and metric upsert."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from src.models.db_models import FitnessMetric, User
from src.services.fitbit.sync import disconnect_fitbit, ensure_valid_token
from src.services.sync_utils import upsert_metric
from src.services.token_encryption import decrypt_token, encrypt_token

from tests.conftest import test_session_maker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_user(**overrides) -> User:
    """Create a User object with sensible defaults for testing."""
    defaults = {
        "id": uuid.uuid4(),
        "email": "test@example.com",
        "hashed_password": "hashed",
        "fitbit_access_token": encrypt_token("access-tok"),
        "fitbit_refresh_token": encrypt_token("refresh-tok"),
        "fitbit_token_expires": int(datetime.now(timezone.utc).timestamp()) + 7200,
        "fitbit_user_id": "fitbit-user-1",
    }
    defaults.update(overrides)
    user = User(**defaults)
    return user


# ---------------------------------------------------------------------------
# ensure_valid_token
# ---------------------------------------------------------------------------
class TestEnsureValidToken:
    @pytest.mark.asyncio
    async def test_no_refresh_when_token_is_valid(self):
        """When the token expires far in the future, no refresh should happen."""
        far_future = int(datetime.now(timezone.utc).timestamp()) + 7200
        user = _make_user(fitbit_token_expires=far_future)

        with patch("src.services.fitbit.sync.refresh_access_token", new_callable=AsyncMock) as mock_refresh:
            token = await ensure_valid_token(user)

        mock_refresh.assert_not_called()
        assert token == "access-tok"

    @pytest.mark.asyncio
    async def test_refresh_when_token_about_to_expire(self):
        """When token expires within 300s, should refresh."""
        almost_expired = int(datetime.now(timezone.utc).timestamp()) + 100
        user = _make_user(fitbit_token_expires=almost_expired)

        new_tokens = {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
        }

        with patch("src.services.fitbit.sync.refresh_access_token", new_callable=AsyncMock, return_value=new_tokens):
            token = await ensure_valid_token(user)

        assert token == "new-access"
        # User fields should be updated
        assert decrypt_token(user.fitbit_access_token) == "new-access"
        assert decrypt_token(user.fitbit_refresh_token) == "new-refresh"
        assert user.fitbit_token_expires is not None

    @pytest.mark.asyncio
    async def test_refresh_when_token_already_expired(self):
        """When token is already expired (past timestamp), should refresh."""
        past = int(datetime.now(timezone.utc).timestamp()) - 1000
        user = _make_user(fitbit_token_expires=past)

        new_tokens = {
            "access_token": "refreshed",
            "refresh_token": "refreshed-rt",
            "expires_in": 7200,
        }

        with patch("src.services.fitbit.sync.refresh_access_token", new_callable=AsyncMock, return_value=new_tokens):
            token = await ensure_valid_token(user)

        assert token == "refreshed"

    @pytest.mark.asyncio
    async def test_refresh_when_expires_is_none(self):
        """When fitbit_token_expires is None, the condition (None < X) is falsy, so no refresh."""
        user = _make_user(fitbit_token_expires=None)

        with patch("src.services.fitbit.sync.refresh_access_token", new_callable=AsyncMock) as mock_refresh:
            token = await ensure_valid_token(user)

        mock_refresh.assert_not_called()
        assert token == "access-tok"


# ---------------------------------------------------------------------------
# disconnect_fitbit
# ---------------------------------------------------------------------------
class TestDisconnectFitbit:
    def test_clears_all_fields(self):
        user = _make_user()
        assert user.fitbit_access_token is not None

        disconnect_fitbit(user)

        assert user.fitbit_access_token is None
        assert user.fitbit_refresh_token is None
        assert user.fitbit_token_expires is None

    def test_idempotent_on_already_disconnected(self):
        user = _make_user(
            fitbit_access_token=None,
            fitbit_refresh_token=None,
            fitbit_token_expires=None,
        )
        disconnect_fitbit(user)
        assert user.fitbit_access_token is None


# ---------------------------------------------------------------------------
# upsert_metric
# ---------------------------------------------------------------------------
class TestUpsertMetric:
    @pytest.mark.asyncio
    async def test_inserts_new_metric(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            # Create a User first so foreign key is satisfied
            user = User(id=user_id, email="u@test.com", hashed_password="h")
            session.add(user)
            await session.flush()

            metric_date = date(2026, 4, 7)
            await upsert_metric(
                session, user_id, metric_date, "weight", {"weight_kg": 80}, source="fitbit"
            )
            await session.commit()

            # Verify it was inserted
            stmt = select(FitnessMetric).where(
                FitnessMetric.user_id == user_id,
                FitnessMetric.metric_type == "weight",
            )
            result = (await session.execute(stmt)).scalar_one()
            assert result.data == {"weight_kg": 80}
            assert result.source == "fitbit"
            assert result.date == metric_date

    @pytest.mark.asyncio
    async def test_updates_existing_metric(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            user = User(id=user_id, email="u2@test.com", hashed_password="h")
            session.add(user)
            await session.flush()

            metric_date = date(2026, 4, 7)

            # Insert first
            await upsert_metric(
                session, user_id, metric_date, "activity", {"steps": 5000}, source="fitbit"
            )
            await session.commit()

            # Update
            await upsert_metric(
                session, user_id, metric_date, "activity", {"steps": 10000}, source="fitbit"
            )
            await session.commit()

            stmt = select(FitnessMetric).where(
                FitnessMetric.user_id == user_id,
                FitnessMetric.metric_type == "activity",
            )
            result = (await session.execute(stmt)).scalar_one()
            assert result.data == {"steps": 10000}

    @pytest.mark.asyncio
    async def test_different_sources_not_conflated(self):
        """Metrics from different sources (fitbit vs renpho) are separate rows."""
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            user = User(id=user_id, email="u3@test.com", hashed_password="h")
            session.add(user)
            await session.flush()

            metric_date = date(2026, 4, 7)

            await upsert_metric(
                session, user_id, metric_date, "weight", {"weight_kg": 80}, source="fitbit"
            )
            await upsert_metric(
                session, user_id, metric_date, "weight", {"weight_kg": 81}, source="renpho"
            )
            await session.commit()

            stmt = select(FitnessMetric).where(
                FitnessMetric.user_id == user_id,
                FitnessMetric.metric_type == "weight",
            )
            results = (await session.execute(stmt)).scalars().all()
            assert len(results) == 2
            sources = {r.source for r in results}
            assert sources == {"fitbit", "renpho"}
