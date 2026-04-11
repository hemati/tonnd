"""Tests for Fitbit API client — OAuth functions and FitbitClient class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.fitbit.client import (
    FitbitAPIError,
    FitbitClient,
    RateLimitError,
    TokenExpiredError,
    exchange_code_for_tokens,
    get_authorization_url,
    get_fitbit_credentials,
    refresh_access_token,
    revoke_token,
)


def _make_async_client(response) -> AsyncMock:
    """Create a mock httpx.AsyncClient that returns the given response on post/get."""
    mock_client = AsyncMock()
    mock_client.post.return_value = response
    mock_client.get.return_value = response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# ---------------------------------------------------------------------------
# get_fitbit_credentials
# ---------------------------------------------------------------------------
class TestGetFitbitCredentials:
    def test_returns_credentials_when_set(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "my-id")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "my-secret")
        cid, csecret = get_fitbit_credentials()
        assert cid == "my-id"
        assert csecret == "my-secret"

    def test_raises_when_client_id_missing(self, monkeypatch):
        monkeypatch.delenv("FITBIT_CLIENT_ID", raising=False)
        monkeypatch.delenv("FITBIT_CLIENT_SECRET", raising=False)
        with pytest.raises(RuntimeError, match="FITBIT_CLIENT_ID"):
            get_fitbit_credentials()

    def test_raises_when_client_secret_missing(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "my-id")
        monkeypatch.delenv("FITBIT_CLIENT_SECRET", raising=False)
        with pytest.raises(RuntimeError, match="FITBIT_CLIENT_ID"):
            get_fitbit_credentials()

    def test_raises_when_both_empty_strings(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "")
        with pytest.raises(RuntimeError):
            get_fitbit_credentials()


# ---------------------------------------------------------------------------
# get_authorization_url
# ---------------------------------------------------------------------------
class TestGetAuthorizationUrl:
    def test_url_contains_required_params(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "test-id")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "test-secret")
        url = get_authorization_url("http://localhost/callback", "state123")
        assert "https://www.fitbit.com/oauth2/authorize" in url
        assert "client_id=test-id" in url
        assert "state=state123" in url
        assert "response_type=code" in url
        assert "redirect_uri=http" in url
        assert "scope=" in url
        assert "prompt=consent" in url


# ---------------------------------------------------------------------------
# exchange_code_for_tokens
# ---------------------------------------------------------------------------
class TestExchangeCodeForTokens:
    @pytest.mark.asyncio
    async def test_success(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "csec")

        token_data = {"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = token_data

        mock_client = _make_async_client(mock_response)
        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_client):
            result = await exchange_code_for_tokens("code123", "http://cb")

        assert result == token_data
        mock_client.post.assert_called_once()
        assert "authorization_code" in str(mock_client.post.call_args)

    @pytest.mark.asyncio
    async def test_failure_raises(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "csec")

        mock_response = MagicMock(status_code=400, text="invalid_code")
        mock_client = _make_async_client(mock_response)

        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception, match="Failed to exchange code"):
                await exchange_code_for_tokens("bad", "http://cb")


# ---------------------------------------------------------------------------
# refresh_access_token
# ---------------------------------------------------------------------------
class TestRefreshAccessToken:
    @pytest.mark.asyncio
    async def test_success(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "csec")

        token_data = {"access_token": "new-at", "refresh_token": "new-rt", "expires_in": 3600}
        mock_response = MagicMock(status_code=200, text="")
        mock_response.json.return_value = token_data

        mock_client = _make_async_client(mock_response)
        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_client):
            result = await refresh_access_token("old-rt")

        assert result == token_data

    @pytest.mark.asyncio
    async def test_401_raises_token_expired(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "csec")

        mock_response = MagicMock(status_code=401, text="unauthorized")
        mock_client = _make_async_client(mock_response)

        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(TokenExpiredError, match="invalid or expired"):
                await refresh_access_token("bad-rt")

    @pytest.mark.asyncio
    async def test_invalid_grant_raises_token_expired(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "csec")

        mock_response = MagicMock(
            status_code=200, text='{"errors":[{"errorType":"invalid_grant"}]}'
        )
        mock_client = _make_async_client(mock_response)

        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(TokenExpiredError):
                await refresh_access_token("bad-rt")

    @pytest.mark.asyncio
    async def test_other_error_raises_fitbit_api_error(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "csec")

        mock_response = MagicMock(status_code=500, text="server error")
        mock_client = _make_async_client(mock_response)

        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(FitbitAPIError, match="Failed to refresh token"):
                await refresh_access_token("rt")


# ---------------------------------------------------------------------------
# revoke_token
# ---------------------------------------------------------------------------
class TestRevokeToken:
    @pytest.mark.asyncio
    async def test_success(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "csec")

        mock_client = _make_async_client(MagicMock(status_code=200))
        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_client):
            result = await revoke_token("token-to-revoke")

        assert result is True

    @pytest.mark.asyncio
    async def test_failure_returns_false(self, monkeypatch):
        monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
        monkeypatch.setenv("FITBIT_CLIENT_SECRET", "csec")

        mock_client = _make_async_client(MagicMock(status_code=401))
        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_client):
            result = await revoke_token("bad-token")

        assert result is False


# ---------------------------------------------------------------------------
# FitbitClient._make_request
# ---------------------------------------------------------------------------
class TestFitbitClientMakeRequest:
    @pytest.mark.asyncio
    async def test_200_returns_json(self):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"data": "ok"}

        mock_http = _make_async_client(mock_response)
        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_http):
            client = FitbitClient("my-token")
            result = await client._make_request("/test/endpoint")

        assert result == {"data": "ok"}
        assert "Bearer my-token" in str(mock_http.get.call_args)

    @pytest.mark.asyncio
    async def test_401_raises_token_expired(self):
        mock_http = _make_async_client(MagicMock(status_code=401))
        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_http):
            client = FitbitClient("expired-token")
            with pytest.raises(TokenExpiredError):
                await client._make_request("/test")

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit(self):
        mock_http = _make_async_client(MagicMock(status_code=429))
        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_http):
            client = FitbitClient("token")
            with pytest.raises(RateLimitError):
                await client._make_request("/test")

    @pytest.mark.asyncio
    async def test_500_raises_fitbit_api_error(self):
        mock_http = _make_async_client(MagicMock(status_code=500, text="internal error"))
        with patch("src.services.fitbit.client.httpx.AsyncClient", return_value=mock_http):
            client = FitbitClient("token")
            with pytest.raises(FitbitAPIError, match="API request failed"):
                await client._make_request("/test")


# ---------------------------------------------------------------------------
# FitbitClient individual get_* methods
# ---------------------------------------------------------------------------
class TestFitbitClientGetMethods:
    @pytest.mark.asyncio
    async def test_get_profile_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"user": {}}
            await client.get_profile()
            mock_req.assert_called_once_with("/1/user/-/profile.json")

    @pytest.mark.asyncio
    async def test_get_weight_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_weight("2026-04-07")
            mock_req.assert_called_once_with("/1/user/-/body/log/weight/date/2026-04-07.json")

    @pytest.mark.asyncio
    async def test_get_weight_range_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_weight_range("2026-04-01", "2026-04-07")
            mock_req.assert_called_once_with(
                "/1/user/-/body/log/weight/date/2026-04-01/2026-04-07.json"
            )

    @pytest.mark.asyncio
    async def test_get_body_fat_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_body_fat("2026-04-07")
            mock_req.assert_called_once_with("/1/user/-/body/log/fat/date/2026-04-07.json")

    @pytest.mark.asyncio
    async def test_get_activity_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_activity("2026-04-07")
            mock_req.assert_called_once_with("/1/user/-/activities/date/2026-04-07.json")

    @pytest.mark.asyncio
    async def test_get_sleep_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_sleep("2026-04-07")
            mock_req.assert_called_once_with("/1.2/user/-/sleep/date/2026-04-07.json")

    @pytest.mark.asyncio
    async def test_get_heart_rate_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_heart_rate("2026-04-07")
            mock_req.assert_called_once_with(
                "/1/user/-/activities/heart/date/2026-04-07/1d.json"
            )

    @pytest.mark.asyncio
    async def test_get_hrv_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_hrv("2026-04-07")
            mock_req.assert_called_once_with("/1/user/-/hrv/date/2026-04-07.json")

    @pytest.mark.asyncio
    async def test_get_spo2_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_spo2("2026-04-07")
            mock_req.assert_called_once_with("/1/user/-/spo2/date/2026-04-07.json")

    @pytest.mark.asyncio
    async def test_get_breathing_rate_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_breathing_rate("2026-04-07")
            mock_req.assert_called_once_with("/1/user/-/br/date/2026-04-07.json")

    @pytest.mark.asyncio
    async def test_get_vo2_max_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_vo2_max("2026-04-07")
            mock_req.assert_called_once_with("/1/user/-/cardioscore/date/2026-04-07.json")

    @pytest.mark.asyncio
    async def test_get_skin_temperature_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_skin_temperature("2026-04-07")
            mock_req.assert_called_once_with("/1/user/-/temp/skin/date/2026-04-07.json")

    @pytest.mark.asyncio
    async def test_get_active_zone_minutes_url(self):
        client = FitbitClient("tok")
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {}
            await client.get_active_zone_minutes("2026-04-07")
            mock_req.assert_called_once_with(
                "/1/user/-/activities/active-zone-minutes/date/2026-04-07/1d.json"
            )


# ---------------------------------------------------------------------------
# FitbitClient.get_all_data_for_date
# ---------------------------------------------------------------------------
class TestGetAllDataForDate:
    @pytest.mark.asyncio
    async def test_all_metrics_present(self):
        """When all endpoints succeed, data dict has all keys and errors is empty."""
        client = FitbitClient("tok")

        async def mock_request(endpoint):
            # Return realistic minimal data for each endpoint
            if "weight" in endpoint:
                return {"weight": [{"weight": 80.5, "fat": 18.2, "bmi": 24.5}]}
            if "activities/date" in endpoint:
                return {
                    "summary": {
                        "steps": 10000,
                        "caloriesOut": 2500,
                        "veryActiveMinutes": 30,
                        "fairlyActiveMinutes": 20,
                        "floors": 10,
                        "distances": [{"activity": "total", "distance": 7.5}],
                    }
                }
            if "sleep" in endpoint:
                return {
                    "sleep": [
                        {
                            "isMainSleep": True,
                            "duration": 28800000,
                            "efficiency": 92,
                            "levels": {
                                "summary": {
                                    "deep": {"minutes": 90},
                                    "light": {"minutes": 200},
                                    "rem": {"minutes": 100},
                                    "wake": {"minutes": 30},
                                }
                            },
                        }
                    ]
                }
            if "heart" in endpoint:
                return {
                    "activities-heart": [
                        {
                            "value": {
                                "restingHeartRate": 62,
                                "heartRateZones": [
                                    {"name": "Fat Burn", "min": 86, "max": 120, "minutes": 45, "caloriesOut": 200},
                                ],
                            }
                        }
                    ]
                }
            if "hrv" in endpoint:
                return {"hrv": [{"value": {"dailyRmssd": 45.2, "deepRmssd": 50.1}}]}
            if "spo2" in endpoint:
                return {"value": {"avg": 97, "min": 95, "max": 99}}
            if "/br/" in endpoint:
                return {"br": [{"value": {"breathingRate": 15.5}}]}
            if "cardioscore" in endpoint:
                return {"cardioScore": [{"value": {"vo2Max": 42.0}}]}
            if "temp/skin" in endpoint:
                return {"tempSkin": [{"value": {"nightlyRelative": -0.2}}]}
            if "active-zone-minutes" in endpoint:
                return {
                    "activities-active-zone-minutes": [
                        {
                            "value": {
                                "fatBurnActiveZoneMinutes": 20,
                                "cardioActiveZoneMinutes": 15,
                                "peakActiveZoneMinutes": 5,
                            }
                        }
                    ]
                }
            return {}

        with patch.object(client, "_make_request", side_effect=mock_request):
            result = await client.get_all_data_for_date("2026-04-07")

        assert result["date"] == "2026-04-07"
        assert result["errors"] == []
        data = result["data"]
        assert data["weight"]["weight_kg"] == 80.5
        assert data["activity"]["steps"] == 10000
        assert data["activity"]["distance_km"] == 7.5
        assert data["sleep"]["total_minutes"] == 480
        assert data["sleep"]["efficiency"] == 92
        assert data["heart_rate"]["resting_heart_rate"] == 62
        assert data["hrv"]["daily_rmssd"] == 45.2
        assert data["spo2"]["avg"] == 97
        assert data["breathing_rate"]["breathing_rate"] == 15.5
        assert data["vo2_max"]["vo2_max"] == 42.0
        assert data["temperature"]["relative_deviation"] == -0.2
        assert data["active_zone_minutes"]["total_minutes"] == 40

    @pytest.mark.asyncio
    async def test_partial_failures_collected_in_errors(self):
        """When some endpoints fail, their errors are collected and other data still returned."""
        client = FitbitClient("tok")

        call_count = 0

        async def mock_request(endpoint):
            nonlocal call_count
            call_count += 1
            if "weight" in endpoint:
                raise FitbitAPIError("weight endpoint down")
            if "sleep" in endpoint:
                raise FitbitAPIError("sleep endpoint down")
            if "activities/date" in endpoint:
                return {
                    "summary": {
                        "steps": 5000,
                        "caloriesOut": 2000,
                        "veryActiveMinutes": 10,
                        "fairlyActiveMinutes": 5,
                        "distances": [],
                    }
                }
            # Return empty/no-data for everything else
            return {}

        with patch.object(client, "_make_request", side_effect=mock_request):
            result = await client.get_all_data_for_date("2026-04-07")

        # Weight and sleep should show up in errors
        assert any("weight" in e for e in result["errors"])
        assert any("sleep" in e for e in result["errors"])
        # Activity should still be present
        assert result["data"]["activity"]["steps"] == 5000
        # distance_km should be None since no "total" distance was found
        assert result["data"]["activity"]["distance_km"] is None

    @pytest.mark.asyncio
    async def test_empty_weight_not_added(self):
        """When weight endpoint returns empty list, no weight key in data."""
        client = FitbitClient("tok")

        async def mock_request(endpoint):
            if "weight" in endpoint:
                return {"weight": []}
            return {}

        with patch.object(client, "_make_request", side_effect=mock_request):
            result = await client.get_all_data_for_date("2026-04-07")

        assert "weight" not in result["data"]

    @pytest.mark.asyncio
    async def test_sleep_no_main_sleep(self):
        """When sleep data has no isMainSleep entry, no sleep key in data."""
        client = FitbitClient("tok")

        async def mock_request(endpoint):
            if "sleep" in endpoint:
                return {"sleep": [{"isMainSleep": False, "duration": 1800000}]}
            return {}

        with patch.object(client, "_make_request", side_effect=mock_request):
            result = await client.get_all_data_for_date("2026-04-07")

        assert "sleep" not in result["data"]


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------
class TestExceptionHierarchy:
    def test_token_expired_is_fitbit_api_error(self):
        assert issubclass(TokenExpiredError, FitbitAPIError)

    def test_rate_limit_is_fitbit_api_error(self):
        assert issubclass(RateLimitError, FitbitAPIError)

    def test_fitbit_api_error_is_exception(self):
        assert issubclass(FitbitAPIError, Exception)
