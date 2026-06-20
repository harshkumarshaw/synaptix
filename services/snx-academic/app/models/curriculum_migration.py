from __future__ import annotations

import datetime
import uuid
from typing import Optional, Any
from sqlalchemy import ForeignKey, ForeignKeyConstraint, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from packages.shared.db.base import TenantScopedBase
from app.models.user import User

class CurriculumMigrationAudit(TenantScopedBase):
    __tablename__ = "curriculum_migration_audits"

    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    from_curriculum_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    to_curriculum_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    migrated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now, nullable=False)
    approved_by: Mapped[uuid.UUID] = mapped_column(nullable=False)
    migration_details: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "from_curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "to_curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "approved_by"],
            ["users.tenant_id", "users.id"],
            ondelete="RESTRICT"
        ),
    )

    approver: Mapped[User] = relationship("User", lazy="raise")
