"""
SQLAlchemy models — Phase 2 Electives (A-08).

Tables: electives, elective_allocations, student_elective_preferences.
NMC CBME 2023 only: two elective blocks (Block 1, Block 2) in Phase III.
75% attendance required per elective block; logbook submission mandatory for NExT.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import TenantScopedBase


class Elective(TenantScopedBase):
    """An elective module offered within a curriculum block.

    NMC CBME 2023 §6.4: two elective blocks of 4 weeks each, post-Phase III Part I exam.
    capacity: max students; coordinator tracks over-subscription.
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


class ElectiveAllocation(TenantScopedBase):
    """Confirmed allocation of a student to an elective block.

    UNIQUE (tenant_id, student_id, block) — one elective per block per student.
    Created by admin/HOD after preference ranking is processed.
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
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    elective_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    block: Mapped[str] = mapped_column(String(10), nullable=False)
    allocated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)


class StudentElectivePreference(TenantScopedBase):
    """Student preference ranking for elective allocation.

    Each student ranks electives 1–10 per block.
    UNIQUE (tenant_id, student_id, block, rank_position) — no two choices at same rank.
    UNIQUE (tenant_id, student_id, block, elective_id) — no duplicate elective in same block.
    """

    __tablename__ = "student_elective_preferences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_student_elective_preferences_id"),
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "block",
            "rank_position",
            name="uq_elective_preferences_rank",
        ),
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "block",
            "elective_id",
            name="uq_elective_preferences_elective",
        ),
        CheckConstraint("block IN ('Block 1', 'Block 2')", name="chk_elective_preferences_block"),
        CheckConstraint(
            "rank_position BETWEEN 1 AND 10", name="chk_elective_preferences_rank_range"
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    elective_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    block: Mapped[str] = mapped_column(String(10), nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
