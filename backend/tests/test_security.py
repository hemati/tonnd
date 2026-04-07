"""Tests for security utilities (OAuth state, input validation)."""

from src.utils.security import (
    generate_secure_state,
    validate_secure_state,
    validate_date_format,
    validate_integer_param,
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
