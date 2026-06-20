from __future__ import annotations

import uuid
from sqlalchemy.orm import Mapped, mapped_column
from packages.shared.db.base import TenantScopedBase


class Section(TenantScopedBase):
    __tablename__ = "sections"

    batch_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
