from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from packages.shared.db.base import TenantScopedBase


class User(TenantScopedBase):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
