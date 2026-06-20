from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from packages.shared.db.base import TenantScopedBase


class Department(TenantScopedBase):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(nullable=False)
