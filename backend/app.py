import os
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import engine, get_async_session
from src.models.db_models import Base, FitnessMetric, User
from src.scheduler import daily_sync_all
from src.services.fitbit_client import (
    FitbitClient,
    RateLimitError,
    TokenExpiredError,
    exchange_code_for_tokens,
    get_authorization_url,
)
from src.services.fitbit_sync import (
    disconnect_fitbit,
    ensure_valid_token,
    upsert_metric,
)
from src.services.token_encryption import encrypt_token
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
    scheduler.add_job(daily_sync_all, "cron", hour=6, minute=0, id="daily_fitbit_sync")
    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(title="TONND", version="1.0.0", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=JWT_SECRET)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    user = result.scalar_one_or_none()
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


# ─── API routes ──────────────────────────────────────────────────────────────


@app.get("/api/user", tags=["api"])
async def get_user(user: User = Depends(current_active_user)):
    return {
        "user_id": str(user.id),
        "email": user.email,
        "fitbit_connected": user.fitbit_access_token is not None,
        "fitbit_user_id": user.fitbit_user_id,
        "last_sync": user.last_sync.isoformat() + "Z" if user.last_sync else None,
    }


@app.post("/api/sync", tags=["api"])
async def sync_fitbit(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    sync_date: Optional[str] = None,
    days: int = Query(default=1, ge=1, le=30),
):
    if not user.fitbit_access_token:
        raise HTTPException(status_code=400, detail="Fitbit not connected")

    access_token = await ensure_valid_token(user)
    client = FitbitClient(access_token)
    synced_metrics = []
    errors = []

    base_date = (
        date.fromisoformat(sync_date)
        if sync_date and validate_date_format(sync_date)
        else date.today()
    )

    for i in range(days):
        current_date = base_date - timedelta(days=i)
        date_str = current_date.isoformat()
        try:
            result = await client.get_all_data_for_date(date_str)
            for metric_type, metric_data in result["data"].items():
                await upsert_metric(
                    session, user.id, current_date, metric_type, metric_data
                )
                synced_metrics.append(f"{date_str}#{metric_type}")
            errors.extend(result.get("errors", []))
        except TokenExpiredError:
            disconnect_fitbit(user)
            await session.commit()
            raise HTTPException(
                status_code=401, detail="Fitbit token expired. Please reconnect."
            )
        except RateLimitError:
            errors.append(f"Rate limited at {date_str}")
            break
        except Exception as e:
            errors.append(f"{date_str}: {e}")

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
        entry = {"date": m.date.isoformat(), **m.data}
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
        "recovery_score": recovery_score,
        "recovery_history": [],
        "last_sync": user.last_sync.isoformat() + "Z" if user.last_sync else None,
        "fitbit_connected": user.fitbit_access_token is not None,
    }


# ─── Health check ────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok"}
