from __future__ import annotations


import uuid
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class Course(TenantScopedBase):
    __tablename__ = "courses"

    curriculum_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("curricula.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    default_attendance_category: Mapped[str] = mapped_column(
        nullable=False, server_default="theory"
    )
    subject_code: Mapped[str] = mapped_column(nullable=False)

    def __init__(self, **kwargs: Any) -> None:
        if "subject_code" not in kwargs and "code" in kwargs:
            kwargs["subject_code"] = kwargs["code"].split("-")[0]
        super().__init__(**kwargs)
