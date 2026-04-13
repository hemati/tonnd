"""Tests for /api/v1/ public API endpoints — auth, scopes, data access, tokens."""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from src.models.body_models import BodyMeasurement
from src.models.fitbit_models import DailyActivity, DailySleep, DailyVitals
from src.models.hevy_models import Workout, WorkoutExercise
from src.services.token_service import create_token, hash_token

from tests.conftest import test_session_maker


async def register_and_login(client, email="apiv1@example.com", password="testpassword123") -> str:
    """Register a user and return JWT token."""
    await client.post("/auth/register", json={"email": email, "password": password})
    login = await client.post("/auth/jwt/login", data={
        "username": email, "password": password,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return login.json()["access_token"]


async def get_user_id(client, token: str) -> str:
    resp = await client.get("/api/user", headers={"Authorization": f"Bearer {token}"})
    return resp.json()["user_id"]


async def seed_metrics(user_id: str):
    """Seed test data for a user (typed tables only)."""
    uid = uuid.UUID(user_id)
    async with test_session_maker() as session:
        today = date.today()
        for i in range(5):
            d = today - timedelta(days=i)
            session.add(DailyVitals(user_id=uid, date=d, source="fitbit", resting_heart_rate=60.0 + i, daily_rmssd=30.0 + i, spo2_avg=96.5))
            session.add(DailySleep(user_id=uid, date=d, source="fitbit", external_id=f"sleep_{i}", total_minutes=400 + i * 10, efficiency=85 + i))
            session.add(BodyMeasurement(user_id=uid, date=d, source="renpho", measured_at=datetime(d.year, d.month, d.day, 8, 0, tzinfo=timezone.utc), weight_kg=75.0 - i * 0.1))
            session.add(DailyActivity(user_id=uid, date=d, source="fitbit", steps=8000 + i * 100))
        # Typed Hevy tables (used by /api/v1/workouts)
        w = Workout(user_id=uid, date=today, source="hevy", external_id="hevy_w1",
                    title="Full Body", total_volume_kg=4500, total_sets=24, total_reps=120)
        session.add(w)
        await session.flush()
        session.add(WorkoutExercise(workout_id=w.id, exercise_index=0,
                                     title="Bench Press", volume_kg=1500,
                                     primary_muscle="chest"))
        await session.commit()


# ─── Auth: Unauthenticated access ───────────────────────────────────────────


@pytest.mark.asyncio
class TestV1Unauthenticated:
    async def test_vitals_requires_auth(self, client):
        r = await client.get("/api/v1/vitals")
        assert r.status_code == 401

    async def test_tokens_requires_auth(self, client):
        r = await client.get("/api/v1/tokens")
        assert r.status_code == 401

    async def test_audit_requires_auth(self, client):
        r = await client.get("/api/v1/audit")
        assert r.status_code == 401



# ─── Auth: JWT access ────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestV1JWTAccess:
    async def test_vitals_with_jwt(self, client):
        token = await register_and_login(client, "jwt-vitals@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/vitals", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0
        assert all("resting_heart_rate" in d for d in data["data"])

    async def test_sleep_with_jwt(self, client):
        token = await register_and_login(client, "jwt-sleep@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/sleep", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["count"] == 5

    async def test_body_with_jwt(self, client):
        token = await register_and_login(client, "jwt-body@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/body", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["count"] == 5

    async def test_activity_with_jwt(self, client):
        token = await register_and_login(client, "jwt-activity@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/activity", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    async def test_workouts_with_jwt(self, client):
        token = await register_and_login(client, "jwt-workouts@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/workouts", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 1
        assert data["data"][0]["title"] == "Full Body"
        assert "exercises" in data["data"][0]
        assert len(data["data"][0]["exercises"]) == 1

    async def test_workout_by_external_id(self, client):
        token = await register_and_login(client, "jwt-wdate@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/workouts/hevy_w1", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["title"] == "Full Body"
        assert len(r.json()["exercises"]) == 1

    async def test_workout_by_external_id_not_found(self, client):
        token = await register_and_login(client, "jwt-wnotfound@test.com")
        r = await client.get("/api/v1/workouts/nonexistent", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404

    async def test_recovery_with_jwt(self, client):
        token = await register_and_login(client, "jwt-recovery@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/recovery", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["score"] is not None

    async def test_query_params(self, client):
        token = await register_and_login(client, "jwt-params@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        start = (date.today() - timedelta(days=2)).isoformat()
        r = await client.get(
            f"/api/v1/vitals?start_date={start}&limit=2&order=asc&source=fitbit",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["count"] <= 2


# ─── Token Management ────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestV1TokenManagement:
    async def test_create_token(self, client):
        jwt = await register_and_login(client, "token-create@test.com")
        r = await client.post("/api/v1/tokens", json={
            "name": "Test Token",
            "scopes": ["read:all"],
        }, headers={"Authorization": f"Bearer {jwt}"})

        assert r.status_code == 201
        data = r.json()
        assert data["token"].startswith("tonnd_")
        assert data["name"] == "Test Token"
        assert data["scopes"] == ["read:all"]

    async def test_list_tokens(self, client):
        jwt = await register_and_login(client, "token-list@test.com")
        await client.post("/api/v1/tokens", json={"name": "T1", "scopes": ["read:all"]}, headers={"Authorization": f"Bearer {jwt}"})
        await client.post("/api/v1/tokens", json={"name": "T2", "scopes": ["read:vitals"]}, headers={"Authorization": f"Bearer {jwt}"})

        r = await client.get("/api/v1/tokens", headers={"Authorization": f"Bearer {jwt}"})
        assert r.status_code == 200
        assert len(r.json()) == 2

    async def test_revoke_token(self, client):
        jwt = await register_and_login(client, "token-revoke@test.com")
        create_r = await client.post("/api/v1/tokens", json={"name": "ToRevoke", "scopes": ["read:all"]}, headers={"Authorization": f"Bearer {jwt}"})
        token_id = create_r.json()["id"]

        r = await client.delete(f"/api/v1/tokens/{token_id}", headers={"Authorization": f"Bearer {jwt}"})
        assert r.status_code == 204

    async def test_revoke_nonexistent(self, client):
        jwt = await register_and_login(client, "token-revnon@test.com")
        r = await client.delete(f"/api/v1/tokens/{uuid.uuid4()}", headers={"Authorization": f"Bearer {jwt}"})
        assert r.status_code == 404

    async def test_create_invalid_scopes(self, client):
        jwt = await register_and_login(client, "token-badscope@test.com")
        r = await client.post("/api/v1/tokens", json={
            "name": "Bad Scope",
            "scopes": ["write:everything"],
        }, headers={"Authorization": f"Bearer {jwt}"})
        assert r.status_code == 400

    async def test_create_invalid_name(self, client):
        jwt = await register_and_login(client, "token-badname@test.com")
        r = await client.post("/api/v1/tokens", json={
            "name": "<script>alert(1)</script>",
            "scopes": ["read:all"],
        }, headers={"Authorization": f"Bearer {jwt}"})
        assert r.status_code == 422  # Pydantic validation

    async def test_pat_auth_works(self, client):
        jwt = await register_and_login(client, "pat-auth@test.com")
        user_id = await get_user_id(client, jwt)
        await seed_metrics(user_id)

        create_r = await client.post("/api/v1/tokens", json={
            "name": "PAT Test", "scopes": ["read:all"],
        }, headers={"Authorization": f"Bearer {jwt}"})
        pat = create_r.json()["token"]

        r = await client.get("/api/v1/vitals", headers={"Authorization": f"Bearer {pat}"})
        assert r.status_code == 200
        assert r.json()["count"] > 0

    async def test_pat_scope_enforcement(self, client):
        jwt = await register_and_login(client, "pat-scope@test.com")
        create_r = await client.post("/api/v1/tokens", json={
            "name": "Vitals Only", "scopes": ["read:vitals"],
        }, headers={"Authorization": f"Bearer {jwt}"})
        pat = create_r.json()["token"]

        # Allowed scope
        r = await client.get("/api/v1/vitals", headers={"Authorization": f"Bearer {pat}"})
        assert r.status_code == 200

        # Denied scope
        r = await client.get("/api/v1/sleep", headers={"Authorization": f"Bearer {pat}"})
        assert r.status_code == 403

    async def test_revoked_pat_rejected(self, client):
        jwt = await register_and_login(client, "pat-revoked@test.com")
        create_r = await client.post("/api/v1/tokens", json={
            "name": "WillRevoke", "scopes": ["read:all"],
        }, headers={"Authorization": f"Bearer {jwt}"})
        pat = create_r.json()["token"]
        token_id = create_r.json()["id"]

        await client.delete(f"/api/v1/tokens/{token_id}", headers={"Authorization": f"Bearer {jwt}"})

        r = await client.get("/api/v1/vitals", headers={"Authorization": f"Bearer {pat}"})
        assert r.status_code == 401

    async def test_invalid_pat_rejected(self, client):
        r = await client.get("/api/v1/vitals", headers={"Authorization": "Bearer tonnd_invalid_token_abc123"})
        assert r.status_code == 401

    async def test_pat_cannot_manage_tokens(self, client):
        jwt = await register_and_login(client, "pat-notokens@test.com")
        create_r = await client.post("/api/v1/tokens", json={
            "name": "NoPerm", "scopes": ["read:all"],
        }, headers={"Authorization": f"Bearer {jwt}"})
        pat = create_r.json()["token"]

        # PAT should not be able to list/create tokens (those use current_active_user = JWT only)
        r = await client.get("/api/v1/tokens", headers={"Authorization": f"Bearer {pat}"})
        assert r.status_code == 401



# ─── Audit ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestV1Audit:
    async def test_audit_empty(self, client):
        jwt = await register_and_login(client, "audit@test.com")
        r = await client.get("/api/v1/audit", headers={"Authorization": f"Bearer {jwt}"})
        assert r.status_code == 200
        assert r.json()["count"] == 0


# ─── Data isolation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestV1DataIsolation:
    async def test_user_cannot_see_other_users_data(self, client):
        jwt1 = await register_and_login(client, "user1@test.com")
        jwt2 = await register_and_login(client, "user2@test.com")
        uid1 = await get_user_id(client, jwt1)
        await seed_metrics(uid1)

        # User2 should see no data
        r = await client.get("/api/v1/vitals", headers={"Authorization": f"Bearer {jwt2}"})
        assert r.status_code == 200
        assert r.json()["count"] == 0
