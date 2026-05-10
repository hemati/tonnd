"""Tests for the new FatSecret MCP tools (both servers)."""

import asyncio
import uuid
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from src.models.fitbit_models import DailyNutrition
from src.models.food_models import FoodEntry

from tests.conftest import test_session_maker


# ─── Both servers register the tools ──────────────────────────────────────


def test_remote_server_registers_both_tools():
    from src.mcp.remote_server import mcp
    names = sorted(t.name for t in asyncio.run(mcp.list_tools()))
    assert "get_nutrition_daily" in names
    assert "get_food_entries" in names


def test_local_server_registers_both_tools():
    import os
    os.environ["TONND_API_TOKEN"] = "tonnd_test"
    import importlib
    import mcp_server
    importlib.reload(mcp_server)
    names = sorted(t.name for t in asyncio.run(mcp_server.mcp.list_tools()))
    assert "get_nutrition_daily" in names
    assert "get_food_entries" in names


# ─── Remote server (DB-direct) — exercises the actual query path ──────────


async def _seed(uid: uuid.UUID):
    """Async helper to seed nutrition data."""
    async with test_session_maker() as session:
        today = date.today()
        for i in range(3):
            d = today - timedelta(days=i)
            session.add(DailyNutrition(
                user_id=uid, date=d, source="fatsecret",
                calories_in=2000 - i * 50, carbs_g=200.0,
            ))
        for i, meal in enumerate(["Breakfast", "Lunch", "Dinner"]):
            session.add(FoodEntry(
                user_id=uid, external_id=f"fe_{i}", source="fatsecret",
                date=today, food_entry_name=f"Item {i}",
                meal=meal, calories=500.0,
            ))
        await session.commit()


class _FakeToken:
    """Stand-in for fastmcp's access_token object."""
    def __init__(self, user_id: uuid.UUID, scopes: list[str]):
        self.claims = {"sub": str(user_id)}
        self.scopes = scopes


@pytest.mark.asyncio
class TestRemoteNutritionDaily:
    async def test_returns_seeded_rows(self):
        from src.mcp import remote_server
        uid = uuid.uuid4()
        await _seed(uid)
        with patch.object(
            remote_server, "get_access_token",
            return_value=_FakeToken(uid, ["read:nutrition"]),
        ), patch.object(remote_server, "async_session_maker", test_session_maker):
            result = await remote_server.get_nutrition_daily()
        assert result["count"] == 3
        assert all("calories_in" in d for d in result["data"])

    async def test_requires_read_nutrition_scope(self):
        from src.mcp import remote_server
        uid = uuid.uuid4()
        await _seed(uid)
        with patch.object(
            remote_server, "get_access_token",
            return_value=_FakeToken(uid, ["read:vitals"]),
        ):
            with pytest.raises(ValueError, match="read:nutrition"):
                await remote_server.get_nutrition_daily()


@pytest.mark.asyncio
class TestRemoteFoodEntries:
    async def test_returns_seeded_rows(self):
        from src.mcp import remote_server
        uid = uuid.uuid4()
        await _seed(uid)
        with patch.object(
            remote_server, "get_access_token",
            return_value=_FakeToken(uid, ["read:nutrition"]),
        ), patch.object(remote_server, "async_session_maker", test_session_maker):
            result = await remote_server.get_food_entries()
        assert result["count"] == 3
        assert all(d["source"] == "fatsecret" for d in result["data"])

    async def test_meal_filter(self):
        from src.mcp import remote_server
        uid = uuid.uuid4()
        await _seed(uid)
        with patch.object(
            remote_server, "get_access_token",
            return_value=_FakeToken(uid, ["read:nutrition"]),
        ), patch.object(remote_server, "async_session_maker", test_session_maker):
            result = await remote_server.get_food_entries(meal="Lunch")
        assert result["count"] == 1
        assert result["data"][0]["meal"] == "Lunch"

    async def test_requires_read_nutrition_scope(self):
        from src.mcp import remote_server
        uid = uuid.uuid4()
        await _seed(uid)
        with patch.object(
            remote_server, "get_access_token",
            return_value=_FakeToken(uid, ["read:body"]),
        ):
            with pytest.raises(ValueError, match="read:nutrition"):
                await remote_server.get_food_entries()
