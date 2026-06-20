from __future__ import annotations

from datetime import time
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from packages.shared.db.base import TenantScopedBase


class TimetableSlot(TenantScopedBase):
    __tablename__ = "timetable_slots"

    day_of_week: Mapped[int] = mapped_column(nullable=False, comment="0=Monday, 6=Sunday")
    start_time: Mapped[time] = mapped_column(nullable=False)
    end_time: Mapped[time] = mapped_column(nullable=False)
    name: Mapped[Optional[str]] = mapped_column(nullable=True)
