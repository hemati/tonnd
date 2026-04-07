"""Tests for API endpoints."""

import pytest


async def register_and_login(client, email="test@example.com", password="testpassword123") -> str:
    """Register a user and return JWT token."""
    await client.post("/auth/register", json={"email": email, "password": password})
    login = await client.post("/auth/jwt/login", data={
        "username": email, "password": password,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return login.json()["access_token"]


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_returns_ok(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_register_user(self, client):
        response = await client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "testpassword123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
        assert "id" in data

    async def test_register_duplicate_email(self, client):
        await client.post("/auth/register", json={
            "email": "dupe@example.com",
            "password": "testpassword123",
        })
        response = await client.post("/auth/register", json={
            "email": "dupe@example.com",
            "password": "anotherpassword",
        })
        assert response.status_code == 400

    async def test_login_with_valid_credentials(self, client):
        await client.post("/auth/register", json={
            "email": "login@example.com",
            "password": "testpassword123",
        })
        response = await client.post("/auth/jwt/login", data={
            "username": "login@example.com",
            "password": "testpassword123",
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_with_wrong_password(self, client):
        await client.post("/auth/register", json={
            "email": "wrong@example.com",
            "password": "correctpassword",
        })
        response = await client.post("/auth/jwt/login", data={
            "username": "wrong@example.com",
            "password": "wrongpassword",
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        assert response.status_code == 400


@pytest.mark.asyncio
class TestProtectedEndpoints:
    async def test_user_endpoint_unauthorized(self, client):
        response = await client.get("/api/user")
        assert response.status_code == 401

    async def test_data_endpoint_unauthorized(self, client):
        response = await client.get("/api/data")
        assert response.status_code == 401

    async def test_sync_endpoint_unauthorized(self, client):
        response = await client.post("/api/sync")
        assert response.status_code == 401

    async def test_user_endpoint_authenticated(self, client):
        token = await register_and_login(client, "auth@example.com")
        response = await client.get("/api/user", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "auth@example.com"
        assert data["fitbit_connected"] is False

    async def test_data_endpoint_authenticated(self, client):
        token = await register_and_login(client, "data@example.com")
        response = await client.get("/api/data?days=7", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "latest_weight" in data
        assert "fitbit_connected" in data
