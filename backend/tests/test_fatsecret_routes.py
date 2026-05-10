"""End-to-end tests for the FatSecret OAuth1 routes."""

from unittest.mock import AsyncMock, patch

import pytest

from src.services.fatsecret import oauth_state as fs_oauth_state
from src.services.token_encryption import decrypt_token


async def _register_and_login(client, email="fs@example.com", password="testpassword123") -> str:
    await client.post("/auth/register", json={"email": email, "password": password})
    login = await client.post("/auth/jwt/login", data={
        "username": email, "password": password,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return login.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _reset_oauth_state():
    fs_oauth_state._STORE.clear()
    yield
    fs_oauth_state._STORE.clear()


@pytest.fixture(autouse=True)
def _set_fs_env(monkeypatch):
    monkeypatch.setenv("FATSECRET_CONSUMER_KEY", "ck")
    monkeypatch.setenv("FATSECRET_CONSUMER_SECRET", "cs")


@pytest.fixture(autouse=True)
def _disable_backfill_background_task(monkeypatch):
    """Backfill spawns a BackgroundTask that opens its own DB session via the
    production async_session_maker. Tests use an in-memory SQLite, so the
    background task would try to query a DB it's never seen. Replace with a
    no-op for route tests — the backfill itself is covered by test_fatsecret_sync.py.
    """
    async def _noop(*args, **kwargs):
        return None
    monkeypatch.setattr("app._run_fatsecret_backfill", _noop)


@pytest.mark.asyncio
class TestFatSecretInit:
    async def test_returns_authorize_url_and_stashes_secret(self, client):
        token = await _register_and_login(client)
        with patch(
            "app.fatsecret_fetch_request_token",
            new_callable=AsyncMock,
            return_value={"oauth_token": "rt_abc", "oauth_token_secret": "rts_xyz"},
        ):
            resp = await client.get("/auth/fatsecret/init", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["authorization_url"].startswith("https://www.fatsecret.com/oauth/authorize?oauth_token=rt_abc")
        # Secret stashed under the oauth_token, not echoed back.
        assert "rts_xyz" not in body["authorization_url"]
        assert "rt_abc" in fs_oauth_state._STORE

    async def test_unauthenticated(self, client):
        resp = await client.get("/auth/fatsecret/init")
        assert resp.status_code == 401

    async def test_propagates_upstream_failure_as_502(self, client):
        from src.services.fatsecret.client import FatSecretAPIError
        token = await _register_and_login(client)
        with patch(
            "app.fatsecret_fetch_request_token",
            new_callable=AsyncMock,
            side_effect=FatSecretAPIError("boom"),
        ):
            resp = await client.get("/auth/fatsecret/init", headers=_auth(token))
        assert resp.status_code == 502


@pytest.mark.asyncio
class TestFatSecretCallback:
    async def test_persists_tokens_and_redirects(self, client):
        token = await _register_and_login(client)
        # Get the user's id by calling /api/user
        me = await client.get("/api/user", headers=_auth(token))
        user_id = me.json()["user_id"]

        # Simulate /init having stashed a request_token.
        import uuid
        fs_oauth_state.put("rt_abc", uuid.UUID(user_id), "rts_xyz")

        with patch(
            "app.fatsecret_fetch_access_token",
            new_callable=AsyncMock,
            return_value={"oauth_token": "acc_t", "oauth_token_secret": "acc_s"},
        ):
            resp = await client.get(
                "/auth/fatsecret/callback?oauth_token=rt_abc&oauth_verifier=ver1",
                headers=_auth(token),
                follow_redirects=False,
            )
        assert resp.status_code == 307  # RedirectResponse
        assert "fatsecret=connected" in resp.headers["location"]

        # Token consumed (single-use).
        assert "rt_abc" not in fs_oauth_state._STORE

        # Persisted + encrypted on the user.
        me2 = await client.get("/api/user", headers=_auth(token))
        assert me2.json()["fatsecret_connected"] is True

    async def test_rejects_unknown_oauth_token(self, client):
        token = await _register_and_login(client)
        resp = await client.get(
            "/auth/fatsecret/callback?oauth_token=stale&oauth_verifier=v",
            headers=_auth(token),
        )
        assert resp.status_code == 400

    async def test_rejects_when_token_belongs_to_other_user(self, client):
        """Token-binding gap defense (Step 5 security finding)."""
        # Stash a token bound to user A.
        import uuid
        attacker_user_id = uuid.uuid4()  # not the logged-in user
        fs_oauth_state.put("rt_abc", attacker_user_id, "rts_xyz")

        # User B logs in and tries to consume it.
        victim_token = await _register_and_login(client, email="victim@example.com")
        resp = await client.get(
            "/auth/fatsecret/callback?oauth_token=rt_abc&oauth_verifier=v",
            headers=_auth(victim_token),
        )
        assert resp.status_code == 403
        # Token still consumed (pop is single-use) so attacker can't reuse it either.
        assert "rt_abc" not in fs_oauth_state._STORE


@pytest.mark.asyncio
class TestFatSecretDisconnect:
    async def test_clears_tokens(self, client):
        token = await _register_and_login(client)
        # Connect first.
        me = await client.get("/api/user", headers=_auth(token))
        user_id = me.json()["user_id"]
        import uuid
        fs_oauth_state.put("rt_abc", uuid.UUID(user_id), "rts_xyz")
        with patch(
            "app.fatsecret_fetch_access_token",
            new_callable=AsyncMock,
            return_value={"oauth_token": "acc_t", "oauth_token_secret": "acc_s"},
        ):
            await client.get(
                "/auth/fatsecret/callback?oauth_token=rt_abc&oauth_verifier=v",
                headers=_auth(token),
                follow_redirects=False,
            )
        # Disconnect.
        resp = await client.delete("/auth/fatsecret/disconnect", headers=_auth(token))
        assert resp.status_code == 200
        me2 = await client.get("/api/user", headers=_auth(token))
        assert me2.json()["fatsecret_connected"] is False


@pytest.mark.asyncio
class TestUserResponseShape:
    async def test_includes_fatsecret_connected_flag(self, client):
        token = await _register_and_login(client)
        resp = await client.get("/api/user", headers=_auth(token))
        body = resp.json()
        assert "fatsecret_connected" in body
        assert body["fatsecret_connected"] is False
