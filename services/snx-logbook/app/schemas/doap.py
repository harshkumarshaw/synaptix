"""Pydantic v2 schemas for DOAP module."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DoapStage(StrEnum):
    D = "D"  # Demonstration
    O = "O"  # Observation  # noqa: E741
    A = "A"  # Assistance
    P = "P"  # Performance


class DoapRating(StrEnum):
    B = "B"  # Below expectation
    M = "M"  # Meets expectation
    E = "E"  # Exceeds expectation


class DoapAttemptType(StrEnum):
    F = "F"  # First
    R = "R"  # Repeat after R decision
    Re = "Re"  # Remediation


class DoapFacultyDecision(StrEnum):
    C = "C"  # Certify
    R = "R"  # Repeat
    Re = "Re"  # Remediate


class DoapState(StrEnum):
    NOT_STARTED = "not_started"
    DEMONSTRATED = "demonstrated"
    OBSERVED = "observed"
    ASSISTED = "assisted"
    PERFORMED = "performed"
    CERTIFIED = "certified"


class DoapSessionCreate(BaseModel):
    """Request to create a DOAP session record."""

    model_config = ConfigDict(use_enum_values=True)

    student_id: UUID
    session_id: UUID
    competency_code: str = Field(min_length=2, max_length=50)
    nmc_level: str = Field(pattern="^(K|KH|SH|P)$")
    is_core: bool = False
    stage: DoapStage
    rating: DoapRating
    attempt_type: DoapAttemptType
    faculty_decision: DoapFacultyDecision
    faculty_id: UUID
    evidence_asset_ids: list[UUID] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_rating_decision_consistency(self) -> "DoapSessionCreate":
        """Rating B implies decision R or Re (cannot be C). DOAP-NMC-003."""
        if (
            self.rating == DoapRating.B.value
            and self.faculty_decision == DoapFacultyDecision.C.value
        ):
            raise ValueError(
                "DOAP-002: Rating B (Below expectation) cannot have faculty_decision C (Certify). "
                "Use R (Repeat) or Re (Remediate)."
            )
        return self


class DoapSessionResponse(BaseModel):
    """DOAP session record response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    session_id: UUID
    competency_code: str
    nmc_level: str
    is_core: bool
    stage: str
    rating: str
    attempt_type: str
    faculty_decision: str
    faculty_id: UUID
    evidence_asset_ids: list[UUID]
    notes: str | None
    signed_off_at: datetime
    created_at: datetime


class DoapStateResponse(BaseModel):
    """Current DOAP state per competency for a student."""

    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    competency_code: str
    current_state: DoapState
    records_per_stage: dict[str, int]  # e.g. {"D": 2, "O": 1, "A": 0, "P": 0}
    certified_stages: list[str]
    pending_stage: str | None
    last_record_at: datetime | None


class DoapProgressionResponse(BaseModel):
    """Full progression history for a student + competency."""

    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    competency_code: str
    state: DoapStateResponse
    records: list[DoapSessionResponse]
