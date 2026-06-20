from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from packages.shared.db.base import TenantScopedBase


class UserRole(TenantScopedBase):
    """SQLAlchemy model for linking users to their roles.

    Many-to-many link table mapped as a distinct model with grant metadata.
    Subject to RLS.
    """

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default="NOW()"
    )
    granted_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
