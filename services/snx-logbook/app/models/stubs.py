from __future__ import annotations

from packages.shared.db.base import GlobalBase, TenantScopedBase


class Tenant(GlobalBase):
    __tablename__ = "tenants"


class Student(TenantScopedBase):
    __tablename__ = "students"


class Faculty(TenantScopedBase):
    __tablename__ = "faculty"
