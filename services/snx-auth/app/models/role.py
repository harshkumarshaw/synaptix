from __future__ import annotations

import uuid
from sqlalchemy.orm import Mapped, mapped_column
from packages.shared.db.base import TenantScopedBase


class Role(TenantScopedBase):
    """SQLAlchemy model for tenant-scoped roles.

    Defines user roles like faculty, mentor, principal, dean, student, etc.
    Scoped by tenant_id and protected by RLS.
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(nullable=False)
    display_name: Mapped[str] = mapped_column(nullable=False)
    is_system_role: Mapped[bool] = mapped_column(default=False, server_default="false")
