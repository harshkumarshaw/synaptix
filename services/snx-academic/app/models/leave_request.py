"""
SQLAlchemy models — Leave Management & Internship Rotation (Phase 2).

Tables: leave_requests, internship_rotations (placeholder for Phase 4 CRMI).
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class InternshipRotation(TenantScopedBase):
    """Placeholder model for Phase 4 CRMI internship rotations.

    Schema exists to support composite FK references from leave_requests.
    Full implementation deferred to Phase 4 (snx-clinical service).
    """

    __tablename__ = "internship_rotations"

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date(), nullable=False)
    end_date: Mapped[date] = mapped_column(Date(), nullable=False)
    leave_days_used: Mapped[int] = mapped_column(nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="scheduled")


class LeaveRequest(TenantScopedBase):
    """Student leave request with workflow-driven approval.

    On approval: DB trigger fn_events_after_insert_leave auto-marks
    attendance records for events within the leave window.
    On reject/cancel: attendance_service.cancel_leave_attendance() removes
    auto-generated rows (unless overwritten by manual faculty entry).
    """

    __tablename__ = "leave_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_leave_requests_tenant_id"),
        CheckConstraint(
            "leave_type IN ('medical', 'academic', 'casual', 'other')",
            name="chk_leave_requests_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="chk_leave_requests_status",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    rotation_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    leave_type: Mapped[str] = mapped_column(String(30), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    workflow_instance_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
