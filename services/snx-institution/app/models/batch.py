from __future__ import annotations

import uuid

from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class Batch(TenantScopedBase):
    __tablename__ = "batches"

    name: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    program_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
