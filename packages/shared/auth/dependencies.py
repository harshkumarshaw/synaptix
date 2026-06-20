"""
Synaptix FastAPI Auth Dependencies.

Provides injectable dependencies for FastAPI endpoints:
- get_current_user: Extract and validate current user from JWT
- require_roles: Enforce RBAC — check the user has one of the required roles

Usage:
    @router.get("/students")
    async def list_students(
        user: Annotated[TokenPayload, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ):
        ...

    @router.delete("/tenants/{id}")
    async def delete_tenant(
        user: Annotated[TokenPayload, Depends(require_roles(["super_admin"]))],
    ):
        ...
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from packages.shared.auth.jwt import MFA_REQUIRED_ROLES, TokenPayload, decode_token
from packages.shared.errors import (
    AuthenticationError,
    MFARequiredError,
    PermissionDeniedError,
)
from packages.shared.logging import get_logger

logger = get_logger(__name__)

# HTTPBearer auto-extracts the Bearer token from Authorization header
_bearer_scheme = HTTPBearer(auto_error=False)


def _get_jwt_secret() -> str:
    """Get the JWT secret from environment.

    Returns:
        JWT secret string.

    Raises:
        RuntimeError: If SNX_JWT_SECRET is not configured.
    """
    secret = os.environ.get("SNX_JWT_SECRET")
    if not secret:
        raise RuntimeError("SNX_JWT_SECRET environment variable not set")
    return secret


async def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ] = None,
) -> TokenPayload:
    """FastAPI dependency: extract and validate the current user's JWT.

    Also sets request.state.jwt_tenant_id for TenantContextMiddleware.

    Args:
        request: FastAPI Request (injected by FastAPI).
        credentials: Bearer token from Authorization header.

    Returns:
        Validated TokenPayload for the authenticated user.

    Raises:
        AuthenticationError: If no token provided or token is invalid.
        MFARequiredError: If user's role requires MFA but mfa_verified is False.
    """
    if credentials is None:
        raise AuthenticationError(
            "No authentication credentials provided. "
            "Include 'Authorization: Bearer <token>' header."
        )

    secret = _get_jwt_secret()
    payload = decode_token(credentials.credentials, secret)

    # Verify access token (not refresh token)
    if payload.type != "access":
        raise AuthenticationError(
            "Expected an access token, received a refresh token.",
            details={"token_type": payload.type},
        )

    # Enforce MFA for privileged roles
    if payload.requires_mfa() and not payload.mfa_verified:
        raise MFARequiredError(
            "Multi-factor authentication is required for your role. "
            "Please complete MFA before accessing this endpoint.",
            details={"roles": payload.roles},
        )

    # Propagate tenant_id to middleware state
    request.state.jwt_tenant_id = payload.tenant_id

    logger.debug(
        "User authenticated",
        extra={
            "user_id": payload.sub,
            "tenant_id": payload.tenant_id,
            "roles": payload.roles,
        },
    )

    return payload


def require_roles(allowed_roles: list[str]) -> Callable[..., TokenPayload]:
    """Dependency factory: enforce that the current user has one of the allowed roles.

    Usage:
        @router.post("/admin/tenants")
        async def create_tenant(
            user: Annotated[TokenPayload, Depends(require_roles(["super_admin"]))]
        ):
            ...

    Args:
        allowed_roles: List of role names that may access this endpoint.

    Returns:
        A FastAPI dependency function that returns the validated TokenPayload.

    Raises:
        PermissionDeniedError: If the user lacks any of the required roles.
    """

    async def _check_roles(
        user: Annotated[TokenPayload, Depends(get_current_user)],
    ) -> TokenPayload:
        user_roles = set(user.roles)
        if not user_roles.intersection(allowed_roles):
            logger.warning(
                "Permission denied",
                extra={
                    "user_id": user.sub,
                    "user_roles": list(user_roles),
                    "required_roles": allowed_roles,
                },
            )
            raise PermissionDeniedError(
                f"Access denied. Required role(s): {', '.join(allowed_roles)}",
                details={
                    "user_roles": list(user_roles),
                    "required_roles": allowed_roles,
                },
            )
        return user

    return _check_roles
