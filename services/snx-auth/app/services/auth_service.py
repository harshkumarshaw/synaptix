"""
snx-auth — Auth Business Logic Service.

Handles the actual authentication logic:
- Password verification (bcrypt)
- OTP generation and verification
- JWT token issuance
- MFA (TOTP) verification
- Session management

This is a stub implementation. Full implementation is Phase 1A.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.auth.jwt import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from packages.shared.db.session import get_db
from packages.shared.errors import (
    AuthenticationError,
    MFACodeInvalidError,
    TokenInvalidError,
)
from packages.shared.logging import get_logger

from app.config import get_settings, Settings
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

logger = get_logger(__name__)


class AuthService:
    """Authentication business logic service.

    Injected as a FastAPI dependency via Depends(AuthService).
    Receives the DB session and settings through dependency injection.
    """

    def __init__(
        self,
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> None:
        """Initialize the auth service.

        Args:
            settings: Application settings (injected).
        """
        self.settings = settings

    async def login(self, body: LoginRequest) -> LoginResponse:
        """Authenticate user with email and password.

        Args:
            body: Login credentials.

        Returns:
            LoginResponse with tokens.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        # TODO(2026-Q3): Implement full password verification with bcrypt + DB lookup.
        # SNX-AUTH-IMPL-001
        raise NotImplementedError(
            "Email login is not yet implemented. Use OTP login for now."
        )

    async def request_otp(self, body: OTPRequestBody) -> None:
        """Generate and send an OTP to the user's registered mobile.

        Args:
            body: Mobile number and tenant_id.

        Raises:
            AuthenticationError: If mobile is not registered.
        """
        # TODO(2026-Q3): Implement OTP generation + SMS dispatch. SNX-AUTH-IMPL-002
        raise NotImplementedError("OTP dispatch not yet implemented.")

    async def verify_otp(self, body: OTPVerifyRequest) -> LoginResponse:
        """Verify OTP and issue JWT tokens.

        Args:
            body: Mobile, OTP, and tenant_id.

        Returns:
            LoginResponse with tokens.

        Raises:
            AuthenticationError: If OTP is incorrect or expired.
        """
        # TODO(2026-Q3): Implement OTP verification. SNX-AUTH-IMPL-003
        raise NotImplementedError("OTP verification not yet implemented.")

    async def refresh(self, body: RefreshRequest) -> RefreshResponse:
        """Exchange refresh token for a new access token.

        Args:
            body: Refresh token.

        Returns:
            RefreshResponse with new access token.

        Raises:
            TokenInvalidError: If refresh token is invalid or expired.
        """
        payload = decode_token(body.refresh_token, self.settings.jwt_secret)

        if payload.type != "refresh":
            raise TokenInvalidError(
                "Expected a refresh token, received an access token.",
                details={"token_type": payload.type},
            )

        # TODO(2026-Q3): Check refresh token is not revoked (DB lookup). SNX-AUTH-IMPL-004
        access_token = create_access_token(
            user_id=payload.user_id,
            tenant_id=payload.tenant_uuid,
            roles=payload.roles,
            secret=self.settings.jwt_secret,
            expires_in_minutes=self.settings.jwt_access_token_expire_minutes,
            mfa_verified=payload.mfa_verified,
        )

        return RefreshResponse(
            access_token=access_token,
            expires_in_seconds=self.settings.jwt_access_token_expire_minutes * 60,
        )

    async def verify_mfa(
        self, body: MFAVerifyRequest, current_user: TokenPayload
    ) -> LoginResponse:
        """Verify TOTP code and issue MFA-verified tokens.

        Args:
            body: TOTP code.
            current_user: Partial access token payload.

        Returns:
            LoginResponse with MFA-verified tokens.

        Raises:
            MFACodeInvalidError: If TOTP code is incorrect.
        """
        # TODO(2026-Q3): Implement TOTP verification with pyotp. SNX-AUTH-IMPL-005
        raise NotImplementedError("MFA verification not yet implemented.")

    async def get_profile(self, current_user: TokenPayload) -> UserProfileResponse:
        """Get the authenticated user's profile.

        Args:
            current_user: Current user from JWT.

        Returns:
            UserProfileResponse with user details.
        """
        # TODO(2026-Q3): Implement DB lookup for user profile. SNX-AUTH-IMPL-006
        raise NotImplementedError("Profile lookup not yet implemented.")

    async def logout(
        self, body: RefreshRequest, current_user: TokenPayload
    ) -> None:
        """Invalidate the user's refresh token.

        Args:
            body: Refresh token to invalidate.
            current_user: Authenticated user.
        """
        # TODO(2026-Q3): Implement refresh token revocation (DB). SNX-AUTH-IMPL-007
        logger.info(
            "Logout requested",
            extra={"user_id": current_user.sub, "tenant_id": current_user.tenant_id},
        )
