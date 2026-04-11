import os
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Literal, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.router import router as api_v1_router
from src.database import engine, get_async_session
from src.middleware.audit import AuditMiddleware
from src.middleware.rate_limit import limiter
from src.middleware.security_headers import SecurityHeadersMiddleware
from src.models.db_models import Base, FitnessMetric, User
import src.models.api_models  # noqa: F401 — register APIToken + AuditLog with Base
from src.scheduler import daily_sync_all
from src.services.fitbit.client import (
    FitbitClient,
    RateLimitError,
    TokenExpiredError,
    exchange_code_for_tokens,
    get_authorization_url,
)
from src.services.fitbit.sync import disconnect_fitbit, ensure_valid_token
from src.services.sync_utils import upsert_metric
from src.services.hevy.client import validate_hevy_api_key
from src.services.hevy.sync import disconnect_hevy, sync_hevy_data
from src.services.renpho.client import RenphoAPIError, renpho_login
from src.services.renpho.sync import disconnect_renpho, sync_renpho_data
from src.services.token_encryption import decrypt_token, encrypt_token
from src.services.user_service import (
    JWT_SECRET,
    UserCreate,
    UserRead,
    UserUpdate,
    auth_backend,
    current_active_user,
    fastapi_users,
    google_oauth_client,
)
from src.utils.security import (
    generate_secure_state,
    validate_date_format,
    validate_secure_state,
)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start daily sync scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_sync_all, "cron", hour=6, minute=0, id="daily_sync_all")
    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(title="TONND", version="1.0.0", lifespan=lifespan)

# ─── Middleware (outermost first) ────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(SessionMiddleware, secret_key=JWT_SECRET)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list({FRONTEND_URL, FRONTEND_URL.replace("://www.", "://"), FRONTEND_URL.replace("://", "://www.")}),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ─── Public API v1 ───────────────────────────────────────────────────────────

app.include_router(api_v1_router)

# ─── Auth routes (fastapi-users) ─────────────────────────────────────────────

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

if google_oauth_client:
    from fastapi_users.router.oauth import generate_state_token

    @app.get("/auth/google/authorize", tags=["auth"])
    async def google_authorize(request: Request):
        authorize_redirect_url = str(request.url_for("google_callback"))
        state = generate_state_token({}, JWT_SECRET)
        request.session["oauth_state"] = state
        authorization_url = await google_oauth_client.get_authorization_url(
            authorize_redirect_url, state=state
        )
        return {"authorization_url": authorization_url}

    @app.get("/auth/google/callback", tags=["auth"])
    async def google_callback(
        request: Request,
        code: str,
        state: str,
        session: AsyncSession = Depends(get_async_session),
    ):
        from fastapi_users.router.oauth import decode_jwt

        # Validate state
        try:
            decode_jwt(state, JWT_SECRET, ["fastapi-users:oauth-state"])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid state")

        # Exchange code for Google tokens
        redirect_url = str(request.url_for("google_callback"))
        oauth2_token = await google_oauth_client.get_access_token(code, redirect_url)
        account_id, account_email = await google_oauth_client.get_id_email(
            oauth2_token["access_token"]
        )

        # Find or create user
        from src.services.user_service import get_user_manager, get_user_db

        async for user_db in get_user_db(session):
            async for user_manager in get_user_manager(user_db):
                user = await user_manager.oauth_callback(
                    "google",
                    oauth2_token["access_token"],
                    account_id,
                    account_email,
                    oauth2_token.get("expires_at"),
                    oauth2_token.get("refresh_token"),
                    request,
                    associate_by_email=True,
                )

        # Generate JWT
        from src.services.user_service import get_jwt_strategy

        strategy = get_jwt_strategy()
        jwt_token = await strategy.write_token(user)

        # Redirect to frontend with token
        return RedirectResponse(
            f"{FRONTEND_URL}/auth/callback?access_token={jwt_token}"
        )


# ─── Fitbit OAuth ────────────────────────────────────────────────────────────


@app.get("/auth/fitbit/init", tags=["fitbit"])
async def fitbit_init(
    request: Request,
    user: User = Depends(current_active_user),
):
    state = generate_secure_state(str(user.id))
    callback_url = str(request.url_for("fitbit_callback"))
    authorization_url = get_authorization_url(callback_url, state)
    return {"authorization_url": authorization_url, "state": state}


@app.get("/auth/fitbit/callback", tags=["fitbit"])
async def fitbit_callback(
    request: Request,
    code: str,
    state: str,
    session: AsyncSession = Depends(get_async_session),
):
    user_id, is_valid = validate_secure_state(state)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    callback_url = str(request.url_for("fitbit_callback"))
    tokens = await exchange_code_for_tokens(code, callback_url)

    stmt = select(User).where(User.id == uuid.UUID(user_id))
    result = await session.execute(stmt)
    user = result.unique().scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.fitbit_user_id = tokens.get("user_id")
    user.fitbit_access_token = encrypt_token(tokens["access_token"])
    user.fitbit_refresh_token = encrypt_token(tokens["refresh_token"])
    user.fitbit_token_expires = int(
        datetime.now(timezone.utc).timestamp()
    ) + tokens.get("expires_in", 3600)
    await session.commit()

    return RedirectResponse(
        f"{FRONTEND_URL}/auth/callback?success=true&fitbit=connected"
    )


# ─── Renpho OAuth ────────────────────────────────────────────────────────────


@app.post("/auth/renpho/connect", tags=["renpho"])
async def renpho_connect(
    request: Request,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    body = await request.json()
    email = body.get("email")
    password = body.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    try:
        renpho_login(email, password)
    except RenphoAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user.renpho_email = encrypt_token(email)
    user.renpho_session_key = encrypt_token(password)
    await session.commit()

    return {"connected": True, "message": "Renpho connected successfully"}


@app.delete("/auth/renpho/disconnect", tags=["renpho"])
async def renpho_disconnect(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    disconnect_renpho(user)
    await session.commit()
    return {"connected": False, "message": "Renpho disconnected"}


# ─── Hevy ────────────────────────────────────────────────────────────────────


@app.post("/auth/hevy/connect", tags=["hevy"])
async def hevy_connect(
    request: Request,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    body = await request.json()
    api_key = body.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key required")

    is_valid = await validate_hevy_api_key(api_key)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid Hevy API key. Make sure you have Hevy Pro.")

    user.hevy_api_key = encrypt_token(api_key)
    await session.commit()

    return {"connected": True, "message": "Hevy connected successfully"}


@app.delete("/auth/hevy/disconnect", tags=["hevy"])
async def hevy_disconnect(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    disconnect_hevy(user)
    await session.commit()
    return {"connected": False, "message": "Hevy disconnected"}


# ─── API routes ──────────────────────────────────────────────────────────────


@app.get("/api/user", tags=["api"])
async def get_user(user: User = Depends(current_active_user)):
    return {
        "user_id": str(user.id),
        "email": user.email,
        "fitbit_connected": user.fitbit_access_token is not None,
        "fitbit_user_id": user.fitbit_user_id,
        "renpho_connected": user.renpho_session_key is not None,
        "hevy_connected": user.hevy_api_key is not None,
        "last_sync": user.last_sync.isoformat() + "Z" if user.last_sync else None,
    }


@app.post("/api/sync", tags=["api"])
async def sync_all_sources(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    sync_date: Optional[str] = None,
    days: int = Query(default=1, ge=1, le=30),
    source: Optional[Literal["fitbit", "renpho", "hevy"]] = Query(default=None, description="Sync only this source"),
):
    synced_metrics = []
    errors = []

    base_date = (
        date.fromisoformat(sync_date)
        if sync_date and validate_date_format(sync_date)
        else date.today()
    )

    sync_fitbit = source in (None, "fitbit")
    sync_renpho = source in (None, "renpho")
    sync_hevy = source in (None, "hevy")

    # Sync Fitbit
    if sync_fitbit and user.fitbit_access_token:
        try:
            access_token = await ensure_valid_token(user)
            client = FitbitClient(access_token)

            for i in range(days):
                current_date = base_date - timedelta(days=i)
                date_str = current_date.isoformat()
                try:
                    result = await client.get_all_data_for_date(date_str)
                    for metric_type, metric_data in result["data"].items():
                        await upsert_metric(
                            session, user.id, current_date, metric_type, metric_data, source="fitbit"
                        )
                        synced_metrics.append(f"fitbit:{date_str}#{metric_type}")
                    errors.extend(result.get("errors", []))
                except RateLimitError:
                    errors.append(f"fitbit: rate limited at {date_str}")
                    break
                except Exception as e:
                    errors.append(f"fitbit:{date_str}: {e}")
        except TokenExpiredError:
            disconnect_fitbit(user)
            errors.append("fitbit: token expired, disconnected")

    # Sync Renpho
    if sync_renpho and user.renpho_session_key:
        for i in range(days):
            current_date = base_date - timedelta(days=i)
            renpho_result = await sync_renpho_data(session, user, current_date)
            synced_metrics.extend(renpho_result["synced_metrics"])
            errors.extend(renpho_result["errors"])

    # Sync Hevy (shared client + template cache across days)
    if sync_hevy and user.hevy_api_key:
        from src.services.hevy.client import get_client
        hevy_api_key = decrypt_token(user.hevy_api_key)
        hevy_client = get_client(hevy_api_key)
        hevy_template_cache: dict = {}
        for i in range(days):
            current_date = base_date - timedelta(days=i)
            hevy_result = await sync_hevy_data(session, user, current_date, hevy_client, hevy_template_cache)
            synced_metrics.extend(hevy_result["synced_metrics"])
            errors.extend(hevy_result["errors"])

    if not user.fitbit_access_token and not user.renpho_session_key and not user.hevy_api_key:
        raise HTTPException(status_code=400, detail="No data sources connected")

    user.last_sync = datetime.now(timezone.utc)
    await session.commit()

    return {
        "success": True,
        "message": f"Synced {len(synced_metrics)} metrics",
        "synced_metrics": synced_metrics,
        "errors": errors,
    }


@app.get("/api/data", tags=["api"])
async def get_data(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    days: int = Query(default=7, ge=1, le=90),
):
    start_date = date.today() - timedelta(days=days)

    stmt = (
        select(FitnessMetric)
        .where(
            FitnessMetric.user_id == user.id,
            FitnessMetric.date >= start_date,
        )
        .order_by(FitnessMetric.date.desc())
    )
    result = await session.execute(stmt)
    metrics = result.scalars().all()

    # Group by metric type
    by_type: dict[str, list[dict]] = {}
    for m in metrics:
        entry = {"date": m.date.isoformat(), "source": m.source, **m.data}
        by_type.setdefault(m.metric_type, []).append(entry)

    # Extract latest values
    def latest(metric_type: str) -> Optional[dict]:
        entries = by_type.get(metric_type)
        return entries[0] if entries else None

    # Recovery score (same formula as original)
    recovery_score = None
    latest_hrv = latest("hrv")
    latest_sleep = latest("sleep")
    latest_hr = latest("heart_rate")
    if latest_hrv and latest_sleep and latest_hr:
        hrv_val = latest_hrv.get("daily_rmssd")
        sleep_eff = latest_sleep.get("efficiency")
        rhr = latest_hr.get("resting_heart_rate")
        if hrv_val and sleep_eff and rhr:
            hrv_score = min(100, (hrv_val / 100) * 100)
            sleep_score = sleep_eff
            rhr_score = max(0, min(100, (100 - rhr) * 2))
            recovery_score = round(
                hrv_score * 0.4 + sleep_score * 0.35 + rhr_score * 0.25
            )

    return {
        "latest_weight": latest("weight"),
        "weight_trend": by_type.get("weight", []),
        "latest_sleep": latest("sleep"),
        "sleep_history": by_type.get("sleep", []),
        "today_activity": latest("activity"),
        "activity_history": by_type.get("activity", []),
        "today_heart_rate": latest("heart_rate"),
        "heart_rate_history": by_type.get("heart_rate", []),
        "latest_hrv": latest("hrv"),
        "hrv_history": by_type.get("hrv", []),
        "latest_spo2": latest("spo2"),
        "spo2_history": by_type.get("spo2", []),
        "latest_breathing_rate": latest("breathing_rate"),
        "breathing_rate_history": by_type.get("breathing_rate", []),
        "latest_vo2_max": latest("vo2_max"),
        "vo2_max_history": by_type.get("vo2_max", []),
        "latest_temperature": latest("temperature"),
        "temperature_history": by_type.get("temperature", []),
        "today_active_zone_minutes": latest("active_zone_minutes"),
        "active_zone_minutes_history": by_type.get("active_zone_minutes", []),
        "latest_workout": latest("workout"),
        "workout_history": by_type.get("workout", []),
        "recovery_score": recovery_score,
        "recovery_history": [],
        "last_sync": user.last_sync.isoformat() + "Z" if user.last_sync else None,
        "fitbit_connected": user.fitbit_access_token is not None,
        "renpho_connected": user.renpho_session_key is not None,
        "hevy_connected": user.hevy_api_key is not None,
    }


# ─── Health check ────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok"}
