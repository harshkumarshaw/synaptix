from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ExaminationCreate(BaseModel):
    curriculum_id: uuid.UUID
    course_id: uuid.UUID
    exam_type: str
    exam_session: str
    academic_year: str
    exam_date: date
    theory_max_marks: int
    practical_max_marks: int
    theory_pass_marks: int
    practical_pass_marks: int
    grace_marks_allowed: int = 5


class ExaminationResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    curriculum_id: uuid.UUID
    course_id: uuid.UUID
    exam_type: str
    exam_session: str
    academic_year: str
    exam_date: date
    theory_max_marks: int
    practical_max_marks: int
    theory_pass_marks: int
    practical_pass_marks: int
    grace_marks_allowed: int
    status: str

    class Config:
        from_attributes = True


class ExamScheduleCreate(BaseModel):
    room_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    invigilator_id: uuid.UUID


class ExamScheduleResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    examination_id: uuid.UUID
    room_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    invigilator_id: uuid.UUID

    class Config:
        from_attributes = True


class IAAggregationRequest(BaseModel):
    student_id: uuid.UUID
    course_id: uuid.UUID
    professional_phase: str


class IAAggregationResponse(BaseModel):
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID
    professional_phase: str
    logbook_marks: Decimal
    viva_marks: Decimal
    practical_marks: Decimal
    clinical_marks: Decimal
    total_ia: Decimal
    ia_max: Decimal
    is_eligible: bool

    class Config:
        from_attributes = True


class ExamEligibilityResponse(BaseModel):
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    examination_id: uuid.UUID
    is_eligible: bool
    blocking_reasons: list[dict[str, Any]] | None = None
    checked_at: datetime
    checked_by: uuid.UUID | None = None

    class Config:
        from_attributes = True


class EligibilityOverrideRequest(BaseModel):
    student_id: uuid.UUID
    reason: str


# ---------------------------------------------------------------------------
# R4.3 — Result Processing Schemas
# ---------------------------------------------------------------------------


class ExamResultSubmit(BaseModel):
    """Request body for examiner submitting marks."""

    student_id: uuid.UUID
    examination_id: uuid.UUID
    theory_marks: Decimal = Field(..., ge=0, description="Raw theory marks obtained")
    practical_marks: Decimal = Field(..., ge=0, description="Raw practical marks obtained")


class ExamResultResponse(BaseModel):
    """Response for a stored exam result."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    examination_id: uuid.UUID
    theory_marks: Decimal | None
    practical_marks: Decimal | None
    ia_marks: Decimal | None
    total_marks: Decimal | None
    theory_grade: str | None
    practical_grade: str | None
    overall_grade: str | None
    grace_marks_applied: int
    attempt_number: int
    status: str

    class Config:
        from_attributes = True


class ModerationRequest(BaseModel):
    """Request body for recording multi-examiner moderation."""

    exam_result_id: uuid.UUID
    examiner_1_marks: Decimal = Field(..., ge=0)
    examiner_2_marks: Decimal = Field(..., ge=0)
    max_marks: Decimal = Field(..., gt=0)
    examiner_3_marks: Decimal | None = Field(None, ge=0)


class ModerationResponse(BaseModel):
    """Response for a stored moderation record."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    exam_result_id: uuid.UUID
    examiner_1_marks: Decimal
    examiner_2_marks: Decimal
    examiner_3_marks: Decimal | None
    moderation_method: str
    final_marks: Decimal

    class Config:
        from_attributes = True


class ResultWorkflowResponse(BaseModel):
    """Response for workflow transitions (verify/approve/publish)."""

    id: uuid.UUID
    status: str
    message: str

    class Config:
        from_attributes = True


class PublishResultsResponse(BaseModel):
    """Response for bulk publish operation."""

    published_count: int
    message: str


# ---------------------------------------------------------------------------
# R4.4 — Mark Sheet Schemas
# ---------------------------------------------------------------------------


class MarkSheetResponse(BaseModel):
    """Response for a generated mark sheet record."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    academic_year: str
    semester: str | None
    pdf_asset_id: uuid.UUID
    qr_verification_code: str
    generated_at: datetime
    generated_by: uuid.UUID | None

    class Config:
        from_attributes = True
