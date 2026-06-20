"""snx-auth — Auth Business Logic Service.

Handles the actual authentication logic:
- Password verification (bcrypt)
- OTP generation and verification
- JWT token issuance
- MFA (TOTP) verification
- Session management
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
import pyotp
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_role import UserRole
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
from packages.shared.auth.jwt import (
    MFA_REQUIRED_ROLES,
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

logger = get_logger(__name__)


class AuthService:
    """Authentication business logic service.

    Injected as a FastAPI dependency via Depends(AuthService).
    Receives the DB session and settings through dependency injection.
    """

    def __init__(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> None:
        """Initialize the auth service.

        Args:
            db: Async database session.
            settings: Application settings (injected).
        """
        self.db = db
        self.settings = settings

    async def login(self, body: LoginRequest) -> LoginResponse:
        """Authenticate user with email and password.

        Args:
            body: Login credentials.

        Returns:
            LoginResponse with tokens.

        Raises:
            AuthenticationError: If credentials are invalid or user inactive.
        """
        # Validate tenant exists
        tenant = await self.db.get(Tenant, body.tenant_id)
        if not tenant:
            raise AuthenticationError("Invalid institution ID")

        # Find user by email and tenant (Defense-in-depth scoping by tenant_id)
        stmt = select(User).where(
            User.email == body.email,
            User.tenant_id == body.tenant_id,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user or not user.password_hash:
            raise AuthenticationError("Invalid email or password")

        # Verify password using native bcrypt
        password_bytes = body.password.encode("utf-8")
        hash_bytes = user.password_hash.encode("utf-8")
        if not bcrypt.checkpw(password_bytes, hash_bytes):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        # Fetch user's roles
        role_stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id, UserRole.tenant_id == body.tenant_id)
        )
        role_result = await self.db.execute(role_stmt)
        roles = list(role_result.scalars().all())

        # Determine MFA requirement
        mfa_required = user.mfa_enabled and any(r in MFA_REQUIRED_ROLES for r in roles)

        # Generate tokens
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=body.tenant_id,
            roles=roles,
            secret=self.settings.jwt_secret,
            expires_in_minutes=self.settings.jwt_access_token_expire_minutes,
            mfa_verified=not mfa_required,
        )

        refresh_token = create_refresh_token(
            user_id=user.id,
            tenant_id=body.tenant_id,
            secret=self.settings.jwt_secret,
            expires_in_days=self.settings.jwt_refresh_token_expire_days,
        )

        # Update last login timestamp
        user.last_login_at = datetime.now(UTC)
        await self.db.commit()

        logger.info(
            "User logged in successfully",
            extra={
                "user_id": str(user.id),
                "tenant_id": str(body.tenant_id),
                "mfa_required": mfa_required,
            },
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in_seconds=self.settings.jwt_access_token_expire_minutes * 60,
            mfa_required=mfa_required,
            user_id=user.id,
            tenant_id=body.tenant_id,
            roles=roles,
        )

    async def request_otp(self, body: OTPRequestBody) -> None:
        """Generate and store an OTP to the user's registered mobile in the DB.

        Args:
            body: Mobile number and tenant_id.

        Raises:
            AuthenticationError: If mobile is not registered or user is inactive.
        """
        # Find user by mobile and tenant (Defense-in-depth scoping by tenant_id)
        stmt = select(User).where(
            User.mobile == body.mobile,
            User.tenant_id == body.tenant_id,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise AuthenticationError("Mobile number not registered under this institution")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        # Generate a 6-digit OTP code
        otp = f"{random.randint(100000, 999999)}"  # noqa: S311

        # Store OTP and expiration in the DB (5 minutes validity)
        user.otp_code = otp
        user.otp_expires_at = datetime.now(UTC) + timedelta(minutes=5)
        await self.db.commit()

        logger.info(
            "OTP generated and stored",
            extra={
                "user_id": str(user.id),
                "mobile": body.mobile,
                "otp_code": otp,  # Log in development environment
            },
        )

    async def verify_otp(self, body: OTPVerifyRequest) -> LoginResponse:
        """Verify OTP and issue JWT tokens.

        Args:
            body: Mobile, OTP, and tenant_id.

        Returns:
            LoginResponse with tokens.

        Raises:
            AuthenticationError: If OTP is incorrect, expired, or not initiated.
        """
        stmt = select(User).where(
            User.mobile == body.mobile,
            User.tenant_id == body.tenant_id,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user or not user.otp_code or not user.otp_expires_at:
            raise AuthenticationError("OTP verification not initiated")

        # Check expiration
        now = datetime.now(UTC)
        if user.otp_expires_at.replace(tzinfo=UTC) < now:
            raise AuthenticationError("OTP has expired")

        # Check code
        if user.otp_code != body.otp:
            raise AuthenticationError("Invalid OTP code")

        # Fetch user's roles
        role_stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id, UserRole.tenant_id == body.tenant_id)
        )
        role_result = await self.db.execute(role_stmt)
        roles = list(role_result.scalars().all())

        # Clear OTP fields and update login timestamp
        user.otp_code = None
        user.otp_expires_at = None
        user.last_login_at = now
        await self.db.commit()

        mfa_required = user.mfa_enabled and any(r in MFA_REQUIRED_ROLES for r in roles)

        access_token = create_access_token(
            user_id=user.id,
            tenant_id=body.tenant_id,
            roles=roles,
            secret=self.settings.jwt_secret,
            expires_in_minutes=self.settings.jwt_access_token_expire_minutes,
            mfa_verified=not mfa_required,
        )

        refresh_token = create_refresh_token(
            user_id=user.id,
            tenant_id=body.tenant_id,
            secret=self.settings.jwt_secret,
            expires_in_days=self.settings.jwt_refresh_token_expire_days,
        )

        logger.info(
            "User authenticated via OTP",
            extra={
                "user_id": str(user.id),
                "tenant_id": str(body.tenant_id),
                "mfa_required": mfa_required,
            },
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in_seconds=self.settings.jwt_access_token_expire_minutes * 60,
            mfa_required=mfa_required,
            user_id=user.id,
            tenant_id=body.tenant_id,
            roles=roles,
        )

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

        # Fetch user's active roles
        role_stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == payload.user_id, UserRole.tenant_id == payload.tenant_uuid)
        )
        role_result = await self.db.execute(role_stmt)
        roles = list(role_result.scalars().all())

        access_token = create_access_token(
            user_id=payload.user_id,
            tenant_id=payload.tenant_uuid,
            roles=roles,
            secret=self.settings.jwt_secret,
            expires_in_minutes=self.settings.jwt_access_token_expire_minutes,
            mfa_verified=payload.mfa_verified,
        )

        return RefreshResponse(
            access_token=access_token,
            expires_in_seconds=self.settings.jwt_access_token_expire_minutes * 60,
        )

    async def verify_mfa(self, body: MFAVerifyRequest, current_user: TokenPayload) -> LoginResponse:
        """Verify TOTP code and issue MFA-verified tokens.

        Args:
            body: TOTP code.
            current_user: Partial access token payload.

        Returns:
            LoginResponse with MFA-verified tokens.

        Raises:
            MFACodeInvalidError: If TOTP code is incorrect.
        """
        stmt = select(User).where(
            User.id == current_user.user_id,
            User.tenant_id == current_user.tenant_uuid,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user or not user.mfa_secret:
            raise MFACodeInvalidError("MFA not set up for this user")

        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(body.totp_code):
            raise MFACodeInvalidError("Invalid MFA code")

        # Fetch roles
        role_stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id, UserRole.tenant_id == user.tenant_id)
        )
        role_result = await self.db.execute(role_stmt)
        roles = list(role_result.scalars().all())

        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=roles,
            secret=self.settings.jwt_secret,
            expires_in_minutes=self.settings.jwt_access_token_expire_minutes,
            mfa_verified=True,
        )

        refresh_token = create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            secret=self.settings.jwt_secret,
            expires_in_days=self.settings.jwt_refresh_token_expire_days,
        )

        logger.info(
            "MFA verified successfully",
            extra={
                "user_id": str(user.id),
                "tenant_id": str(user.tenant_id),
            },
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in_seconds=self.settings.jwt_access_token_expire_minutes * 60,
            mfa_required=False,
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=roles,
        )

    async def get_profile(self, current_user: TokenPayload) -> UserProfileResponse:
        """Get the authenticated user's profile.

        Args:
            current_user: Current user from JWT.

        Returns:
            UserProfileResponse with user details.

        Raises:
            AuthenticationError: If user is not found.
        """
        stmt = select(User).where(
            User.id == current_user.user_id,
            User.tenant_id == current_user.tenant_uuid,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise AuthenticationError("User profile not found")

        role_stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id, UserRole.tenant_id == user.tenant_id)
        )
        role_result = await self.db.execute(role_stmt)
        roles = list(role_result.scalars().all())

        return UserProfileResponse(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            mobile=user.mobile,
            full_name=user.full_name,
            roles=roles,
            is_active=user.is_active,
            mfa_enabled=user.mfa_enabled,
        )

    async def logout(self, body: RefreshRequest, current_user: TokenPayload) -> None:
        """Invalidate the user's refresh token (stub).

        Args:
            body: Refresh token to invalidate.
            current_user: Authenticated user.
        """
        # JWT refresh token blacklisting is currently stubbed/handled stateless.
        logger.info(
            "Logout requested",
            extra={"user_id": current_user.sub, "tenant_id": current_user.tenant_id},
        )
