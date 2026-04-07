"""Tests for token encryption/decryption."""

from src.services.token_encryption import encrypt_token, decrypt_token


class TestTokenEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        token = "test-fitbit-access-token-12345"
        encrypted = encrypt_token(token)
        assert encrypted != token
        assert decrypt_token(encrypted) == token

    def test_encrypted_is_different_each_time(self):
        token = "same-token"
        enc1 = encrypt_token(token)
        enc2 = encrypt_token(token)
        assert enc1 != enc2  # Fernet uses random IV

    def test_empty_string(self):
        encrypted = encrypt_token("")
        assert decrypt_token(encrypted) == ""

    def test_unicode_token(self):
        token = "tökên-with-üñíçödé"
        encrypted = encrypt_token(token)
        assert decrypt_token(encrypted) == token

    def test_long_token(self):
        token = "a" * 10000
        encrypted = encrypt_token(token)
        assert decrypt_token(encrypted) == token
