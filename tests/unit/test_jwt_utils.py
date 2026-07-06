"""
Unit Tests — JWT Utilities.

Tests for packages/shared/auth/jwt.py.
These tests do NOT require a database connection.

Manifest IDs: AUTH-003, AUTH-004
"""

from __future__ import annotations

import uuid

import pytest
from freezegun import freeze_time

from packages.shared.auth.jwt import (
    MFA_REQUIRED_ROLES,
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from packages.shared.errors import TokenExpiredError, TokenInvalidError

# Test constants
TEST_SECRET = "test_secret_must_be_long_enough_for_hs256_at_least_32_chars"
TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")  # JMN


class TestCreateAccessToken:
    """Tests for create_access_token()."""

    @pytest.mark.unit
    def test_creates_valid_jwt_string(self) -> None:
        """create_access_token returns a non-empty JWT string."""
        token = create_access_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            roles=["faculty"],
            secret=TEST_SECRET,
        )
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT has 3 parts separated by dots
        assert token.count(".") == 2

    @pytest.mark.unit
    def test_token_contains_user_id(self) -> None:
        """Decoded token contains the correct user_id."""
        token = create_access_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            roles=["faculty"],
            secret=TEST_SECRET,
        )
        payload = decode_token(token, TEST_SECRET)
        assert payload.user_id == TEST_USER_ID

    @pytest.mark.unit
    def test_token_contains_tenant_id(self) -> None:
        """Decoded token contains the correct tenant_id."""
        token = create_access_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            roles=["faculty"],
            secret=TEST_SECRET,
        )
        payload = decode_token(token, TEST_SECRET)
        assert payload.tenant_uuid == TEST_TENANT_ID

    @pytest.mark.unit
    def test_token_type_is_access(self) -> None:
        """Access token has type='access'."""
        token = create_access_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            roles=["faculty"],
            secret=TEST_SECRET,
        )
        payload = decode_token(token, TEST_SECRET)
        assert payload.type == "access"

    @pytest.mark.unit
    def test_token_contains_roles(self) -> None:
        """Decoded token contains the correct roles."""
        roles = ["faculty", "mentor"]
        token = create_access_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            roles=roles,
            secret=TEST_SECRET,
        )
        payload = decode_token(token, TEST_SECRET)
        assert set(payload.roles) == set(roles)

    @pytest.mark.unit
    def test_mfa_not_verified_by_default(self) -> None:
        """MFA is not verified by default in access tokens."""
        token = create_access_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            roles=["faculty"],
            secret=TEST_SECRET,
        )
        payload = decode_token(token, TEST_SECRET)
        assert payload.mfa_verified is False

    @pytest.mark.unit
    def test_mfa_verified_when_specified(self) -> None:
        """MFA verified flag is set when specified."""
        token = create_access_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            roles=["principal"],
            secret=TEST_SECRET,
            mfa_verified=True,
        )
        payload = decode_token(token, TEST_SECRET)
        assert payload.mfa_verified is True


class TestCreateRefreshToken:
    """Tests for create_refresh_token()."""

    @pytest.mark.unit
    def test_refresh_token_type_is_refresh(self) -> None:
        """Refresh token has type='refresh'."""
        token = create_refresh_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            secret=TEST_SECRET,
        )
        payload = decode_token(token, TEST_SECRET)
        assert payload.type == "refresh"

    @pytest.mark.unit
    def test_refresh_token_has_no_roles(self) -> None:
        """Refresh tokens contain empty roles list."""
        token = create_refresh_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            secret=TEST_SECRET,
        )
        payload = decode_token(token, TEST_SECRET)
        assert payload.roles == []


class TestDecodeToken:
    """Tests for decode_token()."""

    @pytest.mark.unit
    def test_invalid_signature_raises_token_invalid_error(self) -> None:
        """Tampered token signature raises TokenInvalidError."""
        token = create_access_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            roles=["faculty"],
            secret=TEST_SECRET,
        )
        wrong_secret = "completely_different_secret_that_is_also_long_enough_32chars"
        with pytest.raises(TokenInvalidError):
            decode_token(token, wrong_secret)

    @pytest.mark.unit
    def test_malformed_token_raises_token_invalid_error(self) -> None:
        """Malformed JWT string raises TokenInvalidError."""
        with pytest.raises(TokenInvalidError):
            decode_token("not.a.valid.jwt.token", TEST_SECRET)

    @pytest.mark.unit
    @freeze_time("2026-06-20 00:00:00")
    def test_expired_token_raises_token_expired_error(self) -> None:
        """Expired token raises TokenExpiredError (not TokenInvalidError)."""
        token = create_access_token(
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            roles=["faculty"],
            secret=TEST_SECRET,
            expires_in_minutes=1,  # expires in 1 minute
        )
        # Travel 2 minutes into the future
        with freeze_time("2026-06-20 00:02:00"), pytest.raises(TokenExpiredError):
            decode_token(token, TEST_SECRET)

    @pytest.mark.unit
    def test_empty_string_raises_token_invalid_error(self) -> None:
        """Empty token string raises TokenInvalidError."""
        with pytest.raises(TokenInvalidError):
            decode_token("", TEST_SECRET)


class TestMFARequiredRoles:
    """Tests for MFA requirement logic."""

    @pytest.mark.unit
    def test_principal_requires_mfa(self) -> None:
        """Principal role requires MFA."""
        assert "principal" in MFA_REQUIRED_ROLES

    @pytest.mark.unit
    def test_dean_requires_mfa(self) -> None:
        """Dean role requires MFA."""
        assert "dean" in MFA_REQUIRED_ROLES

    @pytest.mark.unit
    def test_controller_of_examinations_requires_mfa(self) -> None:
        """Controller of Examinations role requires MFA."""
        assert "controller_of_examinations" in MFA_REQUIRED_ROLES

    @pytest.mark.unit
    def test_faculty_does_not_require_mfa(self) -> None:
        """Faculty role does NOT require MFA."""
        assert "faculty" not in MFA_REQUIRED_ROLES

    @pytest.mark.unit
    def test_student_does_not_require_mfa(self) -> None:
        """Student role does NOT require MFA."""
        assert "student" not in MFA_REQUIRED_ROLES

    @pytest.mark.unit
    def test_token_payload_requires_mfa_for_principal(self) -> None:
        """TokenPayload.requires_mfa() returns True for principal role."""
        payload = TokenPayload(
            sub=str(TEST_USER_ID),
            tenant_id=str(TEST_TENANT_ID),
            roles=["principal"],
            type="access",
            exp=9999999999,
            iat=1000000000,
        )
        assert payload.requires_mfa() is True

    @pytest.mark.unit
    def test_token_payload_does_not_require_mfa_for_faculty(self) -> None:
        """TokenPayload.requires_mfa() returns False for faculty role."""
        payload = TokenPayload(
            sub=str(TEST_USER_ID),
            tenant_id=str(TEST_TENANT_ID),
            roles=["faculty"],
            type="access",
            exp=9999999999,
            iat=1000000000,
        )
        assert payload.requires_mfa() is False
