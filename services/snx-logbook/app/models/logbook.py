from __future__ import annotations

import datetime
import uuid
from typing import Optional
from sqlalchemy import ForeignKey, ForeignKeyConstraint, Numeric, String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from packages.shared.db.base import TenantScopedBase


class FoundationCourseRecord(TenantScopedBase):
    __tablename__ = "foundation_course_records"

    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    module_name: Mapped[str] = mapped_column(String(100), nullable=False)
    completed_hours: Mapped[float] = mapped_column(Numeric(4, 2), default=0.0, server_default="0.0", nullable=False)
    required_hours: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    is_completed: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    signoff_received_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    signed_off_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "signed_off_by"],
            ["faculty.tenant_id", "faculty.id"],
            ondelete="RESTRICT"
        ),
    )


class AetcomRecord(TenantScopedBase):
    __tablename__ = "aetcom_records"

    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    module_code: Mapped[str] = mapped_column(String(30), nullable=False)
    competency_code: Mapped[str] = mapped_column(String(50), nullable=False)
    professional_phase: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", nullable=False)
    reflection_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signed_off_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    signed_off_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "signed_off_by"],
            ["faculty.tenant_id", "faculty.id"],
            ondelete="RESTRICT"
        ),
    )
