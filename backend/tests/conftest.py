"""Shared test fixtures for backend tests."""

import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test env vars before importing app
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("RESET_PASSWORD_TOKEN_SECRET", "test-reset-secret")
os.environ.setdefault("VERIFICATION_TOKEN_SECRET", "test-verify-secret")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0xMjM0NTY3ODkwMTI=")
os.environ.setdefault("STATE_SECRET", "test-state-secret")
# Decoy URL to prevent database.py from connecting to PostgreSQL at import time.
# Actual tests use the in-memory engine below.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

from src.models.db_models import Base
import src.models.api_models  # noqa: F401 — register APIToken + AuditLog tables
import src.models.fitbit_models  # noqa: F401 — register typed Fitbit tables
from src.database import get_async_session

# Use SQLite for tests (in-memory)
TEST_DB_URL = "sqlite+aiosqlite://"
test_engine = create_async_engine(TEST_DB_URL)
test_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_session():
    async with test_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    """Async test client for FastAPI app."""
    from unittest.mock import patch
    # Import app after env vars are set
    from app import app
    app.dependency_overrides[get_async_session] = override_get_session

    # Patch audit_service to use the test DB session maker instead of production
    with patch("src.services.audit_service.async_session_maker", test_session_maker):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()
