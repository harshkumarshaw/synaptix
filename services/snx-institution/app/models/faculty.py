from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import User
from packages.shared.db.base import TenantScopedBase


class Faculty(TenantScopedBase):
    __tablename__ = "faculty"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    designation: Mapped[str] = mapped_column(nullable=False)
    employee_id: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    # Relationships
    user: Mapped[User] = relationship("User", lazy="raise")
