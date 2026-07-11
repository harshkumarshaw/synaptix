"""
snx-academic — Synaptix Academic Structure & Timetable Scheduler Service.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import (
    academic,
    admissions,
    attendance,
    calendar,
    curriculum_migration,
    dashboard,
    exam,
    leave,
    lesson_plan,
    session,
)
from packages.shared.auth.jwt import TokenPayload
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

# Monkeypatch TokenPayload to add user_uuid alias to comply with router assumptions
TokenPayload.user_uuid = property(lambda self: self.user_id)

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

    logger.info(
        "snx-academic starting",
        extra={"env": settings.env, "version": "0.1.0"},
    )

    yield

    logger.info("snx-academic shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Synaptix Academic Service",
        description="Academic structure and timetable scheduler service",
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

    app.include_router(academic.router, prefix="/api/v1")
    app.include_router(calendar.router, prefix="/api/v1")
    app.include_router(lesson_plan.router, prefix="/api/v1")
    app.include_router(session.router, prefix="/api/v1")
    app.include_router(curriculum_migration.router, prefix="/api/v1")
    app.include_router(attendance.router, prefix="/api/v1")
    app.include_router(leave.router, prefix="/api/v1")
    app.include_router(admissions.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")
    app.include_router(exam.router, prefix="/api/v1")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "message": "Welcome to Synaptix Academic Service",
            "docs": "/docs",
            "health": "/health",
            "status": "running",
        }

    @app.get("/health", tags=["infrastructure"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "snx-academic", "version": "0.1.0"}

    @app.get("/ready", tags=["infrastructure"])
    async def ready() -> dict[str, str]:
        return {"status": "ready", "service": "snx-academic"}

    return app


app = create_app()
