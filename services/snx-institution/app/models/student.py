from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import User
from packages.shared.db.base import TenantScopedBase


class Student(TenantScopedBase):
    __tablename__ = "students"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("batches.id", ondelete="RESTRICT"), nullable=False
    )
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sections.id", ondelete="SET NULL"), nullable=True
    )
    roll_number: Mapped[str] = mapped_column(nullable=False)
    admission_year: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(default="active", server_default="active")

    # Relationships
    user: Mapped[User] = relationship("User", lazy="raise")
