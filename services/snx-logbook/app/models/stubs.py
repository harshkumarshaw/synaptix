from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import GlobalBase, TenantScopedBase


class Tenant(GlobalBase):
    __tablename__ = "tenants"


class Student(TenantScopedBase):
    __tablename__ = "students"


class Faculty(TenantScopedBase):
    __tablename__ = "faculty"


class WorkflowInstance(TenantScopedBase):
    __tablename__ = "workflow_instances"

    workflow_definition_code: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    initiated_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
