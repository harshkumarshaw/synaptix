import uuid

from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class Student(TenantScopedBase):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column()


class WorkflowInstance(TenantScopedBase):
    __tablename__ = "workflow_instances"
