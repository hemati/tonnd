"""TONND OAuth Provider for FastMCP — authenticates against fastapi-users."""

import html
import os
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastmcp.server.auth import AccessToken, OAuthProvider
from mcp.server.auth.provider import AuthorizationCode, AuthorizationParams
from mcp.server.auth.settings import ClientRegistrationOptions
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from src.database import async_session_maker
from src.services.token_service import create_token, verify_token as verify_pat

AUTH_CODE_TTL = timedelta(minutes=5)
AUTH_SESSION_TTL = timedelta(minutes=10)


@dataclass
class _Credentials:
    """Minimal credentials object for fastapi-users authenticate()."""
    username: str
    password: str


@dataclass
class _AuthSession:
    """Server-side session for an in-progress OAuth authorization."""
    client_id: str
    redirect_uri: str
    code_challenge: str
    state: str
    scopes: list[str]
    csrf_token: str
    redirect_uri_provided_explicitly: bool
    expires_at: datetime


class TONNDOAuthProvider(OAuthProvider):
    """OAuth 2.1 provider backed by fastapi-users (email/password + Google)."""

    def __init__(self, base_url: str, login_path: str = "/login"):
        super().__init__(
            base_url=base_url,
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=["read:all", "read:vitals", "read:body", "read:sleep",
                              "read:activity", "read:workouts", "read:recovery"],
                default_scopes=["read:all"],
            ),
        )
        self.login_path = login_path
        self._clients: dict[str, OAuthClientInformationFull] = {}
        self._auth_codes: dict[str, AuthorizationCode] = {}
        self._code_user_ids: dict[str, uuid.UUID] = {}  # code -> user_id
        self._auth_sessions: dict[str, _AuthSession] = {}

    def _cleanup_expired(self) -> None:
        now_ts = time.time()
        now_dt = datetime.now(timezone.utc)
        expired_codes = [k for k, v in self._auth_codes.items() if v.expires_at < now_ts]
        for k in expired_codes:
            del self._auth_codes[k]
            self._code_user_ids.pop(k, None)
        self._auth_sessions = {k: v for k, v in self._auth_sessions.items() if v.expires_at > now_dt}

    # ─── Client Management ───────────────────────────────────────────────

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self._clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self._clients[client_info.client_id] = client_info

    # ─── Authorization ───────────────────────────────────────────────────

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        self._cleanup_expired()

        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)

        redirect_uri = str(params.redirect_uri)
        if client.redirect_uris:
            allowed = [str(u) for u in client.redirect_uris]
            if redirect_uri not in allowed:
                from mcp.server.auth.errors import AuthorizeError
                raise AuthorizeError(error="invalid_request", error_description="redirect_uri not registered")

        self._auth_sessions[session_id] = _AuthSession(
            client_id=client.client_id,
            redirect_uri=redirect_uri,
            code_challenge=params.code_challenge,
            state=params.state or "",
            scopes=params.scopes or [],
            csrf_token=csrf_token,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            expires_at=datetime.now(timezone.utc) + AUTH_SESSION_TTL,
        )

        query = urlencode({"sid": session_id, "csrf": csrf_token})
        return f"{self.base_url}{self.login_path}?{query}"

    def get_routes(self, mcp_path: str | None = None) -> list:
        from starlette.requests import Request
        from starlette.responses import HTMLResponse, RedirectResponse
        from starlette.routing import Route

        routes = super().get_routes(mcp_path=mcp_path)

        async def login_page(request: Request):
            sid = request.query_params.get("sid", "")
            csrf = request.query_params.get("csrf", "")

            if request.method == "GET":
                session = self._auth_sessions.get(sid)
                if not session or session.expires_at < datetime.now(timezone.utc):
                    return HTMLResponse("Authorization session expired. Please try again.", status_code=400)
                return HTMLResponse(_login_html(sid, csrf, str(self.base_url)))

            form = await request.form()
            sid = str(form.get("sid", ""))
            csrf = str(form.get("csrf", ""))
            email = str(form.get("email", ""))
            password = str(form.get("password", ""))

            session = self._auth_sessions.get(sid)
            if not session or session.expires_at < datetime.now(timezone.utc):
                return HTMLResponse("Authorization session expired. Please try again.", status_code=400)
            if csrf != session.csrf_token:
                return HTMLResponse("Invalid CSRF token.", status_code=403)

            user = await _authenticate_user(email, password)
            if not user:
                return HTMLResponse(
                    _login_html(sid, csrf, str(self.base_url), error="Invalid email or password"),
                    status_code=401,
                )

            return self._complete_auth(session, user)

        async def google_start(request: Request):
            sid = request.query_params.get("sid", "")
            csrf = request.query_params.get("csrf", "")

            session = self._auth_sessions.get(sid)
            if not session or session.expires_at < datetime.now(timezone.utc):
                return HTMLResponse("Authorization session expired.", status_code=400)
            if csrf != session.csrf_token:
                return HTMLResponse("Invalid CSRF token.", status_code=403)

            google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
            if not google_client_id:
                return HTMLResponse("Google OAuth not configured", status_code=500)

            google_state = f"{sid}:{secrets.token_urlsafe(16)}"

            google_redirect = f"{self.base_url}/google-callback"
            google_url = (
                "https://accounts.google.com/o/oauth2/v2/auth?"
                + urlencode({
                    "client_id": google_client_id,
                    "redirect_uri": google_redirect,
                    "response_type": "code",
                    "scope": "openid email profile",
                    "state": google_state,
                    "access_type": "online",
                })
            )
            return RedirectResponse(google_url, status_code=302)

        async def google_callback(request: Request):
            google_code = request.query_params.get("code", "")
            google_state = request.query_params.get("state", "")

            if ":" not in google_state:
                return HTMLResponse("Invalid OAuth state", status_code=400)
            sid = google_state.split(":")[0]

            session = self._auth_sessions.get(sid)
            if not session or session.expires_at < datetime.now(timezone.utc):
                return HTMLResponse("Authorization session expired.", status_code=400)

            user = await _google_exchange(google_code, f"{self.base_url}/google-callback")
            if not user:
                return HTMLResponse("Google authentication failed. Make sure you have a TONND account.", status_code=401)

            return self._complete_auth(session, user)

        routes.append(Route(self.login_path, login_page, methods=["GET", "POST"]))
        routes.append(Route("/google-start", google_start, methods=["GET"]))
        routes.append(Route("/google-callback", google_callback, methods=["GET"]))
        return routes

    def _complete_auth(self, session: _AuthSession, user):
        from starlette.responses import RedirectResponse

        self._auth_sessions = {k: v for k, v in self._auth_sessions.items() if v is not session}

        code = secrets.token_urlsafe(32)

        # Use the official MCP SDK AuthorizationCode model
        self._auth_codes[code] = AuthorizationCode(
            code=code,
            client_id=session.client_id,
            scopes=session.scopes or ["read:all"],
            code_challenge=session.code_challenge,
            redirect_uri=session.redirect_uri,
            redirect_uri_provided_explicitly=session.redirect_uri_provided_explicitly,
            expires_at=time.time() + AUTH_CODE_TTL.total_seconds(),
        )
        # Store user_id separately (not part of the SDK model)
        self._code_user_ids[code] = user.id

        sep = "&" if "?" in session.redirect_uri else "?"
        target = f"{session.redirect_uri}{sep}code={code}"
        if session.state:
            target += f"&state={session.state}"
        return RedirectResponse(target, status_code=302)

    # ─── Authorization Code ──────────────────────────────────────────────

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        entry = self._auth_codes.get(authorization_code)
        if not entry:
            return None
        if entry.expires_at < time.time():
            del self._auth_codes[authorization_code]
            self._code_user_ids.pop(authorization_code, None)
            return None
        if entry.client_id != client.client_id:
            return None
        return entry

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        code_str = authorization_code.code
        self._auth_codes.pop(code_str, None)
        user_id = self._code_user_ids.pop(code_str, None)

        if not user_id:
            from mcp.server.auth.errors import TokenError
            raise TokenError(error="invalid_grant", error_description="Unknown authorization code")

        async with async_session_maker() as session:
            token_record, raw_token = await create_token(
                session,
                user_id=user_id,
                name=f"MCP ({client.client_id[:8]})",
                scopes=authorization_code.scopes or ["read:all"],
            )
            await session.commit()

        return OAuthToken(access_token=raw_token, token_type="Bearer")

    # ─── Token Verification ──────────────────────────────────────────────

    async def load_access_token(self, token: str) -> AccessToken | None:
        async with async_session_maker() as session:
            api_token = await verify_pat(session, token)
            if not api_token:
                return None
            await session.commit()

        return AccessToken(
            token=token,
            client_id="tonnd",
            scopes=api_token.scopes,
            claims={"sub": str(api_token.user_id)},
        )

    # ─── Refresh / Revoke ────────────────────────────────────────────────

    async def load_refresh_token(self, client, refresh_token: str):
        return None

    async def exchange_refresh_token(self, client, refresh_token, scopes: list[str]):
        raise NotImplementedError("Refresh tokens not supported")

    async def revoke_token(self, token) -> None:
        pass


# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _authenticate_user(email: str, password: str):
    from fastapi_users.db import SQLAlchemyUserDatabase
    from src.models.db_models import OAuthAccount, User
    from src.services.user_service import UserManager

    async with async_session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, User, OAuthAccount)
        manager = UserManager(user_db)
        try:
            return await manager.authenticate(_Credentials(username=email, password=password))
        except Exception:
            return None


async def _google_exchange(code: str, redirect_uri: str):
    from src.services.user_service import google_oauth_client
    from sqlalchemy import select
    from src.models.db_models import User

    if not google_oauth_client:
        return None

    try:
        token = await google_oauth_client.get_access_token(code, redirect_uri)
        _, email = await google_oauth_client.get_id_email(token["access_token"])
    except Exception:
        return None

    if not email:
        return None

    async with async_session_maker() as session:
        return (
            await session.execute(select(User).where(User.email == email))
        ).unique().scalar_one_or_none()


def _login_html(sid: str, csrf: str, base_url: str = "", error: str = "") -> str:
    error_html = f'<p style="color:#f87171;margin-bottom:12px;font-size:13px">{html.escape(error)}</p>' if error else ""

    google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    google_section = ""
    if google_client_id:
        google_query = urlencode({"sid": sid, "csrf": csrf})
        google_section = f"""
        <a href="{base_url}/google-start?{html.escape(google_query)}" class="google-btn">
            <svg width="16" height="16" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
            Continue with Google
        </a>
        <div class="divider"><span>or</span></div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sign in — TONND</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #0a0a0a; color: #fff; font-family: -apple-system, BlinkMacSystemFont, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; }}
        .card {{ width: 100%; max-width: 360px; padding: 32px; }}
        h1 {{ font-size: 20px; font-weight: 600; margin-bottom: 8px; }}
        p.sub {{ font-size: 13px; color: rgba(255,255,255,0.5); margin-bottom: 24px; }}
        input[type="email"], input[type="password"] {{ width: 100%; padding: 10px 14px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.04); color: #fff; font-size: 14px; margin-bottom: 12px; outline: none; }}
        input:focus {{ border-color: rgba(255,255,255,0.25); }}
        button {{ width: 100%; padding: 10px; border-radius: 6px; border: none; background: #fff; color: #000; font-size: 14px; font-weight: 500; cursor: pointer; }}
        button:hover {{ background: rgba(255,255,255,0.9); }}
        .google-btn {{ display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.12); background: transparent; color: rgba(255,255,255,0.6); font-size: 14px; text-decoration: none; margin-bottom: 16px; }}
        .google-btn:hover {{ color: #fff; border-color: rgba(255,255,255,0.25); }}
        .divider {{ position: relative; text-align: center; margin-bottom: 16px; }}
        .divider::before {{ content: ""; position: absolute; top: 50%; left: 0; right: 0; border-top: 1px solid rgba(255,255,255,0.06); }}
        .divider span {{ position: relative; background: #0a0a0a; padding: 0 12px; font-size: 12px; color: rgba(255,255,255,0.3); }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Sign in to TONND</h1>
        <p class="sub">Authorize access to your health data.</p>
        {error_html}
        {google_section}
        <form method="POST">
            <input type="email" name="email" placeholder="Email" required autofocus>
            <input type="password" name="password" placeholder="Password" required>
            <input type="hidden" name="sid" value="{html.escape(sid)}">
            <input type="hidden" name="csrf" value="{html.escape(csrf)}">
            <button type="submit">Sign In</button>
        </form>
    </div>
</body>
</html>"""
