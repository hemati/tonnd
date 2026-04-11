"""Tests for Personal Access Token service."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.api_models import APIToken
from src.services.token_service import (
    MAX_TOKENS_PER_USER,
    TOKEN_PREFIX,
    create_token,
    generate_raw_token,
    hash_token,
    list_user_tokens,
    revoke_token,
    token_display_prefix,
    validate_scopes,
    verify_token,
)

from tests.conftest import test_session_maker


# ─── Unit tests (no DB) ─────────────────────────────────────────────────────


class TestGenerateRawToken:
    def test_starts_with_prefix(self):
        token = generate_raw_token()
        assert token.startswith(TOKEN_PREFIX)

    def test_sufficient_length(self):
        token = generate_raw_token()
        assert len(token) > 40

    def test_unique(self):
        tokens = {generate_raw_token() for _ in range(100)}
        assert len(tokens) == 100


class TestHashToken:
    def test_deterministic(self):
        token = "tonnd_test123"
        assert hash_token(token) == hash_token(token)

    def test_different_tokens_different_hashes(self):
        assert hash_token("tonnd_aaa") != hash_token("tonnd_bbb")

    def test_hex_output(self):
        h = hash_token("tonnd_test")
        assert len(h) == 64  # SHA-256 hex = 64 chars
        assert all(c in "0123456789abcdef" for c in h)


class TestTokenDisplayPrefix:
    def test_returns_first_12_chars(self):
        token = "tonnd_abcdefghijk"
        assert token_display_prefix(token) == "tonnd_abcdef"


class TestValidateScopes:
    def test_valid_scopes(self):
        result = validate_scopes(["read:vitals", "read:sleep"])
        assert result == ["read:sleep", "read:vitals"]  # sorted

    def test_read_all_valid(self):
        result = validate_scopes(["read:all"])
        assert result == ["read:all"]

    def test_invalid_scope_raises(self):
        with pytest.raises(ValueError, match="Invalid scopes"):
            validate_scopes(["read:vitals", "write:everything"])

    def test_deduplicates(self):
        result = validate_scopes(["read:vitals", "read:vitals"])
        assert result == ["read:vitals"]

    def test_empty_raises(self):
        # Empty list is technically valid (no invalid scopes)
        result = validate_scopes([])
        assert result == []


# ─── Integration tests (with DB) ────────────────────────────────────────────


@pytest.mark.asyncio
class TestCreateToken:
    async def test_create_returns_record_and_raw(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            record, raw = await create_token(
                session, user_id, "Test Token", ["read:all"]
            )
            await session.commit()

            assert raw.startswith(TOKEN_PREFIX)
            assert record.name == "Test Token"
            assert record.scopes == ["read:all"]
            assert record.is_active is True
            assert record.token_hash == hash_token(raw)
            assert record.token_prefix == raw[:12]

    async def test_create_with_expiry(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            expires = datetime.now(timezone.utc) + timedelta(days=30)
            record, raw = await create_token(
                session, user_id, "Expiring", ["read:vitals"], expires_at=expires
            )
            await session.commit()
            assert record.expires_at is not None

    async def test_create_enforces_max_tokens(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            for i in range(MAX_TOKENS_PER_USER):
                await create_token(session, user_id, f"Token {i}", ["read:all"])
            await session.commit()

            with pytest.raises(ValueError, match="Maximum"):
                await create_token(session, user_id, "One too many", ["read:all"])

    async def test_invalid_scopes_rejected(self):
        async with test_session_maker() as session:
            with pytest.raises(ValueError, match="Invalid"):
                await create_token(
                    session, uuid.uuid4(), "Bad", ["read:nonexistent"]
                )


@pytest.mark.asyncio
class TestVerifyToken:
    async def test_valid_token(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            _, raw = await create_token(session, user_id, "Valid", ["read:all"])
            await session.commit()

            result = await verify_token(session, raw)
            assert result is not None
            assert result.user_id == user_id
            assert result.last_used_at is not None

    async def test_invalid_token_returns_none(self):
        async with test_session_maker() as session:
            result = await verify_token(session, "tonnd_nonexistent123456789")
            assert result is None

    async def test_wrong_prefix_returns_none(self):
        async with test_session_maker() as session:
            result = await verify_token(session, "wrong_prefix_token")
            assert result is None

    async def test_revoked_token_returns_none(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            record, raw = await create_token(session, user_id, "Rev", ["read:all"])
            await session.commit()
            await revoke_token(session, record.id, user_id)
            await session.commit()

            result = await verify_token(session, raw)
            assert result is None

    async def test_expired_token_returns_none(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            past = datetime.now(timezone.utc) - timedelta(hours=1)
            _, raw = await create_token(
                session, user_id, "Expired", ["read:all"], expires_at=past
            )
            await session.commit()

            result = await verify_token(session, raw)
            assert result is None


@pytest.mark.asyncio
class TestRevokeToken:
    async def test_revoke_existing(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            record, _ = await create_token(session, user_id, "ToRevoke", ["read:all"])
            await session.commit()

            result = await revoke_token(session, record.id, user_id)
            assert result is True

    async def test_revoke_nonexistent(self):
        async with test_session_maker() as session:
            result = await revoke_token(session, uuid.uuid4(), uuid.uuid4())
            assert result is False

    async def test_revoke_wrong_user(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            record, _ = await create_token(session, user_id, "Mine", ["read:all"])
            await session.commit()

            result = await revoke_token(session, record.id, uuid.uuid4())
            assert result is False


@pytest.mark.asyncio
class TestListUserTokens:
    async def test_list_empty(self):
        async with test_session_maker() as session:
            result = await list_user_tokens(session, uuid.uuid4())
            assert result == []

    async def test_list_returns_all(self):
        async with test_session_maker() as session:
            user_id = uuid.uuid4()
            await create_token(session, user_id, "A", ["read:all"])
            await create_token(session, user_id, "B", ["read:vitals"])
            await session.commit()

            result = await list_user_tokens(session, user_id)
            assert len(result) == 2

    async def test_list_does_not_return_other_users(self):
        async with test_session_maker() as session:
            user1 = uuid.uuid4()
            user2 = uuid.uuid4()
            await create_token(session, user1, "User1", ["read:all"])
            await create_token(session, user2, "User2", ["read:all"])
            await session.commit()

            result = await list_user_tokens(session, user1)
            assert len(result) == 1
            assert result[0].name == "User1"
