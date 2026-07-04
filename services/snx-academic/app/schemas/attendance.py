"""
Pydantic v2 schemas — Attendance Engine (Phase 2).

All schemas use strict mode. No `any` types.
API envelope wraps all responses — see conventions/API_DESIGN.md.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class AttendanceMarkRequest(BaseModel):
    """Mark attendance for one student at one event.

    Used for manual and QR-scanned marking.
    RFID/Face/GPS/Biometric deferred to Phase 2.5.
    """

    student_id: uuid.UUID
    event_id: uuid.UUID
    session_id: uuid.UUID | None = None
    status: Literal["present", "absent", "late", "excused", "medical", "official_duty", "exempt"]
    attendance_category: Literal[
        "theory", "practical", "clinical", "doap", "ece", "aetcom", "foundation_course", "elective"
    ]
    professional_phase: Literal["Phase I", "Phase II", "Phase III Part I", "Phase III Part II"]
    method: Literal["manual", "qr", "rfid", "face", "gps", "biometric"] = "manual"
    geo_lat: Decimal | None = None
    geo_lng: Decimal | None = None
    device_id: str | None = None
    qr_token: str | None = None
    rfid_card_id: str | None = None
    biometric_hash: str | None = None
    # Conflict resolution: original offline timestamp when syncing
    original_marked_at: datetime | None = None
    # 24-hour correction window override
    is_hod_approved: bool = False


class AttendanceBulkMarkRequest(BaseModel):
    """Mark attendance for multiple students in one event batch."""

    event_id: uuid.UUID
    attendance_category: Literal[
        "theory", "practical", "clinical", "doap", "ece", "aetcom", "foundation_course", "elective"
    ]
    professional_phase: Literal["Phase I", "Phase II", "Phase III Part I", "Phase III Part II"]
    method: Literal["manual", "qr"] = "manual"
    records: list[AttendanceBulkRecord]

    @field_validator("records")
    @classmethod
    def records_not_empty(cls, v: list[AttendanceBulkRecord]) -> list[AttendanceBulkRecord]:
        """Ensure bulk records are not empty."""
        if not v:
            raise ValueError("records must not be empty")
        return v


class AttendanceBulkRecord(BaseModel):
    """Single record within a bulk attendance marking request."""

    student_id: uuid.UUID
    status: Literal["present", "absent", "late", "excused", "medical", "official_duty", "exempt"]
    original_marked_at: datetime | None = None


class AttendanceExemptionRequest(BaseModel):
    """Grant attendance exemption for a student+event. Principal-only endpoint."""

    student_id: uuid.UUID
    event_id: uuid.UUID
    reason: str = Field(..., min_length=10, max_length=1000)
    exemption_batch_id: uuid.UUID | None = None


class AttendanceAccommodationCreate(BaseModel):
    """Create a threshold override accommodation for a student."""

    student_id: uuid.UUID
    effective_from: date
    effective_until: date
    attendance_category: str | None = None
    theory_threshold_override: Decimal | None = Field(None, le=Decimal("75.00"))
    practical_threshold_override: Decimal | None = Field(None, le=Decimal("80.00"))
    medical_certificate_asset_id: uuid.UUID | None = None
    workflow_instance_id: uuid.UUID | None = None

    @field_validator("effective_until")
    @classmethod
    def until_after_from(cls, v: date, info: object) -> date:
        """Validate effective_until is after effective_from."""
        from_date = getattr(info, "data", {}).get("effective_from")
        if from_date and v <= from_date:
            raise ValueError("effective_until must be after effective_from")
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class AttendanceRecordOut(BaseModel):
    """Single attendance record response."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    event_id: uuid.UUID
    session_id: uuid.UUID | None
    status: str
    attendance_category: str
    professional_phase: str
    method: str
    marked_at: datetime
    needs_review: bool
    created_at: datetime


class AttendanceSummaryOut(BaseModel):
    """Attendance summary for a student+course+phase+category."""

    model_config = {"from_attributes": True}

    tenant_id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID
    professional_phase: str
    attendance_category: str
    sessions_conducted: int
    sessions_present: int
    sessions_excused: int
    sessions_official_duty: int
    sessions_medical: int
    attendance_pct: Decimal
    last_recalculated_at: datetime


class EligibilityCheckOut(BaseModel):
    """Attendance eligibility check result for a student.

    Two-threshold NMC CBME check: theory ≥75%, practical ≥80%.
    Both must pass — independent thresholds (Commandment 3).
    """

    student_id: uuid.UUID
    is_theory_eligible: bool
    theory_pct: Decimal
    theory_threshold: Decimal = Decimal("75.00")
    is_practical_eligible: bool
    practical_pct: Decimal
    practical_threshold: Decimal = Decimal("80.00")
    is_eligible: bool  # True only if BOTH pass
    failures: list[str]  # Human-readable failure reasons
