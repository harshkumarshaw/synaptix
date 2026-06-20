"""
snx-auth — Synaptix Authentication & Authorization Service.

Handles:
- User login (email+password, OTP, SSO)
- JWT token issuance and refresh
- MFA (TOTP)
- User profile management

Port: 8001 (local dev)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import auth
from packages.shared.auth.tenant_context import TenantContextMiddleware
from packages.shared.errors import (
    AuthenticationError,
    MFARequiredError,
    PermissionDeniedError,
    SynaptixError,
    TenantContextMissingError,
    TokenExpiredError,
    TokenInvalidError,
)
from packages.shared.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Startup: configure logging, database, and any startup tasks.
    Shutdown: cleanup connections.
    """
    settings = get_settings()

    # Configure logging
    configure_logging(
        log_level=settings.log_level,
        json_output=settings.env != "local",
    )

    # Configure database
    from packages.shared.db.session import configure_database

    configure_database(
        database_url=settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.env == "local",
    )

    logger.info(
        "snx-auth starting",
        extra={"env": settings.env, "version": "0.1.0"},
    )

    yield

    logger.info("snx-auth shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Synaptix Auth Service",
        description="Authentication & Authorization for the Synaptix platform",
        version="0.1.0",
        docs_url="/docs" if settings.env == "local" else None,
        redoc_url="/redoc" if settings.env == "local" else None,
        openapi_url="/openapi.json" if settings.env == "local" else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters: first added = outermost) ─────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(TenantContextMiddleware)

    # ── Exception Handlers ──────────────────────────────────────────────────
    @app.exception_handler(SynaptixError)
    async def synaptix_error_handler(request: Request, exc: SynaptixError) -> JSONResponse:
        """Map domain errors to HTTP responses with standard error envelope."""
        status_map: dict[type[SynaptixError], int] = {
            AuthenticationError: 401,
            TokenExpiredError: 401,
            TokenInvalidError: 401,
            MFARequiredError: 403,
            PermissionDeniedError: 403,
            TenantContextMissingError: 403,
        }
        status_code = status_map.get(type(exc), 400)

        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "data": None,
                "meta": {
                    "request_id": str(getattr(request.state, "request_id", "unknown")),
                    "api_version": "v1",
                },
                "errors": [exc.to_dict()],
            },
        )

    # ── Routers ─────────────────────────────────────────────────────────────
    app.include_router(auth.router, prefix="/api/v1")

    # ── Health & Ready endpoints ─────────────────────────────────────────────
    @app.get("/health", tags=["infrastructure"])
    async def health() -> dict[str, str]:
        """Health check endpoint. Returns 200 if the service is running."""
        return {"status": "ok", "service": "snx-auth", "version": "0.1.0"}

    @app.get("/ready", tags=["infrastructure"])
    async def ready() -> dict[str, str]:
        """Readiness check. Returns 200 when DB is reachable."""
        # TODO(2026-Q3): Add actual DB ping check. SNX-DEV-001
        return {"status": "ready", "service": "snx-auth"}

    return app


app = create_app()
