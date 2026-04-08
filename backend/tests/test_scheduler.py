"""Tests for scheduler — sync_user and daily_sync_all."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from src.models.db_models import User
from src.services.fitbit_client import RateLimitError, TokenExpiredError
from src.services.token_encryption import encrypt_token

from tests.conftest import test_session_maker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_user(**overrides) -> User:
    defaults = {
        "id": uuid.uuid4(),
        "email": "sched@test.com",
        "hashed_password": "hashed",
    }
    defaults.update(overrides)
    return User(**defaults)


def _fitbit_token_fields(**overrides) -> dict:
    """Return the standard fields for a Fitbit-connected user."""
    return {
        "fitbit_access_token": encrypt_token("at"),
        "fitbit_refresh_token": encrypt_token("rt"),
        "fitbit_token_expires": int(datetime.now(timezone.utc).timestamp()) + 7200,
        **overrides,
    }


# ---------------------------------------------------------------------------
# sync_user
# ---------------------------------------------------------------------------
class TestSyncUser:
    @pytest.mark.asyncio
    async def test_fitbit_connected_success(self):
        """User with Fitbit token gets synced successfully."""
        from src.scheduler import sync_user

        async with test_session_maker() as session:
            user = _make_user(**_fitbit_token_fields())
            session.add(user)
            await session.flush()

            mock_result = {
                "data": {"activity": {"steps": 10000}},
                "errors": [],
            }

            with patch(
                "src.scheduler.ensure_valid_token",
                new_callable=AsyncMock,
                return_value="valid-token",
            ), patch(
                "src.scheduler.FitbitClient"
            ) as MockClient:
                mock_instance = AsyncMock()
                mock_instance.get_all_data_for_date.return_value = mock_result
                MockClient.return_value = mock_instance

                status = await sync_user(session, user)

            assert status == "success"
            assert user.last_sync is not None
            # get_all_data_for_date called twice (yesterday + today)
            assert mock_instance.get_all_data_for_date.call_count == 2

    @pytest.mark.asyncio
    async def test_fitbit_token_expired(self):
        """TokenExpiredError disconnects Fitbit and returns 'token_expired'."""
        from src.scheduler import sync_user

        async with test_session_maker() as session:
            user = _make_user(**_fitbit_token_fields())
            session.add(user)
            await session.flush()

            with patch(
                "src.scheduler.ensure_valid_token",
                new_callable=AsyncMock,
                side_effect=TokenExpiredError("expired"),
            ), patch("src.scheduler.disconnect_fitbit") as mock_disconnect:
                status = await sync_user(session, user)

            assert status == "token_expired"
            mock_disconnect.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_fitbit_rate_limited(self):
        """RateLimitError returns 'rate_limited' status."""
        from src.scheduler import sync_user

        async with test_session_maker() as session:
            user = _make_user(**_fitbit_token_fields())
            session.add(user)
            await session.flush()

            with patch(
                "src.scheduler.ensure_valid_token",
                new_callable=AsyncMock,
                side_effect=RateLimitError("rate limit hit"),
            ):
                status = await sync_user(session, user)

            assert status == "rate_limited"

    @pytest.mark.asyncio
    async def test_fitbit_generic_failure(self):
        """Generic exception returns 'failed' status."""
        from src.scheduler import sync_user

        async with test_session_maker() as session:
            user = _make_user(**_fitbit_token_fields())
            session.add(user)
            await session.flush()

            with patch(
                "src.scheduler.ensure_valid_token",
                new_callable=AsyncMock,
                side_effect=RuntimeError("network down"),
            ):
                status = await sync_user(session, user)

            assert status == "failed"

    @pytest.mark.asyncio
    async def test_renpho_connected(self):
        """User with renpho_session_key gets Renpho synced."""
        from src.scheduler import sync_user

        async with test_session_maker() as session:
            user = _make_user(
                renpho_email=encrypt_token("r@test.com"),
                renpho_session_key=encrypt_token("renpho-pw"),
            )
            session.add(user)
            await session.flush()

            with patch(
                "src.scheduler.sync_renpho_data",
                new_callable=AsyncMock,
                return_value={"synced_metrics": [], "errors": []},
            ) as mock_renpho:
                status = await sync_user(session, user)

            assert status == "success"
            # Called twice: yesterday + today
            assert mock_renpho.call_count == 2

    @pytest.mark.asyncio
    async def test_renpho_with_errors_logged(self):
        """Renpho errors are logged but don't change status."""
        from src.scheduler import sync_user

        async with test_session_maker() as session:
            user = _make_user(
                renpho_email=encrypt_token("r@test.com"),
                renpho_session_key=encrypt_token("renpho-pw"),
            )
            session.add(user)
            await session.flush()

            with patch(
                "src.scheduler.sync_renpho_data",
                new_callable=AsyncMock,
                return_value={"synced_metrics": [], "errors": ["renpho: auth fail"]},
            ):
                status = await sync_user(session, user)

            # status is still success since renpho errors don't override it
            assert status == "success"

    @pytest.mark.asyncio
    async def test_both_connected(self):
        """User with both Fitbit and Renpho gets both synced."""
        from src.scheduler import sync_user

        async with test_session_maker() as session:
            user = _make_user(
                **_fitbit_token_fields(),
                renpho_email=encrypt_token("r@test.com"),
                renpho_session_key=encrypt_token("renpho-pw"),
            )
            session.add(user)
            await session.flush()

            mock_fitbit_result = {
                "data": {"activity": {"steps": 8000}},
                "errors": [],
            }

            with patch(
                "src.scheduler.ensure_valid_token",
                new_callable=AsyncMock,
                return_value="tok",
            ), patch("src.scheduler.FitbitClient") as MockClient, patch(
                "src.scheduler.sync_renpho_data",
                new_callable=AsyncMock,
                return_value={"synced_metrics": ["weight"], "errors": []},
            ) as mock_renpho:
                mock_instance = AsyncMock()
                mock_instance.get_all_data_for_date.return_value = mock_fitbit_result
                MockClient.return_value = mock_instance

                status = await sync_user(session, user)

            assert status == "success"
            assert mock_instance.get_all_data_for_date.call_count == 2
            assert mock_renpho.call_count == 2

    @pytest.mark.asyncio
    async def test_nothing_connected(self):
        """User with no data sources still returns success."""
        from src.scheduler import sync_user

        async with test_session_maker() as session:
            user = _make_user()
            session.add(user)
            await session.flush()

            status = await sync_user(session, user)

            assert status == "success"
            assert user.last_sync is not None


# ---------------------------------------------------------------------------
# daily_sync_all  (mock the entire function to avoid SQLAlchemy .unique()
# issue with joined eager loads on SQLite test DB)
# ---------------------------------------------------------------------------

def _mock_session_maker_factory(users_to_return):
    """
    Build a mock async_session_maker whose first usage returns users_to_return
    from the query, and subsequent usages provide a session with a working
    `get` that maps user.id -> user, and `commit` that is a no-op.
    """
    call_count = 0
    user_map = {u.id: u for u in users_to_return}

    class _FakeSession:
        """Minimal async session stand-in."""

        async def execute(self, stmt):
            # Return a result-like object with .scalars().all()
            class _Scalars:
                def all(self_inner):
                    return list(users_to_return)
                def unique(self_inner):
                    return self_inner
            class _Result:
                def scalars(self_inner):
                    return _Scalars()
            return _Result()

        async def get(self, model_cls, user_id):
            return user_map.get(user_id)

        async def commit(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    def factory(**kwargs):
        nonlocal call_count
        call_count += 1
        return _FakeSession()

    return factory


class TestDailySyncAll:
    @pytest.mark.asyncio
    async def test_mixed_users(self):
        """daily_sync_all processes multiple users and returns stats."""
        from src.scheduler import daily_sync_all

        user1 = _make_user(**_fitbit_token_fields())
        user2 = _make_user(
            email="u2@test.com",
            renpho_email=encrypt_token("r@test.com"),
            renpho_session_key=encrypt_token("rpw"),
        )

        mock_maker = _mock_session_maker_factory([user1, user2])

        with patch(
            "src.scheduler.async_session_maker", mock_maker
        ), patch(
            "src.scheduler.sync_user",
            new_callable=AsyncMock,
            return_value="success",
        ) as mock_sync, patch("asyncio.sleep", new_callable=AsyncMock):
            stats = await daily_sync_all()

        assert stats["success"] == 2
        assert stats["failed"] == 0
        assert mock_sync.call_count == 2

    @pytest.mark.asyncio
    async def test_rate_limited_stops_batch(self):
        """When a user is rate-limited, the batch stops immediately."""
        from src.scheduler import daily_sync_all

        user1 = _make_user(**_fitbit_token_fields())
        user2 = _make_user(email="u2@test.com", **_fitbit_token_fields())

        mock_maker = _mock_session_maker_factory([user1, user2])

        with patch(
            "src.scheduler.async_session_maker", mock_maker
        ), patch(
            "src.scheduler.sync_user",
            new_callable=AsyncMock,
            return_value="rate_limited",
        ) as mock_sync, patch("asyncio.sleep", new_callable=AsyncMock):
            stats = await daily_sync_all()

        # First user hit rate limit => batch stops
        assert stats["rate_limited"] == 1
        assert mock_sync.call_count == 1

    @pytest.mark.asyncio
    async def test_no_connected_users(self):
        """When no users have connected data sources, stats are all zero."""
        from src.scheduler import daily_sync_all

        mock_maker = _mock_session_maker_factory([])

        with patch(
            "src.scheduler.async_session_maker", mock_maker
        ), patch("asyncio.sleep", new_callable=AsyncMock):
            stats = await daily_sync_all()

        assert stats == {"success": 0, "failed": 0, "token_expired": 0, "rate_limited": 0}

    @pytest.mark.asyncio
    async def test_token_expired_counted(self):
        """Token expired status is tracked in stats."""
        from src.scheduler import daily_sync_all

        user = _make_user(**_fitbit_token_fields())

        mock_maker = _mock_session_maker_factory([user])

        with patch(
            "src.scheduler.async_session_maker", mock_maker
        ), patch(
            "src.scheduler.sync_user",
            new_callable=AsyncMock,
            return_value="token_expired",
        ), patch("asyncio.sleep", new_callable=AsyncMock):
            stats = await daily_sync_all()

        assert stats["token_expired"] == 1
        assert stats["success"] == 0

    @pytest.mark.asyncio
    async def test_failed_counted(self):
        """Failed sync status is tracked in stats."""
        from src.scheduler import daily_sync_all

        user = _make_user(**_fitbit_token_fields())

        mock_maker = _mock_session_maker_factory([user])

        with patch(
            "src.scheduler.async_session_maker", mock_maker
        ), patch(
            "src.scheduler.sync_user",
            new_callable=AsyncMock,
            return_value="failed",
        ), patch("asyncio.sleep", new_callable=AsyncMock):
            stats = await daily_sync_all()

        assert stats["failed"] == 1
        assert stats["success"] == 0
