from __future__ import annotations

import uuid
from typing import Any
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db.base import Base, TenantScopedBase, TimestampMixin


class Examination(TenantScopedBase):
    """An examination offering for a specific curriculum phase and course."""

    __tablename__ = "examinations"

    curriculum_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    exam_type: Mapped[str] = mapped_column(String(30), nullable=False)
    exam_session: Mapped[str] = mapped_column(String(50), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    theory_max_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    practical_max_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    theory_pass_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    practical_pass_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    grace_marks_allowed: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="scheduled", server_default="scheduled"
    )
    workflow_instance_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_examinations_tenant_id"),
        CheckConstraint(
            "exam_type IN ('terminal', 'professional', 'supplementary')",
            name="chk_examinations_exam_type",
        ),
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'results_published')",
            name="chk_examinations_status",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "curriculum_id"],
            ["curricula.tenant_id", "curricula.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["workflow_instances.tenant_id", "workflow_instances.id"],
            ondelete="SET NULL",
        ),
    )


class ExamSchedule(TenantScopedBase):
    """The schedule details for an examination including room and invigilator."""

    __tablename__ = "exam_schedules"

    examination_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    invigilator_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_exam_schedules_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "examination_id"],
            ["examinations.tenant_id", "examinations.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "invigilator_id"],
            ["faculty.tenant_id", "faculty.user_id"],
            ondelete="RESTRICT",
        ),
    )


class VivaScore(TenantScopedBase):
    """Marks obtained by a student in the viva voce component of a course."""

    __tablename__ = "viva_scores"

    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    professional_phase: Mapped[str] = mapped_column(String(30), nullable=False)
    examiner_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    conducted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_viva_scores_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "examiner_id"],
            ["faculty.tenant_id", "faculty.user_id"],
            ondelete="RESTRICT",
        ),
    )


class PracticalAssessment(TenantScopedBase):
    """Marks obtained by a student in the practical assessment of a course."""

    __tablename__ = "practical_assessments"

    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    professional_phase: Mapped[str] = mapped_column(String(30), nullable=False)
    examiner_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    conducted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_practical_assessments_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "examiner_id"],
            ["faculty.tenant_id", "faculty.user_id"],
            ondelete="RESTRICT",
        ),
    )


class ClinicalEvaluation(TenantScopedBase):
    """Marks obtained by a student in clinical evaluations."""

    __tablename__ = "clinical_evaluations"

    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    professional_phase: Mapped[str] = mapped_column(String(30), nullable=False)
    evaluator_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    posting_period: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_clinical_evaluations_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "evaluator_id"],
            ["faculty.tenant_id", "faculty.user_id"],
            ondelete="RESTRICT",
        ),
    )


class IAAggregation(Base, TimestampMixin):
    """Aggregated Internal Assessment (IA) marks for eligibility check."""

    __tablename__ = "ia_aggregation"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, primary_key=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False, primary_key=True)
    course_id: Mapped[uuid.UUID] = mapped_column(nullable=False, primary_key=True)
    professional_phase: Mapped[str] = mapped_column(String(30), nullable=False, primary_key=True)

    logbook_marks: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default="0.00"
    )
    viva_marks: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default="0.00"
    )
    practical_marks: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default="0.00"
    )
    clinical_marks: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default="0.00"
    )
    total_ia: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default="0.00"
    )
    ia_max: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00"), server_default="0.00"
    )
    is_eligible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "course_id"],
            ["courses.tenant_id", "courses.id"],
            ondelete="RESTRICT",
        ),
    )


class ExamEligibility(Base):
    """The eligibility status of a student for a specific examination."""

    __tablename__ = "exam_eligibility"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, primary_key=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False, primary_key=True)
    examination_id: Mapped[uuid.UUID] = mapped_column(nullable=False, primary_key=True)

    is_eligible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    blocking_reasons: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    checked_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "examination_id"],
            ["examinations.tenant_id", "examinations.id"],
            ondelete="CASCADE",
        ),
    )


class ExamResult(TenantScopedBase):
    """Graded result of a student's attempt at an examination."""

    __tablename__ = "exam_results"

    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    examination_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    theory_marks: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    practical_marks: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    ia_marks: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    total_marks: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    theory_grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    practical_grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    overall_grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    grace_marks_applied: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="draft", server_default="draft"
    )
    workflow_instance_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_exam_results_tenant_id"),
        CheckConstraint(
            "status IN ('draft', 'verified', 'approved', 'published')",
            name="chk_exam_results_status",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "examination_id"],
            ["examinations.tenant_id", "examinations.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "workflow_instance_id"],
            ["workflow_instances.tenant_id", "workflow_instances.id"],
            ondelete="SET NULL",
        ),
    )


class ExamModeration(TenantScopedBase):
    """Double-marker/Moderator details for an exam result evaluation."""

    __tablename__ = "exam_moderation"

    exam_result_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    examiner_1_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    examiner_2_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    examiner_3_marks: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    moderation_method: Mapped[str] = mapped_column(String(50), nullable=False)
    final_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_exam_moderation_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "exam_result_id"],
            ["exam_results.tenant_id", "exam_results.id"],
            ondelete="CASCADE",
        ),
    )


class MarkSheet(TenantScopedBase):
    """Academic mark sheet PDF generation tracking and verification metadata."""

    __tablename__ = "mark_sheets"

    student_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    semester: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pdf_asset_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    qr_verification_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    generated_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_mark_sheets_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "pdf_asset_id"],
            ["digital_assets.tenant_id", "digital_assets.id"],
            ondelete="RESTRICT",
        ),
    )


class QuestionPaper(TenantScopedBase):
    """Exam question papers generated, verified, and locked by controllers."""

    __tablename__ = "question_papers"

    examination_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    paper_type: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    asset_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="draft", server_default="draft"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_question_papers_tenant_id"),
        CheckConstraint(
            "paper_type IN ('theory', 'practical', 'viva')",
            name="chk_question_papers_paper_type",
        ),
        CheckConstraint(
            "status IN ('draft', 'approved', 'locked')",
            name="chk_question_papers_status",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "examination_id"],
            ["examinations.tenant_id", "examinations.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "asset_id"],
            ["digital_assets.tenant_id", "digital_assets.id"],
            ondelete="RESTRICT",
        ),
    )
