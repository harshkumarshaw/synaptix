from __future__ import annotations

import uuid
from typing import Any

from app.models.curriculum import Curriculum
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.shared.db.base import TenantScopedBase


class MasterDataEntity(TenantScopedBase):
    __tablename__ = "master_data_entities"

    curriculum_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    category: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    extra_attributes: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)

    # Composite Foreign Key Constraint
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="SET NULL",
        ),
    )

    # Relationships
    curriculum: Mapped[Curriculum | None] = relationship("Curriculum", lazy="raise")
