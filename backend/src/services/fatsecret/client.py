"""FatSecret OAuth 1.0a client + food diary fetcher.

OAuth1 (3-legged) is required because FatSecret's OAuth2 client_credentials
flow can only read generic data, not the user's food diary. We sign requests
with HMAC-SHA1 via oauthlib and ship them through httpx.AsyncClient.
"""

import logging
import math
import os
from datetime import date as date_type
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs

import httpx
from oauthlib.oauth1 import SIGNATURE_HMAC_SHA1, SIGNATURE_TYPE_QUERY, Client as OAuth1Client

from src.utils.safe_parse import safe_float

logger = logging.getLogger(__name__)

REQUEST_TOKEN_URL = "https://authentication.fatsecret.com/oauth/request_token"
AUTHORIZE_URL = "https://www.fatsecret.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://authentication.fatsecret.com/oauth/access_token"
REST_URL = "https://platform.fatsecret.com/rest/server.api"

# Day-since-epoch encoding the FatSecret API expects on `food_entries.get`.
_EPOCH = date_type(1970, 1, 1)

# Map FatSecret raw field name → our column name. Pass-through for keys that
# already match (calories, meal, food_entry_name, etc.).
_FIELD_MAP = {
    "carbohydrate": "carbs_g",
    "fat": "fat_g",
    "protein": "protein_g",
    "fiber": "fiber_g",
    "sugar": "sugar_g",
    "saturated_fat": "saturated_fat_g",
    "polyunsaturated_fat": "polyunsaturated_fat_g",
    "monounsaturated_fat": "monounsaturated_fat_g",
    "cholesterol": "cholesterol_mg",
    "sodium": "sodium_mg",
    "calcium": "calcium_mg",
    "iron": "iron_mg",
    "potassium": "potassium_mg",
    "vitamin_a": "vitamin_a_iu",
    "vitamin_c": "vitamin_c_mg",
}

# Numeric fields we coerce + sanity-check (drop NaN/inf, clamp negatives to None).
_NUMERIC_FIELDS = {
    "number_of_units", "calories",
    "carbs_g", "fat_g", "protein_g", "fiber_g", "sugar_g",
    "saturated_fat_g", "polyunsaturated_fat_g", "monounsaturated_fat_g",
    "cholesterol_mg", "sodium_mg", "calcium_mg", "iron_mg", "potassium_mg",
    "vitamin_a_iu", "vitamin_c_mg",
}


class FatSecretAPIError(Exception):
    pass


class FatSecretAuthError(FatSecretAPIError):
    """Raised on 401/invalid-token from FatSecret — caller should disconnect."""


def get_credentials() -> tuple[str, str]:
    key = os.environ.get("FATSECRET_CONSUMER_KEY", "")
    secret = os.environ.get("FATSECRET_CONSUMER_SECRET", "")
    if not key or not secret:
        raise RuntimeError(
            "FATSECRET_CONSUMER_KEY and FATSECRET_CONSUMER_SECRET must be set."
        )
    return key, secret


def _sign(
    url: str,
    *,
    consumer_key: str,
    consumer_secret: str,
    resource_owner_key: str | None = None,
    resource_owner_secret: str | None = None,
    extra_params: dict | None = None,
) -> str:
    """Sign an OAuth1 GET request and return the fully-qualified, signed URL.

    Signature mode: HMAC-SHA1, query-string (FatSecret accepts and prefers
    query-string signing for REST endpoints).
    """
    client = OAuth1Client(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        signature_method=SIGNATURE_HMAC_SHA1,
        signature_type=SIGNATURE_TYPE_QUERY,
        callback_uri=extra_params.get("oauth_callback") if extra_params else None,
    )
    if extra_params:
        # Build URL with non-OAuth params first; oauthlib appends OAuth params.
        from urllib.parse import urlencode
        non_oauth = {k: v for k, v in extra_params.items() if k != "oauth_callback"}
        if non_oauth:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{urlencode(non_oauth)}"
    signed_uri, _, _ = client.sign(url, http_method="GET")
    return signed_uri


def _parse_form(text: str) -> dict[str, str]:
    """Parse application/x-www-form-urlencoded responses (request_token, access_token)."""
    parsed = parse_qs(text, keep_blank_values=False)
    return {k: v[0] for k, v in parsed.items() if v}


async def fetch_request_token(callback_url: str, http: httpx.AsyncClient) -> dict[str, str]:
    """3-legged OAuth1 step 1: get a temporary request_token + secret."""
    consumer_key, consumer_secret = get_credentials()
    signed = _sign(
        REQUEST_TOKEN_URL,
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        extra_params={"oauth_callback": callback_url},
    )
    resp = await http.get(signed)
    if resp.status_code != 200:
        raise FatSecretAPIError(
            f"request_token failed: {resp.status_code} {resp.text[:200]}"
        )
    data = _parse_form(resp.text)
    if "oauth_token" not in data or "oauth_token_secret" not in data:
        raise FatSecretAPIError(f"request_token missing fields: {data}")
    return data


def authorize_url(oauth_token: str) -> str:
    """3-legged OAuth1 step 2: URL the user opens in their browser."""
    return f"{AUTHORIZE_URL}?oauth_token={oauth_token}"


async def fetch_access_token(
    oauth_token: str,
    oauth_token_secret: str,
    oauth_verifier: str,
    http: httpx.AsyncClient,
) -> dict[str, str]:
    """3-legged OAuth1 step 3: trade verifier for the long-lived access_token."""
    consumer_key, consumer_secret = get_credentials()
    signed = _sign(
        ACCESS_TOKEN_URL,
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        extra_params={"oauth_verifier": oauth_verifier},
    )
    resp = await http.get(signed)
    if resp.status_code == 401:
        raise FatSecretAuthError(f"access_token rejected: {resp.text[:200]}")
    if resp.status_code != 200:
        raise FatSecretAPIError(
            f"access_token failed: {resp.status_code} {resp.text[:200]}"
        )
    data = _parse_form(resp.text)
    if "oauth_token" not in data or "oauth_token_secret" not in data:
        raise FatSecretAPIError(f"access_token missing fields: {data}")
    return data


def _date_to_int(target: date_type) -> int:
    """FatSecret encodes dates as days since 1970-01-01."""
    return (target - _EPOCH).days


def _clean_numeric(val: Any) -> float | None:
    """Coerce to float, drop NaN/inf, clamp negatives to None."""
    f = safe_float(val)
    if f is None:
        return None
    if math.isnan(f) or math.isinf(f) or f < 0:
        return None
    return f


def _normalize_entry(raw: dict, target_date: date_type) -> dict | None:
    """Transform a FatSecret food_entry dict into a FoodEntry-ready field dict.

    Returns None if the entry is malformed (missing external_id or food_entry_name).
    """
    external_id = raw.get("food_entry_id")
    name = raw.get("food_entry_name")
    if not external_id or not name:
        return None

    fields: dict[str, Any] = {
        "external_id": str(external_id),
        "date": target_date,
        "food_entry_name": str(name)[:256],
    }
    for raw_key, val in raw.items():
        if raw_key in ("food_entry_id", "food_entry_name", "date_int"):
            continue
        col = _FIELD_MAP.get(raw_key, raw_key)
        if col in _NUMERIC_FIELDS:
            cleaned = _clean_numeric(val)
            if cleaned is not None:
                fields[col] = cleaned
        elif col in {"meal", "food_id", "serving_id", "food_entry_description"}:
            fields[col] = str(val)[:512] if col == "food_entry_description" else str(val)[:64]
    return fields


def _extract_entries(payload: dict) -> list[dict]:
    """Normalize FatSecret's three response shapes for `food_entries.get`:
      {"food_entries": ""}                              → []
      {"food_entries": {"food_entry": {...}}}           → [{...}]
      {"food_entries": {"food_entry": [{...}, {...}]}}  → [{...}, {...}]
    """
    container = payload.get("food_entries")
    if not isinstance(container, dict):
        return []
    inner = container.get("food_entry")
    if inner is None:
        return []
    if isinstance(inner, list):
        return [e for e in inner if isinstance(e, dict)]
    if isinstance(inner, dict):
        return [inner]
    return []


async def get_food_entries_for_date(
    oauth_token: str,
    oauth_token_secret: str,
    target_date: date_type,
    http: httpx.AsyncClient,
) -> list[dict]:
    """Fetch and normalize all food diary entries for one date.

    Returns a list of field dicts ready to pass into `upsert_food_entry`.
    """
    consumer_key, consumer_secret = get_credentials()
    signed = _sign(
        REST_URL,
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        extra_params={
            "method": "food_entries.get",
            "format": "json",
            "date": str(_date_to_int(target_date)),
        },
    )
    resp = await http.get(signed)
    if resp.status_code == 401:
        raise FatSecretAuthError("food_entries.get: token rejected")
    if resp.status_code != 200:
        raise FatSecretAPIError(
            f"food_entries.get failed: {resp.status_code} {resp.text[:200]}"
        )
    payload = resp.json()
    if isinstance(payload, dict) and "error" in payload:
        err = payload["error"]
        # FatSecret OAuth-related errors usually have code 5/13/14 → invalid token
        code = err.get("code") if isinstance(err, dict) else None
        if code in (5, 13, 14):
            raise FatSecretAuthError(f"FatSecret API error: {err}")
        raise FatSecretAPIError(f"FatSecret API error: {err}")

    return [
        normalized
        for entry in _extract_entries(payload)
        if (normalized := _normalize_entry(entry, target_date)) is not None
    ]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
