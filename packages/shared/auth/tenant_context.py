"""
Synaptix Tenant Context Middleware & Decorator.

The tenant context is established by:
1. TenantContextMiddleware — extracts tenant_id from JWT, sets request.state.tenant_id
2. @require_tenant_context — decorator that verifies tenant_id is present on endpoints

MANDATORY: Every API endpoint that touches tenant-scoped data MUST use
@require_tenant_context. The middleware alone is not enough — the decorator
provides a second explicit check.

NMC Commandment 1: Tenant isolation is sacred.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from packages.shared.errors import TenantContextMissingError
from packages.shared.logging import get_logger

logger = get_logger(__name__)

# Header and claim names
TENANT_ID_HEADER = "X-Tenant-ID"
TENANT_ID_JWT_CLAIM = "tenant_id"

# Endpoints that do NOT require tenant context
TENANT_EXEMPT_PATHS = frozenset(
    [
        "/health",
        "/ready",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/sso/google",
        "/api/v1/auth/sso/microsoft",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]
)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Extracts tenant_id from the JWT token or X-Tenant-ID header.

    Sets request.state.tenant_id (UUID) for every authenticated request.
    Skips exempt paths (login, health, docs).

    The PostgreSQL RLS policy uses SET LOCAL snx.current_tenant_id — this
    middleware provides the UUID value that the DB session will use.
    """

    def __init__(self, app: ASGIApp, exempt_paths: frozenset[str] | None = None) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application.
            exempt_paths: Paths that don't require tenant context. Defaults to TENANT_EXEMPT_PATHS.
        """
        super().__init__(app)
        self.exempt_paths = exempt_paths or TENANT_EXEMPT_PATHS

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request, extracting and validating tenant context.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or endpoint handler.

        Returns:
            The HTTP response.
        """
        # Try to get tenant_id from JWT claims (set by auth middleware earlier in chain)
        tenant_id_str: str | None = getattr(request.state, "jwt_tenant_id", None)

        # Fallback: X-Tenant-ID header (for service-to-service calls)
        if tenant_id_str is None:
            tenant_id_str = request.headers.get(TENANT_ID_HEADER)

        if tenant_id_str is None:
            # Skip tenant extraction for exempt paths if header not present
            if request.url.path in self.exempt_paths:
                return await call_next(request)
            logger.warning(
                "Request without tenant context",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client": request.client.host if request.client else "unknown",
                },
            )
            # Don't raise here — let @require_tenant_context handle it on the endpoint
            return await call_next(request)

        try:
            tenant_id = uuid.UUID(tenant_id_str)
        except ValueError:
            logger.error(
                "Invalid tenant_id format in request",
                extra={"tenant_id_str": tenant_id_str},
            )
            return await call_next(request)

        request.state.tenant_id = tenant_id

        logger.debug(
            "Tenant context established",
            extra={
                "tenant_id": str(tenant_id),
                "path": request.url.path,
            },
        )

        return await call_next(request)


def require_tenant_context(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that verifies tenant context is present before executing the endpoint.

    This is the second layer of tenant isolation enforcement (after middleware).
    Apply to every FastAPI endpoint handler that touches tenant-scoped data.

    Usage:
        @router.get("/students")
        @require_tenant_context
        async def list_students(request: Request, db: AsyncSession = Depends(get_db)):
            ...

    Raises:
        TenantContextMissingError: If request.state.tenant_id is not set.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Extract request from args or kwargs
        request: Request | None = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        if request is None:
            request = kwargs.get("request")

        if request is None or not hasattr(request.state, "tenant_id"):
            raise TenantContextMissingError(
                "Endpoint requires tenant context but none was found. "
                "Ensure TenantContextMiddleware is applied and the request is authenticated."
            )

        return await func(*args, **kwargs)

    return wrapper
