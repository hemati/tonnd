"""Tests for FatSecret OAuth1 in-memory request-token store."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from src.services.fatsecret import oauth_state as st


@pytest.fixture(autouse=True)
def _reset_store():
    st._clear_for_tests()
    yield
    st._clear_for_tests()


class TestPutPopBasic:
    def test_round_trip(self):
        uid = uuid.uuid4()
        st.put("tok1", uid, "secret1")
        out = st.pop_if_valid("tok1")
        assert out == (uid, "secret1")

    def test_pop_missing_token(self):
        assert st.pop_if_valid("nope") is None

    def test_pop_is_single_use(self):
        uid = uuid.uuid4()
        st.put("tok1", uid, "secret1")
        st.pop_if_valid("tok1")
        # Second pop should miss.
        assert st.pop_if_valid("tok1") is None

    def test_overwrite_on_repeat_put(self):
        """User clicks Connect twice — second put wins; first becomes orphaned."""
        uid = uuid.uuid4()
        st.put("tok1", uid, "secret_a")
        st.put("tok1", uid, "secret_b")
        out = st.pop_if_valid("tok1")
        assert out == (uid, "secret_b")


class TestLengthCap:
    def test_rejects_oversize_oauth_token(self):
        with pytest.raises(st.TokenTooLongError):
            st.put("x" * (st.MAX_TOKEN_LEN + 1), uuid.uuid4(), "secret")

    def test_rejects_oversize_secret(self):
        with pytest.raises(st.TokenTooLongError):
            st.put("tok", uuid.uuid4(), "x" * (st.MAX_TOKEN_LEN + 1))

    def test_accepts_at_limit(self):
        st.put("x" * st.MAX_TOKEN_LEN, uuid.uuid4(), "x" * st.MAX_TOKEN_LEN)


class TestTTL:
    def test_pop_after_ttl_returns_none(self):
        uid = uuid.uuid4()
        # Inject a fake clock by patching _now. First call (the put) anchors at t0,
        # second (the pop) jumps past TTL.
        t0 = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
        with patch.object(st, "_now", side_effect=[t0, t0, t0 + st.TTL + timedelta(seconds=1), t0 + st.TTL + timedelta(seconds=1)]):
            st.put("tok1", uid, "secret1")
            assert st.pop_if_valid("tok1") is None

    def test_expired_entries_swept_on_put(self):
        uid = uuid.uuid4()
        t0 = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
        with patch.object(st, "_now", side_effect=[
            t0, t0,  # first put: drop_expired (no entries) + set ttl
            t0 + st.TTL + timedelta(seconds=1),  # second put: drop_expired sees old as expired
            t0 + st.TTL + timedelta(seconds=1),  # second put: set ttl
        ]):
            st.put("tok_old", uid, "old_secret")
            st.put("tok_new", uid, "new_secret")
        assert "tok_old" not in st._STORE
        assert "tok_new" in st._STORE
