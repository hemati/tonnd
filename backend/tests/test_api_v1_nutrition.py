"""Tests for /api/v1/nutrition/daily and /api/v1/nutrition/entries."""

import uuid
from datetime import date, timedelta

import pytest

from src.models.fitbit_models import DailyNutrition
from src.models.food_models import FoodEntry
from src.services.token_service import create_token

from tests.conftest import test_session_maker


async def _register_and_login(client, email="nut@example.com") -> str:
    await client.post("/auth/register", json={"email": email, "password": "testpassword123"})
    login = await client.post("/auth/jwt/login", data={
        "username": email, "password": "testpassword123",
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return login.json()["access_token"]


async def _user_id(client, jwt: str) -> str:
    r = await client.get("/api/user", headers={"Authorization": f"Bearer {jwt}"})
    return r.json()["user_id"]


def _auth(jwt: str) -> dict:
    return {"Authorization": f"Bearer {jwt}"}


async def _seed(user_id: str):
    uid = uuid.UUID(user_id)
    today = date.today()
    async with test_session_maker() as session:
        for i in range(3):
            d = today - timedelta(days=i)
            session.add(DailyNutrition(
                user_id=uid, date=d, source="fatsecret",
                calories_in=2000 - i * 50, carbs_g=200.0, protein_g=120.0, fat_g=70.0,
            ))
        for i, meal in enumerate(["Breakfast", "Lunch", "Dinner"]):
            session.add(FoodEntry(
                user_id=uid, external_id=f"fe_{i}", source="fatsecret",
                date=today, food_entry_name=f"Item {i}",
                meal=meal, calories=500.0 + i * 100, carbs_g=60.0,
            ))
        await session.commit()


# ─── Auth ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestUnauthenticated:
    async def test_daily_requires_auth(self, client):
        r = await client.get("/api/v1/nutrition/daily")
        assert r.status_code == 401

    async def test_entries_requires_auth(self, client):
        r = await client.get("/api/v1/nutrition/entries")
        assert r.status_code == 401


# ─── JWT access ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestJWTAccess:
    async def test_daily_returns_seeded_rows(self, client):
        jwt = await _register_and_login(client, "jwt-daily@test.com")
        uid = await _user_id(client, jwt)
        await _seed(uid)
        r = await client.get("/api/v1/nutrition/daily", headers=_auth(jwt))
        assert r.status_code == 200
        body = r.json()
        assert body["count"] == 3
        assert all("calories_in" in d for d in body["data"])

    async def test_entries_returns_seeded_rows(self, client):
        jwt = await _register_and_login(client, "jwt-entries@test.com")
        uid = await _user_id(client, jwt)
        await _seed(uid)
        r = await client.get("/api/v1/nutrition/entries", headers=_auth(jwt))
        assert r.status_code == 200
        body = r.json()
        assert body["count"] == 3
        assert all(d["source"] == "fatsecret" for d in body["data"])

    async def test_meal_filter(self, client):
        jwt = await _register_and_login(client, "jwt-meal@test.com")
        uid = await _user_id(client, jwt)
        await _seed(uid)
        r = await client.get("/api/v1/nutrition/entries?meal=Breakfast", headers=_auth(jwt))
        assert r.status_code == 200
        body = r.json()
        assert body["count"] == 1
        assert body["data"][0]["meal"] == "Breakfast"

    async def test_date_range_filter_on_daily(self, client):
        jwt = await _register_and_login(client, "jwt-range@test.com")
        uid = await _user_id(client, jwt)
        await _seed(uid)
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        # Single-day range should hit exactly one row.
        r = await client.get(
            f"/api/v1/nutrition/daily?start_date={yesterday}&end_date={yesterday}",
            headers=_auth(jwt),
        )
        assert r.status_code == 200
        assert r.json()["count"] == 1

    async def test_pagination_on_entries(self, client):
        jwt = await _register_and_login(client, "jwt-page@test.com")
        uid = await _user_id(client, jwt)
        await _seed(uid)  # seeds 3 entries
        r1 = await client.get("/api/v1/nutrition/entries?limit=2", headers=_auth(jwt))
        r2 = await client.get("/api/v1/nutrition/entries?limit=2&offset=2", headers=_auth(jwt))
        assert r1.json()["count"] == 2
        assert r2.json()["count"] == 1

    async def test_excludes_other_users(self, client):
        jwt_a = await _register_and_login(client, "user-a@test.com")
        jwt_b = await _register_and_login(client, "user-b@test.com")
        uid_a = await _user_id(client, jwt_a)
        await _seed(uid_a)

        # B has no data; should see empty.
        r = await client.get("/api/v1/nutrition/daily", headers=_auth(jwt_b))
        assert r.json()["count"] == 0


# ─── PAT scope enforcement ────────────────────────────────────────────────


@pytest.mark.asyncio
class TestPATScopes:
    async def test_token_with_read_nutrition_works(self, client):
        jwt = await _register_and_login(client, "pat-ok@test.com")
        uid = await _user_id(client, jwt)
        await _seed(uid)
        async with test_session_maker() as session:
            _tok, raw = await create_token(
                session, uuid.UUID(uid),
                name="nut-read", scopes=["read:nutrition"],
            )
            await session.commit()

        r = await client.get(
            "/api/v1/nutrition/daily", headers={"Authorization": f"Bearer {raw}"},
        )
        assert r.status_code == 200
        assert r.json()["count"] == 3

    async def test_token_without_read_nutrition_rejected(self, client):
        jwt = await _register_and_login(client, "pat-no@test.com")
        uid = await _user_id(client, jwt)
        await _seed(uid)
        async with test_session_maker() as session:
            _tok, raw = await create_token(
                session, uuid.UUID(uid),
                name="vitals-only", scopes=["read:vitals"],
            )
            await session.commit()
        r = await client.get(
            "/api/v1/nutrition/entries", headers={"Authorization": f"Bearer {raw}"},
        )
        assert r.status_code == 403

    async def test_read_all_includes_nutrition(self, client):
        jwt = await _register_and_login(client, "pat-all@test.com")
        uid = await _user_id(client, jwt)
        await _seed(uid)
        async with test_session_maker() as session:
            _tok, raw = await create_token(
                session, uuid.UUID(uid),
                name="all-scope", scopes=["read:all"],
            )
            await session.commit()
        r = await client.get(
            "/api/v1/nutrition/daily", headers={"Authorization": f"Bearer {raw}"},
        )
        assert r.status_code == 200
