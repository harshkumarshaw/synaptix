"""
SQLAlchemy models — Phase 2 Electives (A-08).

Tables:
  - electives                    (offering of an elective in a curriculum block)
  - elective_allocation_runs     (audit trail for each admin-triggered allocation run — ADR-034)
  - elective_allocations         (confirmed student → elective assignments)
  - student_elective_preferences (student's ranked preference list per block)

NMC CBME 2023 only: two elective blocks (Block 1, Block 2) in Phase III.
75% attendance required per elective block; logbook submission mandatory for NExT.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class Elective(TenantScopedBase):
    """An elective module offered within a curriculum block.

    NMC CBME 2023 §6.4: two elective blocks of 4 weeks each, post-Phase III Part I exam.
    capacity: max students; coordinator tracks over-subscription.
    block_duration_weeks: must be 2 per NMC regulation (ELEC-NMC-001).
    """

    __tablename__ = "electives"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_electives_tenant_id"),
        UniqueConstraint("tenant_id", "curriculum_id", "code", name="uq_electives_code"),
        CheckConstraint("block IN ('Block 1', 'Block 2')", name="chk_electives_block"),
        CheckConstraint(
            "elective_type IN ('pre_clinical', 'para_clinical', 'clinical', 'community', 'research')",
            name="chk_electives_type",
        ),
    )

    curriculum_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    block: Mapped[str] = mapped_column(String(10), nullable=False)
    elective_type: Mapped[str] = mapped_column(String(30), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)


class ElectiveAllocationRun(TenantScopedBase):
    """Audit trail for each admin-triggered elective allocation run.

    ADR-034: Every live run_allocation call produces exactly 1 row here.
    Dry-run calls produce NO row (is_dry_run is tracked in response only).
    results_summary JSONB: {"rank_1": 9, "rank_2": 1, "fcfs": 0, "manual": 0}
    """

    __tablename__ = "elective_allocation_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_elective_allocation_runs_tenant_id"),
        CheckConstraint(
            "block IN ('Block 1', 'Block 2')", name="chk_allocation_runs_block"
        ),
        CheckConstraint(
            "algorithm_used IN ('fcfs', 'ranked')", name="chk_allocation_runs_algorithm"
        ),
        CheckConstraint(
            "force_reallocate IN ('additive', 'full') OR force_reallocate IS NULL",
            name="chk_allocation_runs_force_reallocate",
        ),
    )

    curriculum_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    block: Mapped[str] = mapped_column(String(10), nullable=False)
    algorithm_used: Mapped[str] = mapped_column(String(20), nullable=False)
    triggered_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )
    is_dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    force_reallocate: Mapped[str | None] = mapped_column(String(20), nullable=True)

    total_students: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_allocated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_unallocated_pending_review: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    run_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    results_summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class ElectiveAllocation(TenantScopedBase):
    """Confirmed allocation of a student to an elective block.

    UNIQUE (tenant_id, student_id, block) — one elective per block per student.
    allocation_run_id: NULL for manually created allocations (outside automated run).
    allocation_method: how the student was allocated ('rank_1'..'rank_10', 'fcfs', 'manual').
    """

    __tablename__ = "elective_allocations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "block",
            name="uq_elective_allocations_student_block",
        ),
        CheckConstraint("block IN ('Block 1', 'Block 2')", name="chk_elective_allocations_block"),
        CheckConstraint(
            "allocation_method IN ('rank_1','rank_2','rank_3','rank_4','rank_5',"
            "'rank_6','rank_7','rank_8','rank_9','rank_10','fcfs','manual') "
            "OR allocation_method IS NULL",
            name="chk_elective_allocations_method",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    elective_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    block: Mapped[str] = mapped_column(String(10), nullable=False)
    allocated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    # Migration 0014 additions:
    allocation_run_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    allocation_method: Mapped[str | None] = mapped_column(String(20), nullable=True)


class StudentElectivePreference(TenantScopedBase):
    """Student preference ranking for elective allocation.

    Each student ranks electives 1–10 per block.
    submitted_at: used for FCFS ordering and ranked-algorithm tie-breaking.
    Full-block replace semantics: re-submission soft-deletes previous set.

    Unique constraints enforced via partial unique indexes in migration 0012:
    - uq_elective_preferences_rank: (tenant_id, student_id, block, rank_position) WHERE deleted_at IS NULL
    - uq_elective_preferences_elective: (tenant_id, student_id, block, elective_id) WHERE deleted_at IS NULL
    (Partial indexes not expressible as table-level UniqueConstraints in SQLAlchemy ORM;
     enforced at DB level only.)
    """

    __tablename__ = "student_elective_preferences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_student_elective_preferences_id"),
        CheckConstraint("block IN ('Block 1', 'Block 2')", name="chk_elective_preferences_block"),
        CheckConstraint(
            "rank_position BETWEEN 1 AND 10", name="chk_elective_preferences_rank_range"
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    elective_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    block: Mapped[str] = mapped_column(String(10), nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    # Migration 0014 addition:
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )
