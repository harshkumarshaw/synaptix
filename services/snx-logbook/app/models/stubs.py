from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.shared.db.base import GlobalBase, TenantScopedBase


class Tenant(GlobalBase):
    __tablename__ = "tenants"


class Student(TenantScopedBase):
    __tablename__ = "students"


class Faculty(TenantScopedBase):
    __tablename__ = "faculty"


class WorkflowDefinition(TenantScopedBase):
    __tablename__ = "workflow_definitions"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    steps: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="[]")


class WorkflowInstance(TenantScopedBase):
    __tablename__ = "workflow_instances"

    definition_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    current_step: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    current_assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    current_assignee_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    history: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")

    definition: Mapped[WorkflowDefinition] = relationship(
        "WorkflowDefinition",
        primaryjoin="and_(WorkflowInstance.definition_id==WorkflowDefinition.id, WorkflowInstance.tenant_id==WorkflowDefinition.tenant_id)",
        foreign_keys="[WorkflowInstance.tenant_id, WorkflowInstance.definition_id]",
    )

    @property
    def workflow_definition_code(self) -> str:
        return self.definition.code if self.definition else ""
