"""
snx-auth Pydantic Schemas.

Request and response models for auth endpoints.
All models use Pydantic v2 syntax.
"""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# ============================================================================
# Request Models
# ============================================================================


class LoginRequest(BaseModel):
    """Email + password login request."""

    email: EmailStr = Field(description="User's email address")
    password: str = Field(min_length=8, description="User's password")
    tenant_id: uuid.UUID = Field(description="Institution UUID")


class OTPRequestBody(BaseModel):
    """OTP request via mobile number."""

    mobile: str = Field(
        pattern=r"^\+91[6-9]\d{9}$",
        description="Indian mobile number in +91XXXXXXXXXX format",
    )
    tenant_id: uuid.UUID = Field(description="Institution UUID")


class OTPVerifyRequest(BaseModel):
    """OTP verification request."""

    mobile: str = Field(
        pattern=r"^\+91[6-9]\d{9}$",
        description="Same mobile used in /otp/request",
    )
    otp: str = Field(min_length=4, max_length=8, description="OTP from SMS")
    tenant_id: uuid.UUID = Field(description="Institution UUID")


class RefreshRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str = Field(description="Valid refresh JWT token")


class MFAVerifyRequest(BaseModel):
    """TOTP MFA verification request."""

    totp_code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit TOTP code from authenticator app",
    )


# ============================================================================
# Response Models
# ============================================================================


class LoginResponse(BaseModel):
    """Successful login response.

    mfa_required=True means the access token is a partial token —
    the user must call /auth/mfa/verify before accessing privileged endpoints.
    """

    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in_seconds: int
    mfa_required: bool = False
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    roles: list[str]


class RefreshResponse(BaseModel):
    """Access token refresh response."""

    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in_seconds: int


class UserProfileResponse(BaseModel):
    """Current user profile response."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    email: str | None
    mobile: str | None
    full_name: str
    roles: list[str]
    is_active: bool
    mfa_enabled: bool
