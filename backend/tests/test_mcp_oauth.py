"""Tests for the MCP OAuth provider and remote server."""

import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp.oauth_provider import (
    TONNDOAuthProvider,
    _authenticate_user,
    _Credentials,
    _AuthSession,
    _login_html,
)
from src.mcp.remote_server import _get_user_id, _parse_dates, _clamp_limit, MAX_LIMIT

from tests.conftest import test_session_maker


# ─── OAuth Provider Unit Tests ───────────────────────────────────────────────


class TestOAuthProviderInit:
    def test_creates_with_base_url(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        assert str(p.base_url) == "https://example.com/mcp"
        assert p.login_path == "/login"

    def test_empty_stores(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        assert p._clients == {}
        assert p._auth_codes == {}
        assert p._auth_sessions == {}


@pytest.mark.asyncio
class TestClientManagement:
    async def test_register_and_get(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        client = MagicMock()
        client.client_id = "test-client"
        await p.register_client(client)
        result = await p.get_client("test-client")
        assert result is client

    async def test_get_nonexistent(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        assert await p.get_client("nope") is None


@pytest.mark.asyncio
class TestAuthorize:
    async def test_returns_login_url(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        client = MagicMock()
        client.client_id = "c1"
        client.redirect_uris = None
        params = MagicMock()
        params.redirect_uri = "https://callback.com/cb"
        params.code_challenge = "challenge123"
        params.state = "state456"
        params.scopes = ["read:all"]
        params.redirect_uri_provided_explicitly = True

        url = await p.authorize(client, params)
        assert "/login?" in url
        assert "sid=" in url
        assert len(p._auth_sessions) == 1

    async def test_stores_session_with_correct_fields(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        client = MagicMock()
        client.client_id = "c1"
        client.redirect_uris = None
        params = MagicMock()
        params.redirect_uri = "https://cb.com"
        params.code_challenge = "ch"
        params.state = "st"
        params.scopes = ["read:vitals"]
        params.redirect_uri_provided_explicitly = False

        await p.authorize(client, params)
        session = list(p._auth_sessions.values())[0]
        assert session.client_id == "c1"
        assert session.redirect_uri == "https://cb.com"
        assert session.scopes == ["read:vitals"]
        assert session.csrf_token  # non-empty


@pytest.mark.asyncio
class TestLoadAuthorizationCode:
    async def test_valid_code(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        from mcp.server.auth.provider import AuthorizationCode
        code = AuthorizationCode(
            code="testcode",
            client_id="c1",
            scopes=["read:all"],
            code_challenge="ch",
            redirect_uri="https://cb.com",
            redirect_uri_provided_explicitly=True,
            expires_at=time.time() + 300,
        )
        p._auth_codes["testcode"] = code
        client = MagicMock()
        client.client_id = "c1"

        result = await p.load_authorization_code(client, "testcode")
        assert result is code

    async def test_expired_code(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        from mcp.server.auth.provider import AuthorizationCode
        code = AuthorizationCode(
            code="expired",
            client_id="c1",
            scopes=["read:all"],
            code_challenge="ch",
            redirect_uri="https://cb.com",
            redirect_uri_provided_explicitly=True,
            expires_at=time.time() - 10,
        )
        p._auth_codes["expired"] = code
        client = MagicMock()
        client.client_id = "c1"

        result = await p.load_authorization_code(client, "expired")
        assert result is None
        assert "expired" not in p._auth_codes

    async def test_wrong_client(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        from mcp.server.auth.provider import AuthorizationCode
        code = AuthorizationCode(
            code="c",
            client_id="c1",
            scopes=[],
            code_challenge="ch",
            redirect_uri="https://cb.com",
            redirect_uri_provided_explicitly=True,
            expires_at=time.time() + 300,
        )
        p._auth_codes["c"] = code
        client = MagicMock()
        client.client_id = "wrong"

        result = await p.load_authorization_code(client, "c")
        assert result is None

    async def test_nonexistent_code(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        client = MagicMock()
        client.client_id = "c1"
        assert await p.load_authorization_code(client, "nope") is None


@pytest.mark.asyncio
class TestExchangeAuthorizationCode:
    async def test_creates_pat_and_returns_token(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        user_id = uuid.uuid4()
        code = "testcode"
        p._code_user_ids[code] = user_id

        from mcp.server.auth.provider import AuthorizationCode
        auth_code = AuthorizationCode(
            code=code,
            client_id="c1",
            scopes=["read:all"],
            code_challenge="ch",
            redirect_uri="https://cb.com",
            redirect_uri_provided_explicitly=True,
            expires_at=time.time() + 300,
        )
        p._auth_codes[code] = auth_code

        client = MagicMock()
        client.client_id = "c1_abcdef"

        with patch("src.mcp.oauth_provider.create_token") as mock_create:
            mock_record = MagicMock()
            mock_create.return_value = (mock_record, "tonnd_raw_token_123")
            mock_session = AsyncMock()
            with patch("src.mcp.oauth_provider.async_session_maker") as mock_sm:
                mock_sm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_sm.return_value.__aexit__ = AsyncMock(return_value=False)
                result = await p.exchange_authorization_code(client, auth_code)

        assert result.access_token == "tonnd_raw_token_123"
        assert result.token_type == "Bearer"


@pytest.mark.asyncio
class TestLoadAccessToken:
    async def test_valid_token(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        mock_api_token = MagicMock()
        mock_api_token.user_id = uuid.uuid4()
        mock_api_token.scopes = ["read:all"]

        with patch("src.mcp.oauth_provider.verify_pat") as mock_verify:
            mock_verify.return_value = mock_api_token
            mock_session = AsyncMock()
            with patch("src.mcp.oauth_provider.async_session_maker") as mock_sm:
                mock_sm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_sm.return_value.__aexit__ = AsyncMock(return_value=False)
                result = await p.load_access_token("tonnd_testtoken")

        assert result is not None
        assert result.claims["sub"] == str(mock_api_token.user_id)
        assert result.scopes == ["read:all"]

    async def test_invalid_token(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        with patch("src.mcp.oauth_provider.verify_pat") as mock_verify:
            mock_verify.return_value = None
            mock_session = AsyncMock()
            with patch("src.mcp.oauth_provider.async_session_maker") as mock_sm:
                mock_sm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_sm.return_value.__aexit__ = AsyncMock(return_value=False)
                result = await p.load_access_token("invalid")
        assert result is None


@pytest.mark.asyncio
class TestRefreshRevoke:
    async def test_load_refresh_returns_none(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        assert await p.load_refresh_token(None, "token") is None

    async def test_exchange_refresh_raises(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        with pytest.raises(NotImplementedError):
            await p.exchange_refresh_token(None, None, [])

    async def test_revoke_is_noop(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        await p.revoke_token(None)  # should not raise


class TestCleanupExpired:
    def test_removes_expired_codes(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        from mcp.server.auth.provider import AuthorizationCode
        p._auth_codes["expired"] = AuthorizationCode(
            code="expired", client_id="c", scopes=[], code_challenge="c",
            redirect_uri="https://cb.com", redirect_uri_provided_explicitly=True,
            expires_at=time.time() - 10,
        )
        p._auth_codes["valid"] = AuthorizationCode(
            code="valid", client_id="c", scopes=[], code_challenge="c",
            redirect_uri="https://cb.com", redirect_uri_provided_explicitly=True,
            expires_at=time.time() + 300,
        )
        p._code_user_ids["expired"] = uuid.uuid4()
        p._code_user_ids["valid"] = uuid.uuid4()

        p._cleanup_expired()
        assert "expired" not in p._auth_codes
        assert "expired" not in p._code_user_ids
        assert "valid" in p._auth_codes


class TestLoginHtml:
    def test_renders_without_error(self):
        html = _login_html("sid123", "csrf456", "https://example.com")
        assert "sid123" in html
        assert "csrf456" in html
        assert "Sign in to TONND" in html

    def test_renders_error(self):
        html = _login_html("s", "c", error="Bad password")
        assert "Bad password" in html

    def test_escapes_xss(self):
        html = _login_html('<script>alert(1)</script>', "c")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_google_button_when_configured(self):
        import os
        os.environ["GOOGLE_CLIENT_ID"] = "test-google-id"
        try:
            html = _login_html("s", "c", "https://example.com")
            assert "Continue with Google" in html
            assert "google-start" in html
        finally:
            del os.environ["GOOGLE_CLIENT_ID"]


# ─── Remote Server Unit Tests ────────────────────────────────────────────────


class TestParseDate:
    def test_parses_valid_dates(self):
        from datetime import date
        sd, ed = _parse_dates("2026-01-01", "2026-01-31")
        assert sd == date(2026, 1, 1)
        assert ed == date(2026, 1, 31)

    def test_none_inputs(self):
        sd, ed = _parse_dates(None, None)
        assert sd is None
        assert ed is None


class TestClampLimit:
    def test_within_range(self):
        assert _clamp_limit(50) == 50

    def test_below_minimum(self):
        assert _clamp_limit(0) == 1
        assert _clamp_limit(-5) == 1

    def test_above_maximum(self):
        assert _clamp_limit(1000) == MAX_LIMIT

    def test_at_boundary(self):
        assert _clamp_limit(1) == 1
        assert _clamp_limit(MAX_LIMIT) == MAX_LIMIT


class TestGetUserId:
    def test_raises_without_token(self):
        with patch("src.mcp.remote_server.get_access_token", return_value=None):
            with pytest.raises(ValueError, match="Not authenticated"):
                _get_user_id()

    def test_raises_without_sub_claim(self):
        token = MagicMock()
        token.claims = {}
        token.scopes = ["read:all"]
        with patch("src.mcp.remote_server.get_access_token", return_value=token):
            with pytest.raises(ValueError, match="Not authenticated"):
                _get_user_id()

    def test_returns_uuid(self):
        uid = uuid.uuid4()
        token = MagicMock()
        token.claims = {"sub": str(uid)}
        token.scopes = ["read:all"]
        with patch("src.mcp.remote_server.get_access_token", return_value=token):
            assert _get_user_id() == uid

    def test_scope_enforcement(self):
        token = MagicMock()
        token.claims = {"sub": str(uuid.uuid4())}
        token.scopes = ["read:vitals"]
        with patch("src.mcp.remote_server.get_access_token", return_value=token):
            # Has the scope
            _get_user_id("read:vitals")  # should not raise
            # Missing scope
            with pytest.raises(ValueError, match="missing required scope"):
                _get_user_id("read:sleep")

    def test_read_all_grants_everything(self):
        token = MagicMock()
        token.claims = {"sub": str(uuid.uuid4())}
        token.scopes = ["read:all"]
        with patch("src.mcp.remote_server.get_access_token", return_value=token):
            _get_user_id("read:vitals")
            _get_user_id("read:sleep")
            _get_user_id("read:workouts")


@pytest.mark.asyncio
class TestAuthenticateUser:
    async def test_valid_credentials(self):
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        with patch("src.mcp.oauth_provider.async_session_maker") as mock_sm:
            mock_session = AsyncMock()
            mock_sm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sm.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("src.services.user_service.UserManager") as MockUM:
                instance = AsyncMock()
                instance.authenticate.return_value = mock_user
                MockUM.return_value = instance

                result = await _authenticate_user("test@test.com", "password")
                assert result is mock_user

    async def test_invalid_credentials(self):
        with patch("src.mcp.oauth_provider.async_session_maker") as mock_sm:
            mock_session = AsyncMock()
            mock_sm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sm.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("src.services.user_service.UserManager") as MockUM:
                instance = AsyncMock()
                instance.authenticate.return_value = None
                MockUM.return_value = instance

                result = await _authenticate_user("bad@test.com", "wrong")
                assert result is None

    async def test_exception_returns_none(self):
        with patch("src.mcp.oauth_provider.async_session_maker") as mock_sm:
            mock_session = AsyncMock()
            mock_sm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sm.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("src.services.user_service.UserManager") as MockUM:
                instance = AsyncMock()
                instance.authenticate.side_effect = Exception("DB error")
                MockUM.return_value = instance

                result = await _authenticate_user("err@test.com", "pass")
                assert result is None


# ─── Remote Server Tool Tests (mocked DB + auth) ─────────────────────────────


@pytest.mark.asyncio
class TestMCPTools:
    """Test MCP tool functions with mocked auth and DB."""

    @staticmethod
    def _mock_auth(user_id, scopes=None):
        """Patch get_access_token to return a mock token."""
        token = MagicMock()
        token.claims = {"sub": str(user_id)}
        token.scopes = scopes or ["read:all"]
        return patch("src.mcp.remote_server.get_access_token", return_value=token)

    @staticmethod
    def _mock_db(rows=None):
        """Patch async_session_maker to return mock session with query results."""
        from unittest.mock import AsyncMock
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = rows or []
        mock_session.execute.return_value = mock_result

        mock_sm = MagicMock()
        mock_sm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_sm.return_value.__aexit__ = AsyncMock(return_value=False)
        return patch("src.mcp.remote_server.async_session_maker", mock_sm)

    async def test_get_vitals(self):
        from src.mcp.remote_server import get_vitals
        uid = uuid.uuid4()
        with self._mock_auth(uid), self._mock_db():
            result = await get_vitals()
        assert result["count"] == 0
        assert result["data"] == []

    async def test_get_sleep(self):
        from src.mcp.remote_server import get_sleep
        uid = uuid.uuid4()
        with self._mock_auth(uid), self._mock_db():
            result = await get_sleep()
        assert "count" in result

    async def test_get_body_composition(self):
        from src.mcp.remote_server import get_body_composition
        uid = uuid.uuid4()
        with self._mock_auth(uid), self._mock_db():
            result = await get_body_composition()
        assert "count" in result

    async def test_get_workouts(self):
        from src.mcp.remote_server import get_workouts
        uid = uuid.uuid4()
        with self._mock_auth(uid), self._mock_db():
            result = await get_workouts()
        assert "count" in result

    async def test_get_activity(self):
        from src.mcp.remote_server import get_activity
        uid = uuid.uuid4()
        with self._mock_auth(uid), self._mock_db():
            result = await get_activity()
        assert "count" in result

    async def test_get_recovery_score(self):
        from src.mcp.remote_server import get_recovery_score
        uid = uuid.uuid4()
        with self._mock_auth(uid):
            with patch("src.mcp.remote_server.get_latest", return_value=None) as mock_gl:
                with self._mock_db():
                    result = await get_recovery_score()
        assert result["score"] is None

    async def test_get_all_metrics(self):
        from src.mcp.remote_server import get_all_metrics
        uid = uuid.uuid4()
        with self._mock_auth(uid), self._mock_db():
            result = await get_all_metrics()
        assert "count" in result

    async def test_get_vitals_with_dates(self):
        from src.mcp.remote_server import get_vitals
        uid = uuid.uuid4()
        with self._mock_auth(uid), self._mock_db():
            result = await get_vitals(start_date="2026-01-01", end_date="2026-01-31", limit=5)
        assert result["count"] == 0

    async def test_scope_denied(self):
        from src.mcp.remote_server import get_sleep
        uid = uuid.uuid4()
        with self._mock_auth(uid, scopes=["read:vitals"]), self._mock_db():
            with pytest.raises(ValueError, match="missing required scope"):
                await get_sleep()


# ─── OAuth Provider Route Tests ──────────────────────────────────────────────


class TestCompleteAuth:
    def test_generates_code_and_redirects(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        session = _AuthSession(
            client_id="c1",
            redirect_uri="https://callback.com/cb",
            code_challenge="ch",
            state="st",
            scopes=["read:all"],
            csrf_token="csrf",
            redirect_uri_provided_explicitly=True,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )

        user = MagicMock()
        user.id = uuid.uuid4()

        response = p._complete_auth(session, user)
        assert response.status_code == 302
        assert "code=" in response.headers["location"]
        assert "state=st" in response.headers["location"]
        assert len(p._auth_codes) == 1

    def test_stores_user_id(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        session = _AuthSession(
            client_id="c1",
            redirect_uri="https://callback.com/cb?existing=param",
            code_challenge="ch",
            state="",
            scopes=[],
            csrf_token="csrf",
            redirect_uri_provided_explicitly=True,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )

        user = MagicMock()
        user.id = uuid.uuid4()

        p._complete_auth(session, user)
        code = list(p._auth_codes.keys())[0]
        assert p._code_user_ids[code] == user.id


# ─── OAuth Provider Route Handler Tests (via Starlette TestClient) ───────────


@pytest.mark.asyncio
class TestOAuthRoutes:
    """Test the Starlette route handlers via direct request simulation."""

    def _get_provider_with_session(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        sid = "test-sid"
        csrf = "test-csrf"
        p._auth_sessions[sid] = _AuthSession(
            client_id="c1",
            redirect_uri="https://callback.com/cb",
            code_challenge="ch123",
            state="st456",
            scopes=["read:all"],
            csrf_token=csrf,
            redirect_uri_provided_explicitly=True,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        return p, sid, csrf

    async def test_login_get_renders_form(self):
        p, sid, csrf = self._get_provider_with_session()
        routes = p.get_routes(mcp_path="/mcp")
        login_route = [r for r in routes if getattr(r, 'path', '') == '/login'][0]

        from starlette.testclient import TestClient
        from starlette.routing import Router
        app = Router(routes=[login_route])
        client = TestClient(app)
        resp = client.get(f"/login?sid={sid}&csrf={csrf}")
        assert resp.status_code == 200
        assert "Sign in to TONND" in resp.text

    async def test_login_get_expired_session(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        p._auth_sessions["expired-sid"] = _AuthSession(
            client_id="c1", redirect_uri="https://cb.com", code_challenge="ch",
            state="", scopes=[], csrf_token="c", redirect_uri_provided_explicitly=True,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        routes = p.get_routes(mcp_path="/mcp")
        login_route = [r for r in routes if getattr(r, 'path', '') == '/login'][0]

        from starlette.testclient import TestClient
        from starlette.routing import Router
        app = Router(routes=[login_route])
        client = TestClient(app)
        resp = client.get("/login?sid=expired-sid&csrf=c")
        assert resp.status_code == 400

    async def test_login_post_invalid_csrf(self):
        p, sid, csrf = self._get_provider_with_session()
        routes = p.get_routes(mcp_path="/mcp")
        login_route = [r for r in routes if getattr(r, 'path', '') == '/login'][0]

        from starlette.testclient import TestClient
        from starlette.routing import Router
        app = Router(routes=[login_route])
        client = TestClient(app)
        resp = client.post("/login", data={
            "sid": sid, "csrf": "wrong", "email": "a@b.com", "password": "pass"
        })
        assert resp.status_code == 403

    async def test_login_post_bad_password(self):
        p, sid, csrf = self._get_provider_with_session()
        routes = p.get_routes(mcp_path="/mcp")
        login_route = [r for r in routes if getattr(r, 'path', '') == '/login'][0]

        from starlette.testclient import TestClient
        from starlette.routing import Router
        app = Router(routes=[login_route])
        client = TestClient(app)

        with patch("src.mcp.oauth_provider._authenticate_user", return_value=None):
            resp = client.post("/login", data={
                "sid": sid, "csrf": csrf, "email": "a@b.com", "password": "wrong"
            })
        assert resp.status_code == 401
        assert "Invalid email or password" in resp.text

    async def test_login_post_success_redirects(self):
        p, sid, csrf = self._get_provider_with_session()
        routes = p.get_routes(mcp_path="/mcp")
        login_route = [r for r in routes if getattr(r, 'path', '') == '/login'][0]

        from starlette.testclient import TestClient
        from starlette.routing import Router
        app = Router(routes=[login_route])
        client = TestClient(app, follow_redirects=False)

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        with patch("src.mcp.oauth_provider._authenticate_user", return_value=mock_user):
            resp = client.post("/login", data={
                "sid": sid, "csrf": csrf, "email": "a@b.com", "password": "correct"
            })
        assert resp.status_code == 302
        assert "code=" in resp.headers["location"]

    async def test_google_start_redirects_to_google(self):
        p, sid, csrf = self._get_provider_with_session()
        routes = p.get_routes(mcp_path="/mcp")
        google_route = [r for r in routes if getattr(r, 'path', '') == '/google-start'][0]

        from starlette.testclient import TestClient
        from starlette.routing import Router
        import os
        os.environ["GOOGLE_CLIENT_ID"] = "test-gid"
        try:
            app = Router(routes=[google_route])
            client = TestClient(app, follow_redirects=False)
            resp = client.get(f"/google-start?sid={sid}&csrf={csrf}")
            assert resp.status_code == 302
            assert "accounts.google.com" in resp.headers["location"]
        finally:
            del os.environ["GOOGLE_CLIENT_ID"]

    async def test_google_start_invalid_csrf(self):
        p, sid, csrf = self._get_provider_with_session()
        routes = p.get_routes(mcp_path="/mcp")
        google_route = [r for r in routes if getattr(r, 'path', '') == '/google-start'][0]

        from starlette.testclient import TestClient
        from starlette.routing import Router
        app = Router(routes=[google_route])
        client = TestClient(app)
        resp = client.get(f"/google-start?sid={sid}&csrf=wrong")
        assert resp.status_code == 403

    async def test_google_callback_invalid_state(self):
        p = TONNDOAuthProvider(base_url="https://example.com/mcp")
        routes = p.get_routes(mcp_path="/mcp")
        cb_route = [r for r in routes if getattr(r, 'path', '') == '/google-callback'][0]

        from starlette.testclient import TestClient
        from starlette.routing import Router
        app = Router(routes=[cb_route])
        client = TestClient(app)
        resp = client.get("/google-callback?code=abc&state=nosep")
        assert resp.status_code == 400

    async def test_google_callback_success(self):
        p, sid, csrf = self._get_provider_with_session()
        routes = p.get_routes(mcp_path="/mcp")
        cb_route = [r for r in routes if getattr(r, 'path', '') == '/google-callback'][0]

        from starlette.testclient import TestClient
        from starlette.routing import Router
        app = Router(routes=[cb_route])
        client = TestClient(app, follow_redirects=False)

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        with patch("src.mcp.oauth_provider._google_exchange", return_value=mock_user):
            resp = client.get(f"/google-callback?code=gcode&state={sid}:random")
        assert resp.status_code == 302
        assert "code=" in resp.headers["location"]

    async def test_google_callback_auth_failed(self):
        p, sid, csrf = self._get_provider_with_session()
        routes = p.get_routes(mcp_path="/mcp")
        cb_route = [r for r in routes if getattr(r, 'path', '') == '/google-callback'][0]

        from starlette.testclient import TestClient
        from starlette.routing import Router
        app = Router(routes=[cb_route])
        client = TestClient(app)

        with patch("src.mcp.oauth_provider._google_exchange", return_value=None):
            resp = client.get(f"/google-callback?code=gcode&state={sid}:random")
        assert resp.status_code == 401
