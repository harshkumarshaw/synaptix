"""
snx-workflow — Synaptix Workflow Engine, MDM & Digital Asset Repository Service.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import assets, master_data, workflow
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from packages.shared.auth.tenant_context import TenantContextMiddleware
from packages.shared.errors import (
    AuthenticationError,
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
    settings = get_settings()

    configure_logging(
        log_level=settings.log_level,
        json_output=settings.env != "local",
    )

    from packages.shared.db.session import configure_database

    configure_database(
        database_url=settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.env == "local",
    )

    # Ensure local storage directory exists
    import os

    os.makedirs(settings.storage_dir, exist_ok=True)

    logger.info(
        "snx-workflow starting",
        extra={"env": settings.env, "version": "0.1.0"},
    )

    yield

    logger.info("snx-workflow shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Synaptix Workflow Service",
        description="Workflow engine, MDM, and digital asset repository service",
        version="0.1.0",
        docs_url="/docs" if settings.env == "local" else None,
        redoc_url="/redoc" if settings.env == "local" else None,
        openapi_url="/openapi.json" if settings.env == "local" else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(TenantContextMiddleware)

    @app.exception_handler(SynaptixError)
    async def synaptix_error_handler(request: Request, exc: SynaptixError) -> JSONResponse:
        status_map: dict[type[SynaptixError], int] = {
            AuthenticationError: 401,
            TokenExpiredError: 401,
            TokenInvalidError: 401,
            PermissionDeniedError: 403,
            TenantContextMissingError: 403,
        }
        status_code = status_map.get(type(exc), 400)

        # For resource not found, let's map it to 404
        from packages.shared.errors import ResourceNotFoundError

        if isinstance(exc, ResourceNotFoundError) or exc.code in {"SNX-RES-001", "SNX-WFL-002"}:
            status_code = 404

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

    app.include_router(master_data, prefix="/api/v1")
    app.include_router(workflow, prefix="/api/v1")
    app.include_router(assets, prefix="/api/v1")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "message": "Welcome to Synaptix Workflow Service",
            "docs": "/docs",
            "health": "/health",
            "status": "running",
        }

    @app.get("/health", tags=["infrastructure"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "snx-workflow", "version": "0.1.0"}

    @app.get("/ready", tags=["infrastructure"])
    async def ready() -> dict[str, str]:
        return {"status": "ready", "service": "snx-workflow"}

    return app


app = create_app()
