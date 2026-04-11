"""Tests for /api/v1/ public API endpoints — auth, scopes, data access, tokens."""

import uuid
from datetime import date, timedelta

import pytest

from src.models.db_models import FitnessMetric
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
    """Seed test data for a user."""
    uid = uuid.UUID(user_id)
    async with test_session_maker() as session:
        today = date.today()
        for i in range(5):
            d = today - timedelta(days=i)
            session.add(FitnessMetric(user_id=uid, date=d, metric_type="heart_rate", source="fitbit", data={"resting_heart_rate": 60 + i}))
            session.add(FitnessMetric(user_id=uid, date=d, metric_type="hrv", source="fitbit", data={"daily_rmssd": 30 + i}))
            session.add(FitnessMetric(user_id=uid, date=d, metric_type="sleep", source="fitbit", data={"total_minutes": 400 + i * 10, "efficiency": 85 + i}))
            session.add(FitnessMetric(user_id=uid, date=d, metric_type="weight", source="renpho", data={"weight_kg": 75.0 - i * 0.1}))
            session.add(FitnessMetric(user_id=uid, date=d, metric_type="activity", source="fitbit", data={"steps": 8000 + i * 100}))
        session.add(FitnessMetric(user_id=uid, date=today, metric_type="workout", source="hevy", data={"title": "Full Body", "total_volume_kg": 4500, "total_sets": 24}))
        session.add(FitnessMetric(user_id=uid, date=today, metric_type="spo2", source="fitbit", data={"avg": 96.5}))
        session.add(FitnessMetric(user_id=uid, date=today, metric_type="active_zone_minutes", source="fitbit", data={"total_minutes": 35}))
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

    async def test_metrics_requires_auth(self, client):
        r = await client.get("/api/v1/metrics")
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
        assert all("metric_type" in d for d in data["data"])

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
        assert r.json()["count"] == 1

    async def test_workouts_by_date(self, client):
        token = await register_and_login(client, "jwt-wdate@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        today = date.today().isoformat()
        r = await client.get(f"/api/v1/workouts/{today}", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    async def test_workouts_by_date_not_found(self, client):
        token = await register_and_login(client, "jwt-wnotfound@test.com")
        r = await client.get("/api/v1/workouts/2020-01-01", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404

    async def test_recovery_with_jwt(self, client):
        token = await register_and_login(client, "jwt-recovery@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/recovery", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["score"] is not None

    async def test_metrics_with_jwt(self, client):
        token = await register_and_login(client, "jwt-metrics@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/metrics", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["count"] > 0

    async def test_metrics_filter_by_type(self, client):
        token = await register_and_login(client, "jwt-mtype@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/metrics?metric_type=sleep", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert all(d["metric_type"] == "sleep" for d in r.json()["data"])

    async def test_vitals_by_type(self, client):
        token = await register_and_login(client, "jwt-vtype@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/vitals/hrv", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["metric_type"] == "hrv"

    async def test_vitals_unknown_type(self, client):
        token = await register_and_login(client, "jwt-vunk@test.com")
        r = await client.get("/api/v1/vitals/nonexistent", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404

    async def test_body_by_type(self, client):
        token = await register_and_login(client, "jwt-btype@test.com")
        user_id = await get_user_id(client, token)
        await seed_metrics(user_id)

        r = await client.get("/api/v1/body/weight", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["metric_type"] == "weight"

    async def test_body_unknown_type(self, client):
        token = await register_and_login(client, "jwt-bunk@test.com")
        r = await client.get("/api/v1/body/nonexistent", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404

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

    async def test_pat_metrics_scope_enforcement(self, client):
        jwt = await register_and_login(client, "pat-mscope@test.com")
        user_id = await get_user_id(client, jwt)
        await seed_metrics(user_id)

        create_r = await client.post("/api/v1/tokens", json={
            "name": "SleepOnly", "scopes": ["read:sleep"],
        }, headers={"Authorization": f"Bearer {jwt}"})
        pat = create_r.json()["token"]

        # /metrics with allowed type
        r = await client.get("/api/v1/metrics?metric_type=sleep", headers={"Authorization": f"Bearer {pat}"})
        assert r.status_code == 200

        # /metrics with denied type
        r = await client.get("/api/v1/metrics?metric_type=heart_rate", headers={"Authorization": f"Bearer {pat}"})
        assert r.status_code == 403


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
