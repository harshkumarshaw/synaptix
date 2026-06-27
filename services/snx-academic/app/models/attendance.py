"""
SQLAlchemy models — Phase 2 Attendance Engine.

Tables: attendance, attendance_summary, attendance_exemptions, attendance_accommodations.
All models use TenantScopedBase (id, tenant_id, created_at, updated_at, deleted_at).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class Attendance(TenantScopedBase):
    """Individual attendance record per student per event.

    One row per (tenant, event, student) — enforced by UNIQUE constraint.
    Conflict resolution (offline vs online): latest wall-clock assertion wins.
    """

    __tablename__ = "attendance"
    __table_args__ = (
        Index(
            "uq_attendance_event_student",
            "tenant_id",
            "event_id",
            "student_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused', 'medical', 'official_duty', 'exempt')",
            name="chk_attendance_status",
        ),
        CheckConstraint(
            "attendance_category IN ('theory', 'practical', 'clinical', 'doap', 'ece', 'aetcom', 'foundation_course', 'elective')",
            name="chk_attendance_category",
        ),
        CheckConstraint(
            "professional_phase IN ('Phase I', 'Phase II', 'Phase III Part I', 'Phase III Part II')",
            name="chk_attendance_professional_phase",
        ),
        CheckConstraint(
            "method IN ('manual', 'qr', 'rfid', 'face', 'gps', 'biometric')",
            name="chk_attendance_method",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    leave_request_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    attendance_category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    professional_phase: Mapped[str] = mapped_column(String(20), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")

    # Geolocation (for GPS-based attendance)
    geo_lat: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    geo_lng: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)

    # Device / QR tracking
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    qr_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exemption_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    # Conflict resolution timestamps
    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )
    original_marked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Review workflow
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit
    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)


class AttendanceSummary(TenantScopedBase):
    """Materialised attendance summary per student per course per phase per category.

    Recalculated on every attendance INSERT/UPDATE/DELETE via service layer.
    `attendance_pct` is a GENERATED ALWAYS STORED column in the DB.
    """

    __tablename__ = "attendance_summary"
    __table_args__ = (
        # Composite PK: no surrogate id; uniqueness is (tenant, student, course, phase, category)
        # NOTE: TenantScopedBase provides 'id' — but the migration uses a composite PK.
        # The migration's composite PK overrides at the DB level; here we map the columns.
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    professional_phase: Mapped[str] = mapped_column(String(20), nullable=False)
    attendance_category: Mapped[str] = mapped_column(String(30), nullable=False)

    sessions_conducted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_present: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_excused: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_official_duty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_medical: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # GENERATED ALWAYS STORED in DB — read-only from ORM perspective
    attendance_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        Computed(
            """
            CASE
                WHEN sessions_conducted = 0 THEN 0.00
                ELSE ROUND(
                    100.0 * (sessions_present + sessions_excused + sessions_official_duty + sessions_medical)::numeric
                    / sessions_conducted, 2
                )
            END
            """,
            persisted=True,
        ),
        nullable=True,
    )
    last_recalculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )


class AttendanceExemption(TenantScopedBase):
    """Principal-approved exemption for a specific student+event combination.

    Every exemption write triggers an audit_log entry (enforced in service layer).
    Exemptions are APPEND-ONLY at policy level — use soft-delete only.
    """

    __tablename__ = "attendance_exemptions"

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    event_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    exemption_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)


class AttendanceAccommodation(TenantScopedBase):
    """Threshold override for students with medical/disability accommodations.

    Constraints from AGENTS.md + implementation plan:
    - theory_threshold_override <= 75.00 (cannot RAISE the bar)
    - practical_threshold_override <= 80.00 (cannot RAISE the bar)
    Principal-level approval required; linked to workflow instance.
    """

    __tablename__ = "attendance_accommodations"
    __table_args__ = (
        CheckConstraint(
            "theory_threshold_override <= 75.00", name="chk_accommodations_theory_limit"
        ),
        CheckConstraint(
            "practical_threshold_override <= 80.00", name="chk_accommodations_practical_limit"
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[date] = mapped_column(Date, nullable=False)
    attendance_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    theory_threshold_override: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    practical_threshold_override: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    medical_certificate_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    workflow_instance_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
