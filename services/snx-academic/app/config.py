"""
snx-academic Configuration.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """snx-academic service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SNX_",
        case_sensitive=False,
        extra="ignore",
    )

    env: str = Field(default="local", alias="SNX_ENV")
    log_level: str = Field(default="INFO", alias="SNX_LOG_LEVEL")
    timezone: str = Field(default="Asia/Kolkata", alias="SNX_TIMEZONE")

    database_url: str = Field(
        default="postgresql+asyncpg://snx:snx_dev_pass@localhost:5435/synaptix_dev",
        alias="SNX_DATABASE_URL",
    )
    database_pool_size: int = Field(default=10, alias="SNX_DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="SNX_DATABASE_MAX_OVERFLOW")

    jwt_secret: str = Field(alias="SNX_JWT_SECRET")

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"],
    )

    tenant_header: str = Field(default="X-Tenant-ID", alias="SNX_TENANT_HEADER")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
