"""Tests for FatSecret OAuth1 client + food_entries normalization."""

import math
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.services.fatsecret import client as fs


# ─── helpers ───────────────────────────────────────────────────────────────

def _mock_http(*, status: int = 200, text: str = "", json_data=None) -> MagicMock:
    """Build an httpx.AsyncClient mock with a single GET response."""
    mock = MagicMock(spec=httpx.AsyncClient)
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    if json_data is not None:
        resp.json = MagicMock(return_value=json_data)
    mock.get = AsyncMock(return_value=resp)
    return mock


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("FATSECRET_CONSUMER_KEY", "test_key")
    monkeypatch.setenv("FATSECRET_CONSUMER_SECRET", "test_secret")


# ─── credential / auth helpers ─────────────────────────────────────────────

class TestCredentials:
    def test_raises_without_env(self, monkeypatch):
        monkeypatch.delenv("FATSECRET_CONSUMER_KEY", raising=False)
        monkeypatch.delenv("FATSECRET_CONSUMER_SECRET", raising=False)
        with pytest.raises(RuntimeError, match="FATSECRET_CONSUMER_KEY"):
            fs.get_credentials()

    def test_returns_pair(self):
        assert fs.get_credentials() == ("test_key", "test_secret")


class TestAuthorizeURL:
    def test_format(self):
        url = fs.authorize_url("abc123")
        assert url == "https://www.fatsecret.com/oauth/authorize?oauth_token=abc123"


class TestSign:
    def test_sign_attaches_oauth_params_to_query(self):
        signed = fs._sign(
            "https://example.com/api",
            consumer_key="ck", consumer_secret="cs",
            extra_params={"method": "food_entries.get", "format": "json"},
        )
        assert "oauth_signature=" in signed
        assert "oauth_consumer_key=ck" in signed
        assert "method=food_entries.get" in signed
        assert "format=json" in signed


# ─── form parsing ─────────────────────────────────────────────────────────

class TestParseForm:
    def test_basic(self):
        out = fs._parse_form("oauth_token=abc&oauth_token_secret=def")
        assert out == {"oauth_token": "abc", "oauth_token_secret": "def"}

    def test_with_callback_confirmed(self):
        out = fs._parse_form("oauth_token=t&oauth_token_secret=s&oauth_callback_confirmed=true")
        assert out["oauth_token"] == "t"


# ─── request_token / access_token ──────────────────────────────────────────

@pytest.mark.asyncio
class TestFetchRequestToken:
    async def test_success(self):
        http = _mock_http(text="oauth_token=req_t&oauth_token_secret=req_s")
        out = await fs.fetch_request_token("https://app/cb", http)
        assert out["oauth_token"] == "req_t"
        assert out["oauth_token_secret"] == "req_s"

    async def test_http_error(self):
        http = _mock_http(status=500, text="boom")
        with pytest.raises(fs.FatSecretAPIError, match="request_token failed"):
            await fs.fetch_request_token("https://app/cb", http)

    async def test_missing_fields(self):
        http = _mock_http(text="something_else=1")
        with pytest.raises(fs.FatSecretAPIError, match="missing fields"):
            await fs.fetch_request_token("https://app/cb", http)


@pytest.mark.asyncio
class TestFetchAccessToken:
    async def test_success(self):
        http = _mock_http(text="oauth_token=acc_t&oauth_token_secret=acc_s")
        out = await fs.fetch_access_token("rt", "rs", "verifier", http)
        assert out["oauth_token"] == "acc_t"
        assert out["oauth_token_secret"] == "acc_s"

    async def test_401_raises_auth_error(self):
        http = _mock_http(status=401, text="invalid")
        with pytest.raises(fs.FatSecretAuthError):
            await fs.fetch_access_token("rt", "rs", "verifier", http)


# ─── date encoding ─────────────────────────────────────────────────────────

class TestDateInt:
    def test_epoch(self):
        assert fs._date_to_int(date(1970, 1, 1)) == 0

    def test_known_value(self):
        assert fs._date_to_int(date(2026, 5, 9)) == 20582


# ─── numeric sanitization ─────────────────────────────────────────────────

class TestCleanNumeric:
    def test_passes_normal(self):
        assert fs._clean_numeric("12.5") == 12.5
        assert fs._clean_numeric(0) == 0.0

    def test_drops_nan(self):
        assert fs._clean_numeric(math.nan) is None

    def test_drops_inf(self):
        assert fs._clean_numeric(math.inf) is None
        assert fs._clean_numeric(-math.inf) is None

    def test_drops_negative(self):
        assert fs._clean_numeric(-5) is None

    def test_drops_unparseable(self):
        assert fs._clean_numeric("abc") is None
        assert fs._clean_numeric(None) is None


# ─── response shape extraction ─────────────────────────────────────────────

class TestExtractEntries:
    def test_empty_string_response(self):
        assert fs._extract_entries({"food_entries": ""}) == []

    def test_single_entry(self):
        out = fs._extract_entries({"food_entries": {"food_entry": {"food_entry_id": "1"}}})
        assert out == [{"food_entry_id": "1"}]

    def test_list_of_entries(self):
        out = fs._extract_entries({
            "food_entries": {"food_entry": [{"food_entry_id": "1"}, {"food_entry_id": "2"}]}
        })
        assert len(out) == 2

    def test_missing_top_level(self):
        assert fs._extract_entries({}) == []

    def test_null_inner(self):
        assert fs._extract_entries({"food_entries": {"food_entry": None}}) == []


# ─── entry normalization ──────────────────────────────────────────────────

class TestNormalizeEntry:
    def test_field_remapping(self):
        raw = {
            "food_entry_id": "12345", "food_entry_name": "Apple",
            "meal": "Breakfast", "calories": "95", "carbohydrate": "25",
            "fat": "0.3", "protein": "0.5", "fiber": "4.4", "sugar": "19",
            "saturated_fat": "0.05", "polyunsaturated_fat": "0.1", "monounsaturated_fat": "0.01",
            "cholesterol": "0", "sodium": "2", "calcium": "11", "iron": "0.2",
            "potassium": "195", "vitamin_a": "98", "vitamin_c": "8.4",
        }
        out = fs._normalize_entry(raw, date(2026, 5, 9))
        assert out["external_id"] == "12345"
        assert out["food_entry_name"] == "Apple"
        assert out["meal"] == "Breakfast"
        assert out["calories"] == 95.0
        assert out["carbs_g"] == 25.0
        assert out["fat_g"] == 0.3
        assert out["protein_g"] == 0.5
        assert out["fiber_g"] == 4.4
        assert out["sugar_g"] == 19.0
        assert out["saturated_fat_g"] == 0.05
        assert out["polyunsaturated_fat_g"] == 0.1
        assert out["monounsaturated_fat_g"] == 0.01
        assert out["cholesterol_mg"] == 0.0
        assert out["sodium_mg"] == 2.0
        assert out["vitamin_a_iu"] == 98.0
        assert out["vitamin_c_mg"] == 8.4
        assert out["date"] == date(2026, 5, 9)

    def test_drops_negatives_and_nans(self):
        raw = {
            "food_entry_id": "1", "food_entry_name": "Bad",
            "calories": "-50", "fat": "nan",
        }
        out = fs._normalize_entry(raw, date(2026, 5, 9))
        assert "calories" not in out
        assert "fat_g" not in out

    def test_returns_none_without_id_or_name(self):
        assert fs._normalize_entry({"food_entry_name": "x"}, date(2026, 5, 9)) is None
        assert fs._normalize_entry({"food_entry_id": "1"}, date(2026, 5, 9)) is None

    def test_localized_meal_passes_through(self):
        raw = {"food_entry_id": "1", "food_entry_name": "Apfel", "meal": "Frühstück"}
        out = fs._normalize_entry(raw, date(2026, 5, 9))
        assert out["meal"] == "Frühstück"

    def test_long_name_truncated(self):
        raw = {"food_entry_id": "1", "food_entry_name": "x" * 500}
        out = fs._normalize_entry(raw, date(2026, 5, 9))
        assert len(out["food_entry_name"]) == 256


# ─── end-to-end fetch ─────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestGetFoodEntriesForDate:
    async def test_normalizes_payload(self):
        http = _mock_http(json_data={
            "food_entries": {"food_entry": [
                {"food_entry_id": "1", "food_entry_name": "Apple",
                 "meal": "Breakfast", "calories": "95", "carbohydrate": "25"},
                {"food_entry_id": "2", "food_entry_name": "Coffee",
                 "meal": "Breakfast", "calories": "5"},
            ]}
        })
        out = await fs.get_food_entries_for_date("rt", "rs", date(2026, 5, 9), http)
        assert len(out) == 2
        assert out[0]["external_id"] == "1"
        assert out[0]["calories"] == 95.0
        assert out[0]["carbs_g"] == 25.0
        assert out[1]["external_id"] == "2"

    async def test_empty_day(self):
        http = _mock_http(json_data={"food_entries": ""})
        out = await fs.get_food_entries_for_date("rt", "rs", date(2026, 5, 9), http)
        assert out == []

    async def test_401_raises_auth_error(self):
        http = _mock_http(status=401, text="rejected")
        with pytest.raises(fs.FatSecretAuthError):
            await fs.get_food_entries_for_date("rt", "rs", date(2026, 5, 9), http)

    async def test_api_error_payload_invalid_token(self):
        http = _mock_http(json_data={"error": {"code": 5, "message": "Invalid signature"}})
        with pytest.raises(fs.FatSecretAuthError):
            await fs.get_food_entries_for_date("rt", "rs", date(2026, 5, 9), http)

    async def test_api_error_payload_other(self):
        http = _mock_http(json_data={"error": {"code": 1, "message": "Internal error"}})
        with pytest.raises(fs.FatSecretAPIError):
            await fs.get_food_entries_for_date("rt", "rs", date(2026, 5, 9), http)

    async def test_skips_malformed_entries(self):
        http = _mock_http(json_data={
            "food_entries": {"food_entry": [
                {"food_entry_id": "1", "food_entry_name": "OK"},
                {"food_entry_name": "missing id"},
                "not a dict",
            ]}
        })
        out = await fs.get_food_entries_for_date("rt", "rs", date(2026, 5, 9), http)
        assert len(out) == 1
        assert out[0]["external_id"] == "1"
