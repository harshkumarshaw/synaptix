"""
snx-auth — Authentication Router.

Endpoints:
  POST /api/v1/auth/login          — Email + password login
  POST /api/v1/auth/otp/request   — Request OTP via mobile
  POST /api/v1/auth/otp/verify    — Verify OTP and get tokens
  POST /api/v1/auth/refresh        — Refresh access token
  POST /api/v1/auth/mfa/verify    — Verify TOTP MFA code
  GET  /api/v1/auth/me            — Current user profile
  POST /api/v1/auth/logout        — Invalidate refresh token
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MFAVerifyRequest,
    OTPRequestBody,
    OTPVerifyRequest,
    RefreshRequest,
    RefreshResponse,
    UserProfileResponse,
)
from app.services.auth_service import AuthService
from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload
from packages.shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    description=(
        "Authenticates the user with email + password. "
        "For privileged roles (admin, principal, dean, CoE), returns a token "
        "requiring MFA verification before full access is granted."
    ),
)
async def login(
    body: LoginRequest,
    service: Annotated[AuthService, Depends(AuthService)],
) -> LoginResponse:
    """Email + password authentication endpoint.

    Args:
        body: Login credentials (email, password, tenant_id).
        service: Auth service dependency.

    Returns:
        LoginResponse with access_token, refresh_token, and MFA status.
    """
    return await service.login(body)


@router.post(
    "/otp/request",
    status_code=status.HTTP_200_OK,
    summary="Request OTP via mobile number",
)
async def request_otp(
    body: OTPRequestBody,
    service: Annotated[AuthService, Depends(AuthService)],
) -> dict[str, str]:
    """Request a one-time password sent to the user's registered mobile.

    Args:
        body: Mobile number and tenant_id.
        service: Auth service dependency.
    """
    await service.request_otp(body)
    return {"message": "OTP sent to registered mobile number"}


@router.post(
    "/otp/verify",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and get tokens",
)
async def verify_otp(
    body: OTPVerifyRequest,
    service: Annotated[AuthService, Depends(AuthService)],
) -> LoginResponse:
    """Verify OTP and issue JWT tokens on success.

    Args:
        body: Mobile number, OTP, and tenant_id.
        service: Auth service dependency.
    """
    return await service.verify_otp(body)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    body: RefreshRequest,
    service: Annotated[AuthService, Depends(AuthService)],
) -> RefreshResponse:
    """Exchange a valid refresh token for a new access token.

    Args:
        body: Refresh token.
        service: Auth service dependency.
    """
    return await service.refresh(body)


@router.post(
    "/mfa/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify TOTP MFA code",
    description=(
        "Required for admin, principal, dean, controller_of_examinations. "
        "Must be called after /login before accessing privileged endpoints."
    ),
)
async def verify_mfa(
    body: MFAVerifyRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(AuthService)],
) -> LoginResponse:
    """Verify TOTP code and issue MFA-verified tokens.

    Args:
        body: TOTP code from authenticator app.
        current_user: Current user (requires partial access token from /login).
        service: Auth service dependency.
    """
    return await service.verify_mfa(body, current_user)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_me(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(AuthService)],
) -> UserProfileResponse:
    """Get the authenticated user's profile.

    Args:
        current_user: Authenticated user from JWT.
        service: Auth service dependency.
    """
    return await service.get_profile(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout and invalidate refresh token",
)
async def logout(
    body: RefreshRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(AuthService)],
) -> dict[str, str]:
    """Invalidate the user's refresh token.

    Args:
        body: Refresh token to invalidate.
        current_user: Authenticated user.
        service: Auth service dependency.
    """
    await service.logout(body, current_user)
    return {"message": "Logged out successfully"}
