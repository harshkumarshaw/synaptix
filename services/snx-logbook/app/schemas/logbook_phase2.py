"""Pydantic v2 schemas for Logbook Phase 2 extensions."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LogbookEntryCreate(BaseModel):
    """Request to create a logbook entry."""

    model_config = ConfigDict(use_enum_values=True)

    student_id: UUID

    # Discriminator: exactly one of these must be set (per ADR-032)
    subject_code: str | None = Field(default=None, max_length=50)
    elective_id: UUID | None = None

    professional_phase: str = Field(
        pattern="^(Phase I|Phase II|Phase III Part I|Phase III Part II)$"
    )
    competency_code: str = Field(min_length=2, max_length=50)
    nmc_level: str = Field(pattern="^(K|KH|SH|P)$")
    is_core: bool = False

    activity_date: date
    activity_name: str = Field(min_length=1, max_length=150)
    reflection: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_elective_discriminator(self) -> "LogbookEntryCreate":
        """
        ADR-032: exactly one of subject_code or elective_id must be set.
        Maps to CHECK constraint chk_logbook_entries_elective on the table.
        """
        has_subject = self.subject_code is not None
        has_elective = self.elective_id is not None

        if has_subject == has_elective:
            raise ValueError(
                "LOG-VALIDATION-001: Exactly one of subject_code or elective_id "
                "must be set. Got both."
                if has_subject
                else "LOG-VALIDATION-001: Exactly one of subject_code or elective_id "
                "must be set. Got neither."
            )
        return self


class LogbookEntryResponse(BaseModel):
    """Logbook entry response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    subject_code: str | None = None
    elective_id: UUID | None = None
    professional_phase: str
    competency_code: str
    nmc_level: str
    is_core: bool
    activity_date: date
    activity_name: str
    reflection: str | None = None
    rating: str | None = None
    attempt_type: str | None = None
    faculty_decision: str | None = None
    faculty_initials: str | None = None
    student_initials: str | None = None
    status: str
    backdated: bool
    backdating_approved_by: UUID | None = None
    signed_off_by: UUID | None = None
    signed_off_at: datetime | None = None
    created_at: datetime


class LogbookSignoffRequest(BaseModel):
    """Faculty signoff request for a logbook entry."""

    rating: str = Field(pattern="^(B|M|E)$")
    faculty_decision: str = Field(pattern="^(C|R|Re)$")
    faculty_initials: str = Field(min_length=1, max_length=10)
    feedback: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_rating_decision(self) -> "LogbookSignoffRequest":
        """Rating B cannot have decision C (same rule as DOAP — DOAP-NMC-003)."""
        if self.rating == "B" and self.faculty_decision == "C":
            raise ValueError(
                "LOG-VALIDATION-002: Rating B (Below expectation) cannot have "
                "faculty_decision C (Certify)."
            )
        return self


class LogbookEntrySubmitRequest(BaseModel):
    """Student submission of a logbook entry for faculty review."""

    student_initials: str = Field(min_length=1, max_length=10)


class LogbookAssessmentResponse(BaseModel):
    """Logbook assessment (IA marks) response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    subject_code: str
    professional_phase: str
    total_entries: int
    completed_entries: int
    ia_marks_pct: float
    ia_marks_awarded: float
    is_complete: bool
    signed_off_by: UUID | None = None
    signed_off_at: datetime | None = None


class IAMarksCalculation(BaseModel):
    """Internal representation for IA marks calculation."""

    subject_code: str
    professional_phase: str
    total_entries: int
    completed_entries: int
    completion_pct: float  # completed / total * 100
    ia_weight_pct: float  # configured weight (0-20%)
    subject_ia_max: float  # max marks for this subject's IA
    ia_marks_awarded: float  # (completion_pct / 100) * (ia_weight_pct / 100) * subject_ia_max
    capped_at_20_pct: bool  # whether the cap was applied
