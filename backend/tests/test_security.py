"""Tests for security utilities (OAuth state, input validation)."""

import time
from unittest.mock import patch

from src.utils.security import (
    generate_secure_state,
    sanitize_event_for_logging,
    validate_secure_state,
    validate_date_format,
    validate_integer_param,
    STATE_EXPIRY_SECONDS,
)


class TestOAuthState:
    def test_generate_and_validate(self):
        user_id = "test-user-123"
        state = generate_secure_state(user_id)
        recovered_id, is_valid = validate_secure_state(state)
        assert is_valid
        assert recovered_id == user_id

    def test_invalid_state_format(self):
        _, is_valid = validate_secure_state("not-a-valid-state")
        assert not is_valid

    def test_tampered_signature(self):
        state = generate_secure_state("user-123")
        parts = state.split(":")
        parts[-1] = "tampered"
        tampered = ":".join(parts)
        _, is_valid = validate_secure_state(tampered)
        assert not is_valid

    def test_empty_state(self):
        _, is_valid = validate_secure_state("")
        assert not is_valid

    def test_different_users_different_states(self):
        s1 = generate_secure_state("user-1")
        s2 = generate_secure_state("user-2")
        assert s1 != s2

    def test_expired_state(self):
        """State older than STATE_EXPIRY_SECONDS should be rejected."""
        state = generate_secure_state("user-exp")
        # Fast-forward time past expiry
        future = time.time() + STATE_EXPIRY_SECONDS + 100
        with patch("src.utils.security.time.time", return_value=future):
            uid, is_valid = validate_secure_state(state)
        assert not is_valid
        assert uid == ""

    def test_malformed_timestamp(self):
        """State with a non-integer timestamp should be rejected."""
        bad_state = "user-id:not-a-number:nonce:abcdef1234567890"
        uid, is_valid = validate_secure_state(bad_state)
        assert not is_valid
        assert uid == ""

    def test_too_few_parts(self):
        """State with fewer than 4 colon-separated parts should be rejected."""
        uid, is_valid = validate_secure_state("a:b:c")
        assert not is_valid

    def test_too_many_parts(self):
        """State with more than 4 parts should be rejected."""
        uid, is_valid = validate_secure_state("a:b:c:d:e")
        assert not is_valid

    def test_state_format_has_four_parts(self):
        """Generated state should have exactly 4 colon-separated parts."""
        state = generate_secure_state("user-99")
        parts = state.split(":")
        assert len(parts) == 4

    def test_state_signature_is_16_chars(self):
        """The HMAC signature should be truncated to 16 hex chars."""
        state = generate_secure_state("user-sig")
        sig = state.split(":")[-1]
        assert len(sig) == 16


class TestSanitizeEvent:
    def test_redacts_authorization_header(self):
        event = {"headers": {"Authorization": "Bearer secret-token"}}
        sanitized = sanitize_event_for_logging(event)
        assert sanitized["headers"]["Authorization"] == "[REDACTED]"
        # Original should not be modified
        assert event["headers"]["Authorization"] == "Bearer secret-token"

    def test_redacts_cookie_header(self):
        event = {"headers": {"Cookie": "session=abc123"}}
        sanitized = sanitize_event_for_logging(event)
        assert sanitized["headers"]["Cookie"] == "[REDACTED]"

    def test_redacts_lowercase_headers(self):
        event = {"headers": {"authorization": "Bearer tok", "cookie": "x=y"}}
        sanitized = sanitize_event_for_logging(event)
        assert sanitized["headers"]["authorization"] == "[REDACTED]"
        assert sanitized["headers"]["cookie"] == "[REDACTED]"

    def test_redacts_request_context_authorizer(self):
        event = {"requestContext": {"authorizer": {"claims": {"sub": "user-1"}}}}
        sanitized = sanitize_event_for_logging(event)
        assert sanitized["requestContext"]["authorizer"] == "[REDACTED]"

    def test_no_headers_key(self):
        event = {"body": "data"}
        sanitized = sanitize_event_for_logging(event)
        assert "headers" not in sanitized

    def test_preserves_non_sensitive_headers(self):
        event = {"headers": {"Content-Type": "application/json", "Authorization": "Bearer x"}}
        sanitized = sanitize_event_for_logging(event)
        assert sanitized["headers"]["Content-Type"] == "application/json"
        assert sanitized["headers"]["Authorization"] == "[REDACTED]"


class TestDateValidation:
    def test_valid_date(self):
        assert validate_date_format("2026-04-07")

    def test_invalid_format(self):
        assert not validate_date_format("04-07-2026")
        assert not validate_date_format("2026/04/07")

    def test_invalid_date(self):
        assert not validate_date_format("2026-13-01")
        assert not validate_date_format("2026-02-30")

    def test_empty_string(self):
        assert not validate_date_format("")

    def test_none(self):
        assert not validate_date_format(None)

    def test_non_string_type(self):
        assert not validate_date_format(12345)


class TestIntegerParam:
    def test_valid_integer(self):
        assert validate_integer_param("7", default=1) == 7

    def test_default_on_none(self):
        assert validate_integer_param(None, default=5) == 5

    def test_clamp_min(self):
        assert validate_integer_param("0", default=1, min_val=1) == 1

    def test_clamp_max(self):
        assert validate_integer_param("999", default=1, max_val=30) == 30

    def test_invalid_string(self):
        assert validate_integer_param("abc", default=7) == 7

    def test_float_string_returns_default(self):
        assert validate_integer_param("3.14", default=2) == 2

    def test_type_error_returns_default(self):
        assert validate_integer_param([], default=9) == 9
