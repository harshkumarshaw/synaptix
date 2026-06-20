from __future__ import annotations

from packages.shared.db.base import TenantScopedBase


class Student(TenantScopedBase):
    __tablename__ = "students"


class WorkflowInstance(TenantScopedBase):
    __tablename__ = "workflow_instances"
