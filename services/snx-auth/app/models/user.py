from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class User(TenantScopedBase):
    """SQLAlchemy model for tenant-scoped users.

    Represents a user belonging to a specific tenant.
    Subject to Row Level Security (RLS) automatically filtered by tenant_id.
    """

    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(nullable=True)
    mobile: Mapped[str | None] = mapped_column(nullable=True)
    full_name: Mapped[str] = mapped_column(nullable=False)
    display_name: Mapped[str | None] = mapped_column(nullable=True)
    password_hash: Mapped[str | None] = mapped_column(nullable=True)
    mfa_secret: Mapped[str | None] = mapped_column(nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(default=False, server_default="false")
    google_sub: Mapped[str | None] = mapped_column(nullable=True)
    microsoft_sub: Mapped[str | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    consent_given_at: Mapped[datetime | None] = mapped_column(nullable=True)
    otp_code: Mapped[str | None] = mapped_column(nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
