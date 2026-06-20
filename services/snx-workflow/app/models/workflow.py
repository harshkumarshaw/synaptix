from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import ForeignKey, ForeignKeyConstraint, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from packages.shared.db.base import TenantScopedBase
from app.models.user import User



class WorkflowDefinition(TenantScopedBase):
    __tablename__ = "workflow_definitions"

    name: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    version: Mapped[int] = mapped_column(default=1, server_default="1", nullable=False)
    is_current: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)
    steps: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)


class WorkflowInstance(TenantScopedBase):
    __tablename__ = "workflow_instances"

    definition_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    entity_type: Mapped[str] = mapped_column(nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    current_step: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    current_assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    current_assignee_role: Mapped[Optional[str]] = mapped_column(nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, server_default="[]", nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)

    # Composite Foreign Key Constraints
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "definition_id"],
            ["workflow_definitions.tenant_id", "workflow_definitions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "current_assignee_id"],
            ["users.tenant_id", "users.id"],
            ondelete="SET NULL",
        ),
    )

    # Relationships
    definition: Mapped[WorkflowDefinition] = relationship("WorkflowDefinition", lazy="raise", overlaps="current_assignee")
    current_assignee: Mapped[Optional[User]] = relationship("User", lazy="raise", overlaps="definition")



class WorkflowTransition(TenantScopedBase):
    __tablename__ = "workflow_transitions"

    instance_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    from_step: Mapped[str] = mapped_column(nullable=False)
    to_step: Mapped[str] = mapped_column(nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )


    # Override base classes to omit updated_at and deleted_at (this table is strictly append-only)
    updated_at = None
    deleted_at = None

    # Composite Foreign Key Constraints
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "instance_id"],
            ["workflow_instances.tenant_id", "workflow_instances.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["users.tenant_id", "users.id"],
            ondelete="RESTRICT",
        ),
    )

    # Relationships
    instance: Mapped[WorkflowInstance] = relationship("WorkflowInstance", lazy="raise", overlaps="actor")
    actor: Mapped[User] = relationship("User", lazy="raise", overlaps="instance")

