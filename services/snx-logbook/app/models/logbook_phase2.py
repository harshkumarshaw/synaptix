"""
SQLAlchemy models — Phase 2 Digital Logbook & DOAP (A-09, A-10).

Tables: logbook_entries (Phase 2 full), logbook_assessments, doap_session_records.

Unified logbook: regular and elective logbook entries share logbook_entries table.
Separation enforced by CHECK: (elective_id IS NULL AND subject_code IS NOT NULL) OR
                               (elective_id IS NOT NULL AND subject_code IS NULL)
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class LogbookEntry(TenantScopedBase):
    """Digital logbook entry per student per competency activity.

    Unified regular + elective logbook.
    - Regular: elective_id=NULL, subject_code=NOT NULL
    - Elective: elective_id=NOT NULL, subject_code=NULL
    NMC CBME 2019/2023: NMC levels K/KH/SH/P; DOAP stage D/O/A/P.
    """

    __tablename__ = "logbook_entries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_logbook_entries_tenant_id"),
        CheckConstraint(
            "((elective_id IS NULL AND subject_code IS NOT NULL) OR "
            "(elective_id IS NOT NULL AND subject_code IS NULL))",
            name="chk_logbook_entries_elective",
        ),
        CheckConstraint(
            "nmc_level IN ('K', 'KH', 'SH', 'P')", name="chk_logbook_entries_nmc_level"
        ),
        CheckConstraint("rating IN ('B', 'M', 'E')", name="chk_logbook_entries_rating"),
        CheckConstraint(
            "attempt_type IN ('F', 'R', 'Re')", name="chk_logbook_entries_attempt_type"
        ),
        CheckConstraint(
            "faculty_decision IN ('C', 'R', 'Re')", name="chk_logbook_entries_faculty_decision"
        ),
        CheckConstraint(
            "status IN ('pending', 'submitted', 'approved', 'rejected')",
            name="chk_logbook_entries_status",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    elective_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    subject_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    professional_phase: Mapped[str] = mapped_column(String(20), nullable=False)
    competency_code: Mapped[str] = mapped_column(String(50), nullable=False)
    nmc_level: Mapped[str] = mapped_column(String(2), nullable=False)
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    activity_name: Mapped[str] = mapped_column(String(150), nullable=False)
    reflection: Mapped[str | None] = mapped_column(Text, nullable=True)

    # DOAP / logbook assessment fields
    rating: Mapped[str | None] = mapped_column(String(10), nullable=True)  # B/M/E
    attempt_type: Mapped[str | None] = mapped_column(String(10), nullable=True)  # F/R/Re
    faculty_decision: Mapped[str | None] = mapped_column(String(10), nullable=True)  # C/R/Re
    faculty_initials: Mapped[str | None] = mapped_column(String(10), nullable=True)
    student_initials: Mapped[str | None] = mapped_column(String(10), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    backdated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    backdating_approved_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    signed_off_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    signed_off_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)


class LogbookAssessment(TenantScopedBase):
    """Aggregate logbook IA assessment per student per subject per phase.

    ia_marks_pct: computed from signed-off entries / total required entries.
    ia_marks_awarded: = ia_marks_pct * subject_ia_max / 100 (set by logbook_service).
    is_complete triggers certificate eligibility for NExT.
    """

    __tablename__ = "logbook_assessments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_logbook_assessments_id"),
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "subject_code",
            "professional_phase",
            name="uq_logbook_assessments_student_subject_phase",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    subject_code: Mapped[str] = mapped_column(String(50), nullable=False)
    professional_phase: Mapped[str] = mapped_column(String(20), nullable=False)

    total_entries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_entries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ia_marks_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    ia_marks_awarded: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, default=Decimal("0.00")
    )
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    signed_off_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    signed_off_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)


class DoapSessionRecord(TenantScopedBase):
    """DOAP (Demonstration of Acquired Proficiency) sign-off record per student per session.

    NMC CBME 2019/2023 A-09: DOAP sessions require faculty sign-off with
    stage rating (D=Demonstrates, O=Observes, A=Assists, P=Performs independently).
    One record per student per session per competency.
    """

    __tablename__ = "doap_session_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_doap_session_records_id"),
        CheckConstraint("nmc_level IN ('K', 'KH', 'SH', 'P')", name="chk_doap_nmc_level"),
        CheckConstraint("stage IN ('D', 'O', 'A', 'P')", name="chk_doap_stage"),
        CheckConstraint("rating IN ('B', 'M', 'E')", name="chk_doap_rating"),
        CheckConstraint("attempt_type IN ('F', 'R', 'Re')", name="chk_doap_attempt_type"),
        CheckConstraint("faculty_decision IN ('C', 'R', 'Re')", name="chk_doap_faculty_decision"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    competency_code: Mapped[str] = mapped_column(String(50), nullable=False)
    nmc_level: Mapped[str] = mapped_column(String(2), nullable=False)
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    stage: Mapped[str] = mapped_column(String(10), nullable=False)
    rating: Mapped[str] = mapped_column(String(10), nullable=False)
    attempt_type: Mapped[str] = mapped_column(String(10), nullable=False)
    faculty_decision: Mapped[str] = mapped_column(String(10), nullable=False)
    faculty_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evidence_asset_ids: Mapped[list[uuid.UUID]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    signed_off_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )
