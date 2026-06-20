import uuid
from datetime import datetime, timezone, timedelta
import pytest
import pyotp
import bcrypt
from sqlalchemy import select

from packages.shared.errors import AuthenticationError, MFACodeInvalidError
from packages.shared.auth.jwt import decode_token, TokenPayload
from app.services.auth_service import AuthService
from app.models.user import User
from app.models.tenant import Tenant
from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas.auth import (
    LoginRequest,
    OTPRequestBody,
    OTPVerifyRequest,
    MFAVerifyRequest,
    RefreshRequest,
)

@pytest.mark.anyio
async def test_auth_service_flows(db_session, app_settings, tenant_id):
    """Test full AuthService flow: password login, OTP request/verify, MFA, profile."""
    auth_service = AuthService(db_session, app_settings)

    # 1. Create a test tenant in db (if not exists)
    tenant = await db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(
            id=tenant_id,
            code="JMN",
            name="JMN Medical College",
            institution_type="medical",
            regulatory_body="NMC",
        )
        db_session.add(tenant)
        await db_session.commit()

    # 2. Create a test role
    role_name = "principal"
    role_stmt = select(Role).where(Role.name == role_name, Role.tenant_id == tenant_id)
    role_res = await db_session.execute(role_stmt)
    role = role_res.scalars().first()
    if not role:
        role = Role(
            tenant_id=tenant_id,
            name=role_name,
            display_name="Principal",
            is_system_role=True,
        )
        db_session.add(role)
        await db_session.commit()

    # 3. Create a test user
    user_email = "test_faculty@jmn.edu"
    user_mobile = "+919876543210"
    user_password = "securepassword123"
    
    # Clean up existing user if any
    cleanup_stmt = select(User).where(User.email == user_email, User.tenant_id == tenant_id)
    cleanup_res = await db_session.execute(cleanup_stmt)
    existing_user = cleanup_res.scalars().first()
    if existing_user:
        await db_session.delete(existing_user)
        await db_session.commit()

    mfa_secret = pyotp.random_base32()
    user = User(
        tenant_id=tenant_id,
        email=user_email,
        mobile=user_mobile,
        full_name="Dr. Test Faculty",
        password_hash=bcrypt.hashpw(user_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        mfa_secret=mfa_secret,
        mfa_enabled=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Link user to role
    user_role = UserRole(
        tenant_id=tenant_id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(user_role)
    await db_session.commit()

    # Refresh user reference
    await db_session.refresh(user)

    # ── Test A: Login with invalid password ──
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.login(
            LoginRequest(
                email=user_email,
                password="wrongpassword",
                tenant_id=tenant_id,
            )
        )
    assert "invalid email or password" in str(exc_info.value).lower()

    # ── Test B: Successful Login with password ──
    login_response = await auth_service.login(
        LoginRequest(
            email=user_email,
            password=user_password,
            tenant_id=tenant_id,
        )
    )
    assert login_response.user_id == user.id
    assert login_response.tenant_id == tenant_id
    assert role_name in login_response.roles
    assert login_response.mfa_required is True  # Faculty role with mfa_enabled=True requires MFA

    # Validate access token
    payload = decode_token(login_response.access_token, app_settings.jwt_secret)
    assert payload.user_id == user.id
    assert payload.mfa_verified is False  # Partially authenticated

    # ── Test C: Request OTP ──
    await auth_service.request_otp(
        OTPRequestBody(
            mobile=user_mobile,
            tenant_id=tenant_id,
        )
    )
    # Reload user from DB to check OTP
    await db_session.refresh(user)
    assert user.otp_code is not None
    assert user.otp_expires_at > datetime.now(timezone.utc)

    # ── Test D: Verify OTP ──
    otp_response = await auth_service.verify_otp(
        OTPVerifyRequest(
            mobile=user_mobile,
            otp=user.otp_code,
            tenant_id=tenant_id,
        )
    )
    assert otp_response.user_id == user.id
    assert otp_response.mfa_required is True  # MFA still required

    # Check OTP was cleared
    await db_session.refresh(user)
    assert user.otp_code is None
    assert user.otp_expires_at is None

    # ── Test E: Verify MFA TOTP ──
    totp = pyotp.TOTP(mfa_secret)
    totp_code = totp.now()

    mfa_response = await auth_service.verify_mfa(
        MFAVerifyRequest(totp_code=totp_code),
        payload,  # Pass the partial token payload
    )
    assert mfa_response.user_id == user.id
    assert mfa_response.mfa_required is False

    # Validate access token has mfa_verified=True
    mfa_payload = decode_token(mfa_response.access_token, app_settings.jwt_secret)
    assert mfa_payload.mfa_verified is True

    # ── Test F: Get User Profile ──
    profile = await auth_service.get_profile(mfa_payload)
    assert profile.user_id == user.id
    assert profile.email == user_email
    assert profile.mobile == user_mobile
    assert role_name in profile.roles
    assert profile.mfa_enabled is True
