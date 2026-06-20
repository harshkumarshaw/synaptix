"""
Synaptix Test Configuration — conftest.py

Shared pytest fixtures available across all test modules.
Fixtures here are automatically discovered by pytest.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment variables BEFORE any imports
os.environ.setdefault("SNX_ENV", "test")
os.environ.setdefault(
    "SNX_DATABASE_URL",
    "postgresql+asyncpg://snx_test:snx_test_pass@localhost:5433/synaptix_test",
)
os.environ.setdefault(
    "SNX_JWT_SECRET",
    "test_jwt_secret_that_is_long_enough_for_hs256_at_least_32_chars",
)

from packages.shared.db.base import Base

# ============================================================================
# Constants
# ============================================================================

JMN_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
JWT_SECRET = os.environ["SNX_JWT_SECRET"]


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio for all async tests."""
    return "asyncio"


@pytest.fixture
def tenant_id() -> uuid.UUID:
    """Return the JMN test tenant UUID."""
    return JMN_TENANT_ID


@pytest.fixture
def jwt_secret() -> str:
    """Return the test JWT secret."""
    return JWT_SECRET


@pytest.fixture
def test_user_id() -> uuid.UUID:
    """Return a test user UUID."""
    return TEST_USER_ID
