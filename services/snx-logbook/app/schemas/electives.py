"""
Pydantic v2 schemas — Electives (A-08).

All schemas use ConfigDict(from_attributes=True) — Pydantic v2 convention.
Cross-field validators use @model_validator(mode='after').
Single-field validators use @field_validator.

Error codes:
  SNX-ELEC-001: Generic elective validation error
  SNX-ELEC-002: Block already allocated — preferences locked
  SNX-ELEC-003: Elective belongs to wrong block
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Elective CRUD Schemas
# ---------------------------------------------------------------------------


class ElectiveCreate(BaseModel):
    """Payload to create a new elective offering."""

    curriculum_id: uuid.UUID
    code: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=150)
    block: Literal["Block 1", "Block 2"]
    elective_type: Literal["pre_clinical", "para_clinical", "clinical", "community", "research"]
    capacity: int = Field(..., ge=1, le=500)
    block_duration_weeks: int = Field(
        default=2,
        ge=1,
        le=4,
        description="NMC CBME 2019 Reg 7 mandates 2 weeks per block (4 weeks total)",
    )


class ElectiveResponse(BaseModel):
    """ORM-mapped response for a single elective."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    curriculum_id: uuid.UUID
    code: str
    title: str
    block: str
    elective_type: str
    capacity: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Student Preference Schemas
# ---------------------------------------------------------------------------


class PreferenceItem(BaseModel):
    """A single preference entry: which elective at which rank."""

    elective_id: uuid.UUID
    rank_position: int = Field(..., ge=1, le=10)


class PreferencesSubmitRequest(BaseModel):
    """
    Full preference set submission for a student + block.

    Semantics (full-block replace):
    - On submit, ALL existing active preferences for (student, block) are soft-deleted.
    - The new set is inserted atomically in the same transaction.
    - If an allocation for this block already exists, SNX-ELEC-002 is raised.

    Validation enforced here (schema level):
    - No duplicate rank_positions within the submitted set.
    - No duplicate elective_ids within the submitted set.
    - Ranks must form a contiguous sequence starting at 1 (no gaps).
    """

    student_id: uuid.UUID
    block: Literal["Block 1", "Block 2"]
    preferences: list[PreferenceItem] = Field(..., min_length=1, max_length=10)

    @model_validator(mode="after")
    def validate_preferences(self) -> PreferencesSubmitRequest:
        """Enforce no duplicate ranks, no duplicate electives, contiguous ranks."""
        ranks = [p.rank_position for p in self.preferences]
        elective_ids = [p.elective_id for p in self.preferences]

        if len(ranks) != len(set(ranks)):
            raise ValueError("Duplicate rank_position values are not allowed within a block submission")

        if len(elective_ids) != len(set(elective_ids)):
            raise ValueError("Duplicate elective_id values are not allowed within a block submission")

        # Ranks must start at 1 and be contiguous (1, 2, 3 — not 1, 3, 5)
        sorted_ranks = sorted(ranks)
        expected = list(range(1, len(sorted_ranks) + 1))
        if sorted_ranks != expected:
            raise ValueError(
                f"Rank positions must form a contiguous sequence starting at 1. "
                f"Got: {sorted_ranks}, expected: {expected}"
            )

        return self


class PreferenceResponse(BaseModel):
    """ORM-mapped response for a single preference row."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    student_id: uuid.UUID
    elective_id: uuid.UUID
    block: str
    rank_position: int
    submitted_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Allocation Schemas
# ---------------------------------------------------------------------------


class AllocationRunRequest(BaseModel):
    """
    Admin-triggered allocation run request.

    dry_run=True: compute and return result, commit NO writes.
    force_reallocate=None: skip students already allocated (default safe mode).
    force_reallocate='additive': allocate only unallocated students.
    force_reallocate='full': clear all existing allocations, re-run from scratch.
    """

    curriculum_id: uuid.UUID
    block: Literal["Block 1", "Block 2"]
    algorithm: Literal["fcfs", "ranked"] = "ranked"
    dry_run: bool = False
    force_reallocate: Literal["additive", "full"] | None = None

    @model_validator(mode="after")
    def validate_dry_run_constraints(self) -> AllocationRunRequest:
        """Dry-run is incompatible with force_reallocate='full'."""
        if self.dry_run and self.force_reallocate == "full":
            raise ValueError(
                "dry_run=True is incompatible with force_reallocate='full'. "
                "A dry-run full reallocation would delete existing data without committing, "
                "creating confusing state. Use dry_run=False to test full reallocation."
            )
        return self


class AllocationByRank(BaseModel):
    """Breakdown of how many students were allocated at each rank pass."""

    rank_1: int = 0
    rank_2: int = 0
    rank_3: int = 0
    rank_4: int = 0
    rank_5: int = 0
    rank_6: int = 0
    rank_7: int = 0
    rank_8: int = 0
    rank_9: int = 0
    rank_10: int = 0
    fcfs: int = 0
    manual: int = 0


class AllocationRunResponse(BaseModel):
    """
    Response from a completed allocation run.

    run_id is None when dry_run=True (no audit row created).
    """

    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID | None  # None for dry_run
    tenant_id: uuid.UUID
    curriculum_id: uuid.UUID
    block: str
    algorithm_used: str
    dry_run: bool
    force_reallocate: str | None
    total_students_considered: int
    total_allocated: int
    total_unallocated_pending_review: int
    allocations_by_rank: dict[str, int]
    duration_ms: int | None
    triggered_at: datetime


class AllocationResponse(BaseModel):
    """ORM-mapped response for a single confirmed allocation."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: uuid.UUID
    student_id: uuid.UUID
    elective_id: uuid.UUID
    block: str
    allocation_run_id: uuid.UUID | None
    allocation_method: str | None
    allocated_at: datetime
    supervisor_id: uuid.UUID | None
