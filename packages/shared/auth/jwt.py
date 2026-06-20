"""
Synaptix JWT Utilities.

Handles JWT encoding, decoding, and validation for all services.
All services share the same JWT secret (configured via SNX_JWT_SECRET env var).

Token payload structure:
    {
        "sub": "user-uuid",
        "tenant_id": "tenant-uuid",
        "roles": ["faculty", "mentor"],
        "type": "access" | "refresh",
        "exp": <unix timestamp>,
        "iat": <unix timestamp>,
        "jti": "unique-token-id"
    }

MFA-required roles: admin, principal, dean, controller_of_examinations
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from packages.shared.errors import TokenExpiredError, TokenInvalidError
from packages.shared.logging import get_logger

logger = get_logger(__name__)

# NMC-mandated roles that require MFA before token issuance
MFA_REQUIRED_ROLES = frozenset(
    [
        "admin",
        "institution_admin",
        "principal",
        "dean",
        "controller_of_examinations",
    ]
)

ALGORITHM = "HS256"


class TokenPayload(BaseModel):
    """Validated JWT payload structure.

    Attributes:
        sub: User UUID as string.
        tenant_id: Tenant UUID as string.
        roles: List of role names the user holds.
        type: Token type — access or refresh.
        exp: Expiration timestamp.
        iat: Issued-at timestamp.
        jti: Unique token ID (for revocation tracking).
        mfa_verified: Whether MFA was verified for this session.
    """

    sub: str
    tenant_id: str
    roles: list[str] = Field(default_factory=list)
    type: Literal["access", "refresh"] = "access"
    exp: int
    iat: int
    jti: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mfa_verified: bool = False

    @property
    def user_id(self) -> uuid.UUID:
        """Parse sub as UUID."""
        return uuid.UUID(self.sub)

    @property
    def tenant_uuid(self) -> uuid.UUID:
        """Parse tenant_id as UUID."""
        return uuid.UUID(self.tenant_id)

    def requires_mfa(self) -> bool:
        """Check if any of the user's roles require MFA."""
        return bool(MFA_REQUIRED_ROLES.intersection(self.roles))


def create_access_token(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    roles: list[str],
    secret: str,
    expires_in_minutes: int = 60,
    mfa_verified: bool = False,
) -> str:
    """Create a signed JWT access token.

    Args:
        user_id: UUID of the authenticated user.
        tenant_id: UUID of the user's tenant.
        roles: List of role names.
        secret: JWT signing secret from environment.
        expires_in_minutes: Token lifetime in minutes.
        mfa_verified: Whether MFA was completed for this session.

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "roles": roles,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
        "jti": str(uuid.uuid4()),
        "mfa_verified": mfa_verified,
    }

    token = jwt.encode(payload, secret, algorithm=ALGORITHM)
    logger.info(
        "Access token issued",
        extra={
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "roles": roles,
            "expires_in_minutes": expires_in_minutes,
        },
    )
    return token


def create_refresh_token(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    secret: str,
    expires_in_days: int = 30,
) -> str:
    """Create a signed JWT refresh token.

    Refresh tokens contain minimal claims (no roles) and are used only
    to obtain new access tokens.

    Args:
        user_id: UUID of the authenticated user.
        tenant_id: UUID of the user's tenant.
        secret: JWT signing secret from environment.
        expires_in_days: Refresh token lifetime in days.

    Returns:
        Signed JWT refresh token string.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "roles": [],
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=expires_in_days)).timestamp()),
        "jti": str(uuid.uuid4()),
        "mfa_verified": False,
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str) -> TokenPayload:
    """Decode and validate a JWT token.

    Args:
        token: JWT string to decode.
        secret: JWT signing secret from environment.

    Returns:
        Validated TokenPayload instance.

    Raises:
        TokenExpiredError: If the token has expired.
        TokenInvalidError: If the token is malformed or signature is invalid.
    """
    try:
        raw = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return TokenPayload(**raw)
    except JWTError as e:
        error_str = str(e).lower()
        if "expired" in error_str:
            raise TokenExpiredError(
                "Token has expired. Please login again.",
                details={"error": str(e)},
            ) from e
        raise TokenInvalidError(
            "Token is invalid or signature verification failed.",
            details={"error": str(e)},
        ) from e
