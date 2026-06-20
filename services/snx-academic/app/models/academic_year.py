from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from packages.shared.db.base import TenantScopedBase


class AcademicYear(TenantScopedBase):
    __tablename__ = "academic_years"

    name: Mapped[str] = mapped_column(nullable=False)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    is_current: Mapped[bool] = mapped_column(default=False, server_default="false")
