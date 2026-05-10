"""FatSecret OAuth 1.0a client + food diary fetcher.

OAuth1 (3-legged) is required because FatSecret's OAuth2 client_credentials
flow can only read generic data, not the user's food diary. We sign with
HMAC-SHA1 via oauthlib and ship through httpx.AsyncClient.

Signature is delivered in the Authorization header (not the URL query) so
OAuth tokens cannot leak via request-URL logging in proxies or middleware.
"""

import json as _json
import logging
import math
import os
from datetime import date as date_type
from typing import Any
from urllib.parse import parse_qs, urlencode

import httpx
from oauthlib.oauth1 import (
    SIGNATURE_HMAC_SHA1,
    SIGNATURE_TYPE_AUTH_HEADER,
    Client as OAuth1Client,
)

from src.utils.safe_parse import safe_float

logger = logging.getLogger(__name__)

REQUEST_TOKEN_URL = "https://authentication.fatsecret.com/oauth/request_token"
AUTHORIZE_URL = "https://www.fatsecret.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://authentication.fatsecret.com/oauth/access_token"
REST_URL = "https://platform.fatsecret.com/rest/server.api"

# Day-since-epoch encoding the FatSecret API expects on `food_entries.get`.
_EPOCH = date_type(1970, 1, 1)

# Map FatSecret raw field name → our column name. Keys missing from this map
# (calories, meal, food_entry_name, ...) are passed through as-is.
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

_NUMERIC_FIELDS = {
    "number_of_units", "calories",
    "carbs_g", "fat_g", "protein_g", "fiber_g", "sugar_g",
    "saturated_fat_g", "polyunsaturated_fat_g", "monounsaturated_fat_g",
    "cholesterol_mg", "sodium_mg", "calcium_mg", "iron_mg", "potassium_mg",
    "vitamin_a_iu", "vitamin_c_mg",
}

# FatSecret error codes that mean the user's token is permanently invalid.
# Code 5 (invalid signature) is intentionally NOT here — it fires on transient
# clock skew and shouldn't auto-disconnect users.
_AUTH_FATAL_CODES = {13, 14}


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
    callback_uri: str | None = None,
    verifier: str | None = None,
    query_params: dict | None = None,
) -> tuple[str, dict]:
    """Sign a GET request. Returns (uri, headers); call as http.get(uri, headers=headers).

    Tokens land in the Authorization header, not the query string.
    """
    client = OAuth1Client(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        callback_uri=callback_uri,
        verifier=verifier,
        signature_method=SIGNATURE_HMAC_SHA1,
        signature_type=SIGNATURE_TYPE_AUTH_HEADER,
    )
    if query_params:
        url = f"{url}?{urlencode(query_params)}"
    uri, headers, _body = client.sign(url, http_method="GET")
    return uri, headers


def _parse_form(text: str) -> dict[str, str]:
    """Parse application/x-www-form-urlencoded responses (request_token, access_token)."""
    parsed = parse_qs(text, keep_blank_values=False)
    return {k: v[0] for k, v in parsed.items() if v}


async def fetch_request_token(callback_url: str, http: httpx.AsyncClient) -> dict[str, str]:
    """3-legged OAuth1 step 1: get a temporary request_token + secret."""
    consumer_key, consumer_secret = get_credentials()
    uri, headers = _sign(
        REQUEST_TOKEN_URL,
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        callback_uri=callback_url,
    )
    resp = await http.get(uri, headers=headers)
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
    uri, headers = _sign(
        ACCESS_TOKEN_URL,
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        verifier=oauth_verifier,
    )
    resp = await http.get(uri, headers=headers)
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
    """Transform a FatSecret food_entry dict into FoodEntry-ready fields.

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
            limit = 512 if col == "food_entry_description" else 64
            fields[col] = str(val)[:limit]
    return fields


def _extract_entries(payload: dict) -> list[dict]:
    """Normalize FatSecret's three documented response shapes for `food_entries.get`:
      {"food_entries": ""}                              → []
      {"food_entries": {"food_entry": {...}}}           → [{...}]
      {"food_entries": {"food_entry": [{...}, {...}]}}  → [{...}, {...}]
    Anything else is treated as a protocol violation and raises.
    """
    container = payload.get("food_entries")
    if container == "" or container is None:
        return []
    if not isinstance(container, dict):
        raise FatSecretAPIError(f"unexpected food_entries shape: {type(container).__name__}")
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
    """Fetch and normalize all food diary entries for one date."""
    consumer_key, consumer_secret = get_credentials()
    uri, headers = _sign(
        REST_URL,
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        query_params={
            "method": "food_entries.get",
            "format": "json",
            "date": str(_date_to_int(target_date)),
        },
    )
    resp = await http.get(uri, headers=headers)
    if resp.status_code == 401:
        raise FatSecretAuthError("food_entries.get: token rejected")
    if resp.status_code != 200:
        raise FatSecretAPIError(
            f"food_entries.get failed: {resp.status_code} {resp.text[:200]}"
        )
    try:
        payload = resp.json()
    except (ValueError, _json.JSONDecodeError):
        raise FatSecretAPIError(
            f"food_entries.get returned non-JSON body: {resp.text[:200]}"
        )
    if isinstance(payload, dict) and "error" in payload:
        err = payload["error"]
        code = err.get("code") if isinstance(err, dict) else None
        if code in _AUTH_FATAL_CODES:
            raise FatSecretAuthError(f"FatSecret API error: {err}")
        raise FatSecretAPIError(f"FatSecret API error: {err}")

    return [
        normalized
        for entry in _extract_entries(payload)
        if (normalized := _normalize_entry(entry, target_date)) is not None
    ]
