"""
Electives integration test stubs — Session 9.

Tests ELEC-003..007, ELEC-009 cover the allocation algorithms and audit run logging.
All stubs are @pytest.mark.xfail until ElectiveService + migration 0014 are complete.
ELEC-008 (concurrent lock) is deferred_to: Phase 2.5 per COVERAGE_MANIFEST.

Run with:
    PYTHONPATH=.:services/snx-logbook pytest tests/integration/test_electives.py -v
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# ELEC-003: FCFS allocation — ADR-034 worked example
# ---------------------------------------------------------------------------


@pytest.mark.xfail(strict=False, reason="ELEC-003: FCFS allocation not yet implemented")
@pytest.mark.asyncio
async def test_elec_003_fcfs_allocation(db_session: AsyncSession) -> None:
    """
    ELEC-003: FCFS allocation — 10 students, 3 electives cap=4.
    Per ADR-034 worked example:
    - Students submit by submitted_at order
    - First 4 to want A get A; first 4 to want B get B; first 2 to want C get C
    - All 10 students allocated (in FCFS, order = submission time)
    """
    from app.schemas.electives import AllocationRunRequest
    from app.services.elective_service import ElectiveService

    tenant_id = uuid.uuid4()
    curriculum_id = uuid.uuid4()

    # Seed electives A, B, C with cap=4 each
    # ... (seeding implemented by testing agent in Session 10)

    service = ElectiveService(db=db_session)
    result = await service.run_allocation(
        tenant_id=tenant_id,
        request=AllocationRunRequest(
            curriculum_id=curriculum_id,
            block="Block 1",
            algorithm="fcfs",
            dry_run=False,
            force_reallocate=None,
        ),
        actor_id=uuid.uuid4(),
    )

    assert result.total_allocated == 10
    assert result.total_unallocated_pending_review == 0
    assert result.dry_run is False


# ---------------------------------------------------------------------------
# ELEC-004: Ranked allocation — ADR-034 worked example
# ---------------------------------------------------------------------------


@pytest.mark.xfail(strict=False, reason="ELEC-004: Ranked allocation not yet implemented")
@pytest.mark.asyncio
async def test_elec_004_ranked_allocation_adr034_example(db_session: AsyncSession) -> None:
    """
    ELEC-004: Ranked allocation per ADR-034 worked example.
    Setup: 3 electives A(cap=4), B(cap=4), C(cap=4), 10 students.
    Expected result:
    - A gets S1, S2, S3, S4 (all rank-1 for A, fills)
    - B gets S5 (rank-2), S6, S7, S8 (rank-1 for B)
    - C gets S9, S10 (rank-1 for C)
    - allocations_by_rank: {rank_1: 9, rank_2: 1}
    - 0 unallocated
    """
    from app.schemas.electives import AllocationRunRequest
    from app.services.elective_service import ElectiveService

    tenant_id = uuid.uuid4()
    curriculum_id = uuid.uuid4()

    service = ElectiveService(db=db_session)
    result = await service.run_allocation(
        tenant_id=tenant_id,
        request=AllocationRunRequest(
            curriculum_id=curriculum_id,
            block="Block 1",
            algorithm="ranked",
            dry_run=False,
            force_reallocate=None,
        ),
        actor_id=uuid.uuid4(),
    )

    assert result.total_allocated == 10
    assert result.total_unallocated_pending_review == 0
    assert result.allocations_by_rank.get("rank_1", 0) == 9
    assert result.allocations_by_rank.get("rank_2", 0) == 1


# ---------------------------------------------------------------------------
# ELEC-005: Reallocation — additive mode
# ---------------------------------------------------------------------------


@pytest.mark.xfail(strict=False, reason="ELEC-005: Reallocation additive mode not yet implemented")
@pytest.mark.asyncio
async def test_elec_005_reallocation_additive(db_session: AsyncSession) -> None:
    """
    ELEC-005: Additive reallocation.
    - Run initial allocation (allocates 8 of 10 students)
    - 2 students remain unallocated_pending_review
    - Add a new elective with capacity=2
    - Run additive reallocate
    - Existing 8 allocations unchanged; 2 new ones created
    """
    from app.schemas.electives import AllocationRunRequest
    from app.services.elective_service import ElectiveService

    tenant_id = uuid.uuid4()
    curriculum_id = uuid.uuid4()

    service = ElectiveService(db=db_session)
    result = await service.run_allocation(
        tenant_id=tenant_id,
        request=AllocationRunRequest(
            curriculum_id=curriculum_id,
            block="Block 1",
            algorithm="ranked",
            dry_run=False,
            force_reallocate="additive",
        ),
        actor_id=uuid.uuid4(),
    )
    # Only unallocated students are touched
    assert result.total_unallocated_pending_review == 0


# ---------------------------------------------------------------------------
# ELEC-006: Reallocation — full mode
# ---------------------------------------------------------------------------


@pytest.mark.xfail(strict=False, reason="ELEC-006: Reallocation full mode not yet implemented")
@pytest.mark.asyncio
async def test_elec_006_reallocation_full(db_session: AsyncSession) -> None:
    """
    ELEC-006: Full reallocation clears all existing allocations then re-runs.
    - Run initial allocation
    - Run force_reallocate=full
    - Verify old allocation rows are soft-deleted
    - Verify new allocations are created
    - audit_log has two entries (initial + reallocate)
    """
    from app.schemas.electives import AllocationRunRequest
    from app.services.elective_service import ElectiveService

    tenant_id = uuid.uuid4()
    curriculum_id = uuid.uuid4()

    service = ElectiveService(db=db_session)
    result = await service.run_allocation(
        tenant_id=tenant_id,
        request=AllocationRunRequest(
            curriculum_id=curriculum_id,
            block="Block 1",
            algorithm="ranked",
            dry_run=False,
            force_reallocate="full",
        ),
        actor_id=uuid.uuid4(),
    )
    assert result.run_id is not None
    assert result.total_allocated >= 0


# ---------------------------------------------------------------------------
# ELEC-007: Allocation run produces audit row in elective_allocation_runs
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=False, reason="ELEC-007: elective_allocation_runs audit row not yet implemented"
)
@pytest.mark.asyncio
async def test_elec_007_allocation_run_audit_row(db_session: AsyncSession) -> None:
    """
    ELEC-007: Every live run_allocation inserts exactly 1 row into elective_allocation_runs
    with correct totals and algorithm_used.
    """
    from app.models.electives import ElectiveAllocationRun
    from app.schemas.electives import AllocationRunRequest
    from app.services.elective_service import ElectiveService
    from sqlalchemy import select

    tenant_id = uuid.uuid4()
    curriculum_id = uuid.uuid4()

    service = ElectiveService(db=db_session)
    result = await service.run_allocation(
        tenant_id=tenant_id,
        request=AllocationRunRequest(
            curriculum_id=curriculum_id,
            block="Block 1",
            algorithm="ranked",
            dry_run=False,
            force_reallocate=None,
        ),
        actor_id=uuid.uuid4(),
    )

    row = await db_session.scalar(
        select(ElectiveAllocationRun).where(ElectiveAllocationRun.id == result.run_id)
    )
    assert row is not None
    assert row.algorithm_used == "ranked"
    assert row.total_allocated == result.total_allocated


# ---------------------------------------------------------------------------
# ELEC-009: Dry-run allocation — no writes, same counts as live
# ---------------------------------------------------------------------------


@pytest.mark.xfail(strict=False, reason="ELEC-009: Dry-run mode not yet implemented")
@pytest.mark.asyncio
async def test_elec_009_dry_run_matches_live(db_session: AsyncSession) -> None:
    """
    ELEC-009: Dry-run returns same allocation counts as live run
    but writes no rows to elective_allocations or elective_allocation_runs.
    """
    from app.models.electives import ElectiveAllocation
    from app.schemas.electives import AllocationRunRequest
    from app.services.elective_service import ElectiveService
    from sqlalchemy import func, select

    tenant_id = uuid.uuid4()
    curriculum_id = uuid.uuid4()

    service = ElectiveService(db=db_session)
    base_request = AllocationRunRequest(
        curriculum_id=curriculum_id,
        block="Block 1",
        algorithm="ranked",
        dry_run=False,
        force_reallocate=None,
    )
    dry_request = AllocationRunRequest(
        curriculum_id=curriculum_id,
        block="Block 1",
        algorithm="ranked",
        dry_run=True,
        force_reallocate=None,
    )

    dry_result = await service.run_allocation(
        tenant_id=tenant_id, request=dry_request, actor_id=uuid.uuid4()
    )
    assert dry_result.dry_run is True

    # Verify no actual rows written
    count = await db_session.scalar(
        select(func.count())
        .select_from(ElectiveAllocation)
        .where(ElectiveAllocation.tenant_id == tenant_id)
    )
    assert count == 0

    # Now live run should match dry-run totals
    live_result = await service.run_allocation(
        tenant_id=tenant_id, request=base_request, actor_id=uuid.uuid4()
    )
    assert live_result.total_allocated == dry_result.total_allocated
