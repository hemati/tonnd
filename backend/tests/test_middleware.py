"""Tests for security headers, rate limiting key function, and audit middleware."""

import pytest

from src.middleware.rate_limit import _get_key


class _FakeRequest:
    """Minimal request-like object for testing rate limit key extraction."""

    def __init__(self, auth_header=None, ip="1.2.3.4"):
        self.headers = {}
        if auth_header:
            self.headers["Authorization"] = auth_header

        class Client:
            host = ip
        self.client = Client()


class TestRateLimitKey:
    def test_pat_key(self):
        req = _FakeRequest("Bearer tonnd_abc123def456ghi789")
        key = _get_key(req)
        assert key.startswith("pat:")

    def test_jwt_key_uses_ip(self):
        req = _FakeRequest("Bearer eyJhbGciOiJIUzI1NiJ9.test.sig", ip="10.0.0.1")
        key = _get_key(req)
        assert key == "jwt:10.0.0.1"

    def test_no_auth_uses_ip(self):
        req = _FakeRequest(ip="192.168.1.1")
        key = _get_key(req)
        assert key == "192.168.1.1"

    def test_empty_auth_uses_ip(self):
        req = _FakeRequest("", ip="10.0.0.5")
        key = _get_key(req)
        assert key == "10.0.0.5"


@pytest.mark.asyncio
class TestSecurityHeaders:
    async def test_security_headers_present(self, client):
        r = await client.get("/health")
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert "max-age" in r.headers["Strict-Transport-Security"]
        assert "strict-origin" in r.headers["Referrer-Policy"]
        assert "camera=()" in r.headers["Permissions-Policy"]
        assert "default-src" in r.headers["Content-Security-Policy"]

    async def test_api_endpoints_have_no_cache(self, client):
        # /api/v1/ endpoints require auth, use /api/data for simpler test
        from tests.test_api_v1 import register_and_login
        token = await register_and_login(client, "cache-test@example.com")
        r = await client.get("/api/data?days=7", headers={"Authorization": f"Bearer {token}"})
        assert r.headers.get("Cache-Control") == "no-store"
        assert r.headers.get("Pragma") == "no-cache"

    async def test_non_api_no_cache_headers(self, client):
        r = await client.get("/health")
        # /health is not under /api/ so Cache-Control should not be no-store
        cc = r.headers.get("Cache-Control", "")
        assert cc != "no-store"
