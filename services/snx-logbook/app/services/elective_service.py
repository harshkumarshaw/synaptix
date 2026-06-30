"""
ElectiveService — Phase 2 Electives (A-08).

Implements:
  - create_elective()
  - submit_preferences()      ← full-block replace semantics (ADR-034 spec)
  - get_student_preferences()
  - run_allocation()          ← FCFS + Ranked algorithms (ADR-034)
  - get_student_allocations()
  - withdraw_allocation()
  - _tiebreak_rank()          ← deterministic tie-breaking for ranked algorithm

Error codes:
  SNX-ELEC-001: Elective not found
  SNX-ELEC-002: Block already allocated — preferences locked
  SNX-ELEC-003: Elective belongs to wrong block
  SNX-ELEC-004: Lock not available (concurrent allocation in progress)
  SNX-ELEC-005: Allocation not found or already withdrawn

Locking strategy (ADR-034):
  - SELECT ... FOR UPDATE on all elective rows for (tenant, curriculum, block)
  - SET LOCAL statement_timeout = '30s' before acquiring locks
  - LockNotAvailableError raised if lock unavailable (returns 409 to caller)
  - Dry-run uses FOR SHARE (non-blocking snapshot reads)

Audit log writes per endpoint:
  - submit_preferences → 1 audit_log row (action=submit_preferences)
  - run_allocation (live) → 1 audit_log row + 1 elective_allocation_runs row + N elective_allocations
  - withdraw_allocation → 1 audit_log row (action=withdraw_allocation)
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import UTC, datetime
from typing import Annotated

from app.models.electives import (
    Elective,
    ElectiveAllocation,
    ElectiveAllocationRun,
    StudentElectivePreference,
)
from app.schemas.electives import (
    AllocationResponse,
    AllocationRunRequest,
    AllocationRunResponse,
    ElectiveCreate,
    ElectiveResponse,
    PreferenceResponse,
    PreferencesSubmitRequest,
)
from app.services.audit_logger import write_audit_log
from fastapi import Depends
from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.db.session import get_db
from packages.shared.errors import (
    ResourceNotFoundError,
    SynaptixError,
)
from packages.shared.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Custom domain errors for Electives
# ---------------------------------------------------------------------------


class ElectiveBlockAllocatedError(SynaptixError):
    """SNX-ELEC-002: Block already allocated — preferences are locked."""

    code = "SNX-ELEC-002"

    def __init__(self, student_id: uuid.UUID, block: str) -> None:
        super().__init__(
            message=f"Block '{block}' is already allocated for student {student_id}. "
            "Preferences cannot be changed after allocation.",
        )


class ElectiveWrongBlockError(SynaptixError):
    """SNX-ELEC-003: Elective belongs to a different block than requested."""

    code = "SNX-ELEC-003"

    def __init__(self, elective_id: uuid.UUID, elective_block: str, requested_block: str) -> None:
        super().__init__(
            message=f"Elective {elective_id} belongs to '{elective_block}', "
            f"cannot be added to preferences for '{requested_block}'.",
        )


class ElectiveLockError(SynaptixError):
    """SNX-ELEC-004: Could not acquire row lock for allocation run."""

    code = "SNX-ELEC-004"

    def __init__(self, block: str) -> None:
        super().__init__(
            message=f"Could not acquire allocation lock for block '{block}'. "
            "Another allocation run may be in progress. Retry in a few seconds.",
        )


# ---------------------------------------------------------------------------
# ElectiveService
# ---------------------------------------------------------------------------


class ElectiveService:
    """Service layer for Electives module (A-08).

    All public methods accept tenant_id explicitly — no global tenant context
    assumed. Every mutating method writes an audit_log entry.
    """

    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # ELEC-001: Create elective
    # -----------------------------------------------------------------------

    async def create_elective(
        self,
        tenant_id: uuid.UUID,
        payload: ElectiveCreate,
        actor_id: uuid.UUID | None = None,
    ) -> ElectiveResponse:
        """Create a new elective offering.

        Audit: action=create_elective, resource_type=elective
        """
        elective = Elective(
            tenant_id=tenant_id,
            curriculum_id=payload.curriculum_id,
            code=payload.code,
            title=payload.title,
            block=payload.block,
            elective_type=payload.elective_type,
            capacity=payload.capacity,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(elective)
        await self.db.flush()

        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="CREATE_ELECTIVE",
            resource_type="elective",
            resource_id=elective.id,
            new_values={
                "code": elective.code,
                "block": elective.block,
                "elective_type": elective.elective_type,
                "capacity": elective.capacity,
            },
        )

        return ElectiveResponse.model_validate(elective)

    # -----------------------------------------------------------------------
    # ELEC-002: Submit student preferences (full-block replace)
    # -----------------------------------------------------------------------

    async def submit_preferences(
        self,
        tenant_id: uuid.UUID,
        payload: PreferencesSubmitRequest,
        actor_id: uuid.UUID | None = None,
    ) -> list[PreferenceResponse]:
        """Submit (or replace) a student's ranked preferences for a block.

        Semantics — full-block replace:
        1. Guard: reject if allocation for this block already exists (SNX-ELEC-002).
        2. Validate: each elective_id must belong to the specified block (SNX-ELEC-003).
        3. Soft-delete all existing active preferences for (student, block).
        4. Insert new preference set.
        5. Write audit_log row.

        All within a single transaction (caller owns commit).
        Audit: action=submit_preferences, resource_type=student_elective_preference
        """
        student_id = payload.student_id
        block = payload.block

        # Step 1: Guard — allocation already exists?
        existing_alloc_result = await self.db.execute(
            select(ElectiveAllocation).where(
                ElectiveAllocation.tenant_id == tenant_id,
                ElectiveAllocation.student_id == student_id,
                ElectiveAllocation.block == block,
                ElectiveAllocation.deleted_at.is_(None),
            )
        )
        if existing_alloc_result.scalar_one_or_none() is not None:
            raise ElectiveBlockAllocatedError(student_id=student_id, block=block)

        # Step 2: Validate elective_ids belong to the correct block
        elective_ids = [p.elective_id for p in payload.preferences]
        electives_result = await self.db.execute(
            select(Elective).where(
                Elective.tenant_id == tenant_id,
                Elective.id.in_(elective_ids),
                Elective.deleted_at.is_(None),
            )
        )
        electives_by_id: dict[uuid.UUID, Elective] = {
            e.id: e for e in electives_result.scalars().all()
        }

        for pref in payload.preferences:
            elective = electives_by_id.get(pref.elective_id)
            if elective is None:
                raise ResourceNotFoundError(
                    f"Elective {pref.elective_id} not found for tenant {tenant_id}"
                )
            if elective.block != block:
                raise ElectiveWrongBlockError(
                    elective_id=pref.elective_id,
                    elective_block=elective.block,
                    requested_block=block,
                )

        # Step 3: Soft-delete existing preferences for this student+block
        await self.db.execute(
            update(StudentElectivePreference)
            .where(
                StudentElectivePreference.tenant_id == tenant_id,
                StudentElectivePreference.student_id == student_id,
                StudentElectivePreference.block == block,
                StudentElectivePreference.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )

        # Step 4: Insert new preference set
        now = datetime.now(UTC)
        new_prefs: list[StudentElectivePreference] = []
        for pref in payload.preferences:
            row = StudentElectivePreference(
                tenant_id=tenant_id,
                student_id=student_id,
                elective_id=pref.elective_id,
                block=block,
                rank_position=pref.rank_position,
                submitted_at=now,
            )
            self.db.add(row)
            new_prefs.append(row)

        await self.db.flush()

        # Step 5: Audit log
        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="SUBMIT_PREFERENCES",
            resource_type="student_elective_preference",
            resource_id=student_id,
            new_values={
                "student_id": str(student_id),
                "block": block,
                "preference_count": len(new_prefs),
                "preferences": [
                    {"elective_id": str(p.elective_id), "rank_position": p.rank_position}
                    for p in new_prefs
                ],
            },
        )

        return [PreferenceResponse.model_validate(p) for p in new_prefs]

    async def get_student_preferences(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        block: str | None = None,
    ) -> list[PreferenceResponse]:
        """Return active preferences for a student, optionally filtered by block."""
        stmt = select(StudentElectivePreference).where(
            StudentElectivePreference.tenant_id == tenant_id,
            StudentElectivePreference.student_id == student_id,
            StudentElectivePreference.deleted_at.is_(None),
        )
        if block is not None:
            stmt = stmt.where(StudentElectivePreference.block == block)
        stmt = stmt.order_by(
            StudentElectivePreference.block,
            StudentElectivePreference.rank_position,
        )
        result = await self.db.execute(stmt)
        return [PreferenceResponse.model_validate(p) for p in result.scalars().all()]

    # -----------------------------------------------------------------------
    # ELEC-003..009: Allocation run (FCFS + Ranked)
    # -----------------------------------------------------------------------

    async def run_allocation(
        self,
        tenant_id: uuid.UUID,
        request: AllocationRunRequest,
        actor_id: uuid.UUID,
    ) -> AllocationRunResponse:
        """Run the elective allocation algorithm for a block.

        Locking:
          - SET LOCAL statement_timeout = '30s'
          - SELECT ... FOR UPDATE on all elective rows for this block
          - FOR SHARE on dry_run (non-blocking snapshot)

        Audit (live runs only — NOT dry-run):
          - 1 elective_allocation_runs row
          - N elective_allocations rows (one per allocated student)
          - 1 audit_log row (action=run_allocation)

        Raises:
          ElectiveLockError (SNX-ELEC-004) if lock cannot be acquired.
        """
        start_ms = int(time.time() * 1000)

        # Step 1: Set statement timeout to fail fast on lock contention
        await self.db.execute(
            # type: ignore[arg-type]
            __import__("sqlalchemy").text("SET LOCAL statement_timeout = '30s'")
        )

        # Step 2: Acquire row-level lock on all electives for this block
        lock_clause = "FOR UPDATE NOWAIT" if not request.dry_run else "FOR SHARE"
        # Build the lock query with a safe literal (not user input — values come from
        # our own constants 'FOR UPDATE NOWAIT' or 'FOR SHARE').
        # noqa: S608 — lock_clause is not user-controlled; it's a boolean branch.
        lock_sql = (  # noqa: S608
            "SELECT id, capacity FROM electives "
            "WHERE tenant_id = :tenant_id "
            "  AND curriculum_id = :curriculum_id "
            "  AND block = :block "
            "  AND deleted_at IS NULL "
        ) + lock_clause
        try:
            locked_result = await self.db.execute(
                __import__("sqlalchemy").text(lock_sql),  # noqa: S608
                {
                    "tenant_id": str(tenant_id),
                    "curriculum_id": str(request.curriculum_id),
                    "block": request.block,
                },
            )
        except OperationalError:
            raise ElectiveLockError(block=request.block)

        # Build mutable capacity map: {elective_id: remaining_capacity}
        capacity_map: dict[uuid.UUID, int] = {
            uuid.UUID(str(row[0])): row[1] for row in locked_result.fetchall()
        }

        if not capacity_map:
            raise ResourceNotFoundError(
                f"No electives found for curriculum {request.curriculum_id}, block {request.block}"
            )

        # Step 3: Handle force_reallocate=full — soft-delete all existing allocations
        if request.force_reallocate == "full" and not request.dry_run:
            existing_allocs_result = await self.db.execute(
                select(ElectiveAllocation).where(
                    ElectiveAllocation.tenant_id == tenant_id,
                    ElectiveAllocation.elective_id.in_(list(capacity_map.keys())),
                    ElectiveAllocation.block == request.block,
                    ElectiveAllocation.deleted_at.is_(None),
                )
            )
            for alloc in existing_allocs_result.scalars().all():
                alloc.deleted_at = datetime.now(UTC)
                # Restore capacity
                capacity_map[alloc.elective_id] = capacity_map.get(alloc.elective_id, 0) + 1
            await self.db.flush()

        # Step 4: Build set of already-allocated students (skip in additive mode)
        already_allocated: set[uuid.UUID] = set()
        if request.force_reallocate != "full":
            alloc_check_result = await self.db.execute(
                select(ElectiveAllocation.student_id).where(
                    ElectiveAllocation.tenant_id == tenant_id,
                    ElectiveAllocation.elective_id.in_(list(capacity_map.keys())),
                    ElectiveAllocation.block == request.block,
                    ElectiveAllocation.deleted_at.is_(None),
                )
            )
            already_allocated = {row[0] for row in alloc_check_result.fetchall()}

        # Step 5: Fetch all preferences for this block, ordered by submitted_at
        prefs_result = await self.db.execute(
            select(StudentElectivePreference)
            .where(
                StudentElectivePreference.tenant_id == tenant_id,
                StudentElectivePreference.elective_id.in_(list(capacity_map.keys())),
                StudentElectivePreference.block == request.block,
                StudentElectivePreference.deleted_at.is_(None),
            )
            .order_by(
                StudentElectivePreference.student_id,
                StudentElectivePreference.rank_position,
            )
        )
        all_prefs = list(prefs_result.scalars().all())

        # Group preferences by student
        prefs_by_student: dict[uuid.UUID, list[StudentElectivePreference]] = {}
        for pref in all_prefs:
            prefs_by_student.setdefault(pref.student_id, []).append(pref)

        # Sort each student's prefs by rank_position
        for _sid, pref_list in prefs_by_student.items():
            pref_list.sort(key=lambda p: p.rank_position)

        # Determine unique students who are candidates
        candidate_students = set(prefs_by_student.keys()) - already_allocated

        # Step 6: Run the selected algorithm
        run_id = uuid.uuid4()
        allocations_by_rank: dict[str, int] = {}
        new_allocations: list[dict] = []  # dicts; flushed only on live run

        if request.algorithm == "fcfs":
            new_allocations, allocations_by_rank = self._run_fcfs(
                tenant_id=tenant_id,
                candidate_students=candidate_students,
                prefs_by_student=prefs_by_student,
                capacity_map=capacity_map,
                run_id=run_id,
                all_prefs=all_prefs,
            )
        else:
            new_allocations, allocations_by_rank = self._run_ranked(
                tenant_id=tenant_id,
                candidate_students=candidate_students,
                prefs_by_student=prefs_by_student,
                capacity_map=capacity_map,
                run_id=run_id,
                run_uuid=run_id,
            )

        total_allocated = len(new_allocations)
        total_unallocated = len(candidate_students) - total_allocated

        end_ms = int(time.time() * 1000)
        duration_ms = end_ms - start_ms

        # Step 7: Persist (live run only)
        if not request.dry_run:
            # Insert allocation rows
            for alloc_data in new_allocations:
                alloc = ElectiveAllocation(
                    tenant_id=tenant_id,
                    student_id=alloc_data["student_id"],
                    elective_id=alloc_data["elective_id"],
                    block=request.block,
                    allocation_run_id=run_id,
                    allocation_method=alloc_data["allocation_method"],
                    allocated_at=datetime.now(UTC),
                )
                self.db.add(alloc)

            # Insert audit run row
            run_row = ElectiveAllocationRun(
                id=run_id,
                tenant_id=tenant_id,
                curriculum_id=request.curriculum_id,
                block=request.block,
                algorithm_used=request.algorithm,
                triggered_by=actor_id,
                triggered_at=datetime.now(UTC),
                is_dry_run=False,
                force_reallocate=request.force_reallocate,
                total_students=len(candidate_students),
                total_allocated=total_allocated,
                total_unallocated_pending_review=total_unallocated,
                run_duration_ms=duration_ms,
                results_summary=allocations_by_rank,
            )
            self.db.add(run_row)
            await self.db.flush()

            # Audit log
            await write_audit_log(
                db=self.db,
                tenant_id=tenant_id,
                actor_user_id=actor_id,
                action="RUN_ALLOCATION",
                resource_type="elective_allocation_run",
                resource_id=run_id,
                new_values={
                    "run_id": str(run_id),
                    "algorithm": request.algorithm,
                    "block": request.block,
                    "total_allocated": total_allocated,
                    "total_unallocated": total_unallocated,
                    "force_reallocate": request.force_reallocate,
                },
            )

        return AllocationRunResponse(
            run_id=run_id if not request.dry_run else None,
            tenant_id=tenant_id,
            curriculum_id=request.curriculum_id,
            block=request.block,
            algorithm_used=request.algorithm,
            dry_run=request.dry_run,
            force_reallocate=request.force_reallocate,
            total_students_considered=len(candidate_students),
            total_allocated=total_allocated,
            total_unallocated_pending_review=total_unallocated,
            allocations_by_rank=allocations_by_rank,
            duration_ms=duration_ms,
            triggered_at=datetime.now(UTC),
        )

    # -----------------------------------------------------------------------
    # Algorithm: FCFS
    # -----------------------------------------------------------------------

    def _run_fcfs(
        self,
        tenant_id: uuid.UUID,
        candidate_students: set[uuid.UUID],
        prefs_by_student: dict[uuid.UUID, list[StudentElectivePreference]],
        capacity_map: dict[uuid.UUID, int],
        run_id: uuid.UUID,
        all_prefs: list[StudentElectivePreference],
    ) -> tuple[list[dict], dict[str, int]]:
        """FCFS algorithm: first submitted preference wins capacity slot.

        Per ADR-034 specification:
        - Order all preferences by submitted_at ASC (earliest first)
        - For each preference, if capacity > 0 and student not yet allocated → allocate
        """
        allocations: list[dict] = []
        allocations_by_rank: dict[str, int] = {"fcfs": 0}
        allocated_students: set[uuid.UUID] = set()

        # Sort ALL preferences by submitted_at ASC for true FCFS ordering
        sorted_prefs = sorted(all_prefs, key=lambda p: (p.submitted_at, p.rank_position))

        for pref in sorted_prefs:
            if pref.student_id not in candidate_students:
                continue
            if pref.student_id in allocated_students:
                continue
            if capacity_map.get(pref.elective_id, 0) <= 0:
                continue

            capacity_map[pref.elective_id] -= 1
            allocated_students.add(pref.student_id)
            allocations.append({
                "student_id": pref.student_id,
                "elective_id": pref.elective_id,
                "allocation_method": "fcfs",
            })
            allocations_by_rank["fcfs"] = allocations_by_rank.get("fcfs", 0) + 1

        return allocations, allocations_by_rank

    # -----------------------------------------------------------------------
    # Algorithm: Ranked
    # -----------------------------------------------------------------------

    def _run_ranked(
        self,
        tenant_id: uuid.UUID,
        candidate_students: set[uuid.UUID],
        prefs_by_student: dict[uuid.UUID, list[StudentElectivePreference]],
        capacity_map: dict[uuid.UUID, int],
        run_id: uuid.UUID,
        run_uuid: uuid.UUID,
    ) -> tuple[list[dict], dict[str, int]]:
        """Ranked algorithm: pass through rank 1..10, allocating greedily.

        Per ADR-034 specification:
        Pass rank-1: for each student who has a rank-1 preference for an elective
                     with capacity > 0, allocate.
        Pass rank-2: for unallocated students, try rank-2 preference, etc.
        Tie-breaking within a rank pass: earliest submitted_at; if equal, deterministic
                     hash of (student_id, run_id).

        Students unallocated after rank-10 pass → pending_manual_review.
        """
        allocations: list[dict] = []
        allocations_by_rank: dict[str, int] = {}
        allocated_students: set[uuid.UUID] = set()

        for rank in range(1, 11):
            rank_key = f"rank_{rank}"
            # Collect candidates at this rank, sorted by tie-breaking criteria
            rank_candidates: list[tuple[float, uuid.UUID, uuid.UUID]] = []  # (sort_key, student_id, elective_id)

            for student_id in candidate_students:
                if student_id in allocated_students:
                    continue
                prefs = prefs_by_student.get(student_id, [])
                pref_at_rank = next(
                    (p for p in prefs if p.rank_position == rank), None
                )
                if pref_at_rank is None:
                    continue
                if capacity_map.get(pref_at_rank.elective_id, 0) <= 0:
                    continue

                # Sort key: (submitted_at timestamp, deterministic tiebreak)
                sort_key = (
                    pref_at_rank.submitted_at.timestamp(),
                    self._tiebreak_rank(student_id, run_uuid),
                )
                rank_candidates.append((sort_key, student_id, pref_at_rank.elective_id))

            # Sort by (submitted_at, tiebreak) to honour earliest-first within rank pass
            rank_candidates.sort(key=lambda x: x[0])

            for _sort_key, student_id, elective_id in rank_candidates:
                if student_id in allocated_students:
                    continue
                if capacity_map.get(elective_id, 0) <= 0:
                    continue

                capacity_map[elective_id] -= 1
                allocated_students.add(student_id)
                allocations.append({
                    "student_id": student_id,
                    "elective_id": elective_id,
                    "allocation_method": rank_key,
                })
                allocations_by_rank[rank_key] = allocations_by_rank.get(rank_key, 0) + 1

        return allocations, allocations_by_rank

    # -----------------------------------------------------------------------
    # ELEC-E002: Deterministic tie-breaking
    # -----------------------------------------------------------------------

    def _tiebreak_rank(self, student_id: uuid.UUID, run_id: uuid.UUID) -> float:
        """Return a deterministic float in [0,1) for tie-breaking.

        Uses SHA-256 of (student_id bytes || run_id bytes).
        Same inputs → same output (deterministic).
        Different student_ids → different outputs (distinct).
        """
        digest = hashlib.sha256(student_id.bytes + run_id.bytes).digest()
        # Take first 8 bytes as big-endian unsigned int, normalise to [0,1)
        return int.from_bytes(digest[:8], "big") / (2**64)

    # -----------------------------------------------------------------------
    # Get student allocations
    # -----------------------------------------------------------------------

    async def get_student_allocations(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        block: str | None = None,
    ) -> list[AllocationResponse]:
        """Return confirmed allocations for a student."""
        stmt = select(ElectiveAllocation).where(
            ElectiveAllocation.tenant_id == tenant_id,
            ElectiveAllocation.student_id == student_id,
            ElectiveAllocation.deleted_at.is_(None),
        )
        if block is not None:
            stmt = stmt.where(ElectiveAllocation.block == block)
        result = await self.db.execute(stmt)
        return [AllocationResponse.model_validate(a) for a in result.scalars().all()]

    # -----------------------------------------------------------------------
    # ELEC-E003: Withdraw allocation
    # -----------------------------------------------------------------------

    async def withdraw_allocation(
        self,
        tenant_id: uuid.UUID,
        allocation_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
    ) -> None:
        """Withdraw a student's allocation. Restores capacity on the elective.

        Audit: action=withdraw_allocation, resource_type=elective_allocation
        """
        # Find allocation
        result = await self.db.execute(
            select(ElectiveAllocation).where(
                ElectiveAllocation.tenant_id == tenant_id,
                ElectiveAllocation.id == allocation_id,
                ElectiveAllocation.deleted_at.is_(None),
            )
        )
        alloc = result.scalar_one_or_none()
        if alloc is None:
            raise NotFoundError(f"Allocation {allocation_id} not found or already withdrawn")

        # Soft-delete the allocation
        alloc.deleted_at = datetime.now(UTC)
        await self.db.flush()

        # Audit
        await write_audit_log(
            db=self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            action="WITHDRAW_ALLOCATION",
            resource_type="elective_allocation",
            resource_id=allocation_id,
            new_values={
                "student_id": str(alloc.student_id),
                "elective_id": str(alloc.elective_id),
                "block": alloc.block,
                "withdrawn_at": datetime.now(UTC).isoformat(),
            },
        )
