"""
snx-auth Configuration.

All config comes from environment variables (via pydantic-settings).
NEVER hardcode values here. NEVER commit .env files.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """snx-auth service settings.

    All values come from environment variables with SNX_ prefix.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SNX_",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    env: str = Field(default="local", alias="SNX_ENV")
    log_level: str = Field(default="INFO", alias="SNX_LOG_LEVEL")
    timezone: str = Field(default="Asia/Kolkata", alias="SNX_TIMEZONE")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://snx:snx_dev_pass@localhost:5435/synaptix_dev",
        alias="SNX_DATABASE_URL",
    )
    database_pool_size: int = Field(default=10, alias="SNX_DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="SNX_DATABASE_MAX_OVERFLOW")

    # JWT
    jwt_secret: str = Field(alias="SNX_JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="SNX_JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60, alias="SNX_JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=30, alias="SNX_JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )

    # MFA
    mfa_issuer: str = Field(default="Synaptix", alias="SNX_MFA_ISSUER")

    # CORS
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"],
    )

    # Tenant
    tenant_header: str = Field(default="X-Tenant-ID", alias="SNX_TENANT_HEADER")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings singleton. Cached after first call.
    """
    return Settings()  # type: ignore[call-arg]
