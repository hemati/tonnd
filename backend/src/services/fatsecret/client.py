"""FatSecret OAuth 1.0a client + food diary fetcher.

OAuth1 (3-legged) is required because FatSecret's OAuth2 client_credentials
flow can only read generic data, not the user's food diary. We sign with
HMAC-SHA1 via oauthlib and ship through httpx.AsyncClient.

Signature is delivered in the URL query string (signature_type=QUERY).
This was originally moved to AUTH_HEADER on a security review note, but
FatSecret's auth servers don't accept the Authorization header and reject
with "Missing required parameter: oauth_consumer_key". Mitigation for the
URL-leak risk: TONND does not log httpx request URLs anywhere, and the
oauth_signature in the URL is not the OAuth token itself — it's a one-shot
HMAC of that request. The high-value secrets (oauth_token_secret,
consumer_secret) are NEVER in the URL.
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
    SIGNATURE_TYPE_QUERY,
    Client as OAuth1Client,
)

from src.utils.safe_parse import safe_float

logger = logging.getLogger(__name__)

REQUEST_TOKEN_URL = "https://authentication.fatsecret.com/oauth/request_token"
# NOTE: the original spec said www.fatsecret.com/oauth/authorize but that
# returns 403/Not Found. The correct authorize endpoint is on the same
# authentication.* host as the request_token + access_token endpoints.
AUTHORIZE_URL = "https://authentication.fatsecret.com/oauth/authorize"
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
) -> str:
    """Sign a GET request. Returns the fully-qualified signed URL.

    All OAuth params (consumer_key, signature, callback, verifier, …) land
    in the URL query string. FatSecret's auth endpoints don't recognize
    Authorization-header-mode OAuth1.
    """
    client = OAuth1Client(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        callback_uri=callback_uri,
        verifier=verifier,
        signature_method=SIGNATURE_HMAC_SHA1,
        signature_type=SIGNATURE_TYPE_QUERY,
    )
    if query_params:
        url = f"{url}?{urlencode(query_params)}"
    uri, _headers, _body = client.sign(url, http_method="GET")
    return uri


def _parse_form(text: str) -> dict[str, str]:
    """Parse application/x-www-form-urlencoded responses (request_token, access_token)."""
    parsed = parse_qs(text, keep_blank_values=False)
    return {k: v[0] for k, v in parsed.items() if v}


async def fetch_request_token(callback_url: str, http: httpx.AsyncClient) -> dict[str, str]:
    """3-legged OAuth1 step 1: get a temporary request_token + secret."""
    consumer_key, consumer_secret = get_credentials()
    uri = _sign(
        REQUEST_TOKEN_URL,
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        callback_uri=callback_url,
    )
    resp = await http.get(uri)
    if resp.status_code != 200:
        raise FatSecretAPIError(
            f"request_token failed: {resp.status_code} {resp.text[:200]}"
        )
    data = _parse_form(resp.text)
    if "oauth_token" not in data or "oauth_token_secret" not in data:
        # Don't echo `data` — partial responses can include the secret field.
        raise FatSecretAPIError(
            f"request_token missing fields (got keys: {sorted(data.keys())})"
        )
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
    uri = _sign(
        ACCESS_TOKEN_URL,
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        verifier=oauth_verifier,
    )
    resp = await http.get(uri)
    if resp.status_code == 401:
        raise FatSecretAuthError(f"access_token rejected: {resp.text[:200]}")
    if resp.status_code != 200:
        raise FatSecretAPIError(
            f"access_token failed: {resp.status_code} {resp.text[:200]}"
        )
    data = _parse_form(resp.text)
    if "oauth_token" not in data or "oauth_token_secret" not in data:
        # Don't echo `data` — partial responses can include the secret field.
        raise FatSecretAPIError(
            f"access_token missing fields (got keys: {sorted(data.keys())})"
        )
    return data


def _date_to_int(target: date_type) -> int:
    """FatSecret encodes dates as days since 1970-01-01."""
    return (target - _EPOCH).days


# Hard ceiling for any per-entry numeric. Largest plausible single-entry
# values: ~10000 calories, ~10000g of any macro (a 10kg block of food).
# Anything larger is corrupted / hostile data and would overflow the
# Postgres Integer column when summed into daily_nutrition.calories_in.
_NUMERIC_MAX = 1_000_000.0


def _clean_numeric(val: Any) -> float | None:
    """Coerce to float, drop NaN/inf/negative, cap absurdly large values.

    Returning None for >_NUMERIC_MAX is intentional: silently clamping to
    the cap would write a misleading "1M calories" record. Dropping the
    field forces the user to notice (the entry shows incomplete macros).
    """
    f = safe_float(val)
    if f is None:
        return None
    if math.isnan(f) or math.isinf(f) or f < 0 or f > _NUMERIC_MAX:
        return None
    return f


# DB column-width caps. Truncating in the client keeps INSERT/flush from
# crashing on oversized FatSecret-supplied strings; widths must match
# food_models.FoodEntry exactly.
_STR_LIMITS = {
    "external_id": 64,
    "food_entry_name": 256,
    "meal": 32,
    "food_id": 64,
    "serving_id": 64,
    "food_entry_description": 512,
}


def _raw_external_id(raw: dict) -> str | None:
    """Extract the food_entry_id from a raw FatSecret entry, truncated to DB width.

    Used both by _normalize_entry and by the sync reconciliation pass — the
    reconciliation needs to know "what the API claims exists" independent of
    whether an entry is otherwise well-formed enough to persist.
    """
    eid = raw.get("food_entry_id")
    if not eid:
        return None
    return str(eid)[:_STR_LIMITS["external_id"]]


def _normalize_entry(raw: dict, target_date: date_type) -> dict | None:
    """Transform a FatSecret food_entry dict into FoodEntry-ready fields.

    Returns None if the entry is malformed (missing external_id or food_entry_name).
    Callers reconciling soft-deletes should use _raw_external_id() instead of
    inferring "API has this id" from the presence of a normalized entry — a
    malformed entry that returns None still represents a server-side row.
    """
    external_id = _raw_external_id(raw)
    name = raw.get("food_entry_name")
    if not external_id or not name:
        return None

    fields: dict[str, Any] = {
        "external_id": external_id,
        "date": target_date,
        "food_entry_name": str(name)[:_STR_LIMITS["food_entry_name"]],
    }
    for raw_key, val in raw.items():
        if raw_key in ("food_entry_id", "food_entry_name", "date_int"):
            continue
        col = _FIELD_MAP.get(raw_key, raw_key)
        if col in _NUMERIC_FIELDS:
            cleaned = _clean_numeric(val)
            if cleaned is not None:
                fields[col] = cleaned
        elif col in _STR_LIMITS:
            fields[col] = str(val)[:_STR_LIMITS[col]]
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
) -> dict:
    """Fetch food diary entries for one date.

    Returns:
        {
            "normalized": [field-dict ready for upsert_food_entry, ...],
            "api_external_ids": {raw_external_id, ...}  # ALL ids the API claims
                                                         # exist for the date,
                                                         # incl. entries we
                                                         # couldn't normalize
        }

    Reconciliation uses `api_external_ids`, not the normalized list — a
    malformed entry that we drop on parse must NOT be treated as deleted by
    the reconciliation pass.
    """
    consumer_key, consumer_secret = get_credentials()
    uri = _sign(
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
    resp = await http.get(uri)
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

    raw_entries = _extract_entries(payload)
    api_external_ids: set[str] = {
        rid for rid in (_raw_external_id(e) for e in raw_entries) if rid
    }
    normalized = [
        n for entry in raw_entries
        if (n := _normalize_entry(entry, target_date)) is not None
    ]
    return {"normalized": normalized, "api_external_ids": api_external_ids}
