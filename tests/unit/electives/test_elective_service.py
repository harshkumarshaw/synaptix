"""
Electives unit test stubs — Session 9.

All tests are @pytest.mark.xfail until ElectiveService is implemented.
xfail markers are REMOVED stub-by-stub as the corresponding service function
is completed. This file is the contract: every COVERAGE_MANIFEST entry for
module A-08 (ELEC-001..009, ELEC-E001..007) must have a matching test here.

DOAP is NOT in this file — see Session 10.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def student_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_db() -> AsyncMock:
    """Async DB session mock with execute returning a result that has scalar_one_or_none()=None."""
    db = AsyncMock()
    # Configure execute to return a result mock with all common methods returning None/[]
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    result_mock.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    result_mock.fetchall = MagicMock(return_value=[])
    db.execute = AsyncMock(return_value=result_mock)
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


# ---------------------------------------------------------------------------
# ELEC-001: Create elective
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_elec_001_create_elective(mock_db: AsyncMock, tenant_id: uuid.UUID) -> None:
    """ELEC-001: Create elective with valid payload inserts row, returns ElectiveResponse."""
    from app.services.elective_service import ElectiveService
    from app.schemas.electives import ElectiveCreate, ElectiveResponse

    payload = ElectiveCreate(
        curriculum_id=uuid.uuid4(),
        code="ELEC-CARD-01",
        title="Clinical Cardiology Elective",
        block="Block 1",
        elective_type="clinical",
        capacity=10,
    )
    # ElectiveService.create_elective adds the row then flushes — mock the ORM object
    # by patching the Elective constructor to return a MagicMock with required attributes
    import datetime as dt
    from unittest.mock import patch
    from app.models.electives import Elective

    fake_elective = MagicMock(spec=Elective)
    fake_elective.id = uuid.uuid4()
    fake_elective.tenant_id = tenant_id
    fake_elective.curriculum_id = payload.curriculum_id
    fake_elective.code = "ELEC-CARD-01"
    fake_elective.title = "Clinical Cardiology Elective"
    fake_elective.block = "Block 1"
    fake_elective.elective_type = "clinical"
    fake_elective.capacity = 10
    fake_elective.created_at = dt.datetime(2026, 6, 30, 12, 0, tzinfo=dt.timezone.utc)
    fake_elective.updated_at = dt.datetime(2026, 6, 30, 12, 0, tzinfo=dt.timezone.utc)

    service = ElectiveService(db=mock_db)
    with patch("app.services.elective_service.Elective", return_value=fake_elective):
        result = await service.create_elective(tenant_id=tenant_id, payload=payload, actor_id=uuid.uuid4())

    assert isinstance(result, ElectiveResponse)
    assert result.code == "ELEC-CARD-01"
    assert result.block == "Block 1"
    mock_db.flush.assert_awaited_once()


# ---------------------------------------------------------------------------
# ELEC-002: Submit student preferences (full-block replace, idempotent)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_elec_002_submit_preferences_idempotent(
    test_db_session: AsyncSession, tenant_id: uuid.UUID, student_id: uuid.UUID
) -> None:
    """ELEC-002: Submit preferences: full-block replace; re-submit replaces existing set."""
    from app.services.elective_service import ElectiveService
    from app.schemas.electives import PreferencesSubmitRequest, PreferenceItem
    from app.models.electives import Elective, StudentElectivePreference

    elective_ids = [uuid.uuid4() for _ in range(3)]
    
    # Seed electives
    for eid in elective_ids:
        elective = Elective(
            id=eid,
            tenant_id=tenant_id,
            curriculum_id=uuid.uuid4(),
            code=f"ELEC-{eid}",
            title="Elective",
            block="Block 1",
            elective_type="clinical",
            capacity=10,
        )
        test_db_session.add(elective)
    await test_db_session.commit()

    payload = PreferencesSubmitRequest(
        student_id=student_id,
        block="Block 1",
        preferences=[
            PreferenceItem(elective_id=elective_ids[0], rank_position=1),
            PreferenceItem(elective_id=elective_ids[1], rank_position=2),
            PreferenceItem(elective_id=elective_ids[2], rank_position=3),
        ],
    )

    service = ElectiveService(db=test_db_session)
    # First submission
    await service.submit_preferences(tenant_id=tenant_id, payload=payload, actor_id=student_id)
    # Second submission (idempotent — should replace)
    await service.submit_preferences(tenant_id=tenant_id, payload=payload, actor_id=student_id)
    await test_db_session.commit()

    # Query preferences
    from sqlalchemy import select
    result = await test_db_session.execute(
        select(StudentElectivePreference).where(
            StudentElectivePreference.tenant_id == tenant_id,
            StudentElectivePreference.student_id == student_id,
            StudentElectivePreference.block == "Block 1",
            StudentElectivePreference.deleted_at.is_(None),
        )
    )
    prefs = result.scalars().all()
    assert len(prefs) == 3


# ---------------------------------------------------------------------------
# ELEC-E001: Re-submit preferences replaces previous set
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_elec_e001_preferences_replace_on_resubmit(
    test_db_session: AsyncSession, tenant_id: uuid.UUID, student_id: uuid.UUID
) -> None:
    """ELEC-E001: Student submits 5 preferences, then re-submits 3. Final state = 3 preferences only."""
    from app.services.elective_service import ElectiveService
    from app.schemas.electives import PreferencesSubmitRequest, PreferenceItem
    from app.models.electives import Elective, StudentElectivePreference

    elective_ids = [uuid.uuid4() for _ in range(5)]
    
    # Seed electives
    for eid in elective_ids:
        elective = Elective(
            id=eid,
            tenant_id=tenant_id,
            curriculum_id=uuid.uuid4(),
            code=f"ELEC-{eid}",
            title="Elective",
            block="Block 1",
            elective_type="clinical",
            capacity=10,
        )
        test_db_session.add(elective)
    await test_db_session.commit()

    first_payload = PreferencesSubmitRequest(
        student_id=student_id,
        block="Block 1",
        preferences=[PreferenceItem(elective_id=elective_ids[i], rank_position=i + 1) for i in range(5)],
    )
    second_payload = PreferencesSubmitRequest(
        student_id=student_id,
        block="Block 1",
        preferences=[PreferenceItem(elective_id=elective_ids[i], rank_position=i + 1) for i in range(3)],
    )

    service = ElectiveService(db=test_db_session)
    await service.submit_preferences(tenant_id=tenant_id, payload=first_payload, actor_id=student_id)
    await test_db_session.commit()

    result = await service.submit_preferences(tenant_id=tenant_id, payload=second_payload, actor_id=student_id)
    await test_db_session.commit()

    # Query active preferences
    from sqlalchemy import select
    res = await test_db_session.execute(
        select(StudentElectivePreference).where(
            StudentElectivePreference.tenant_id == tenant_id,
            StudentElectivePreference.student_id == student_id,
            StudentElectivePreference.block == "Block 1",
            StudentElectivePreference.deleted_at.is_(None),
        )
    )
    active_prefs = res.scalars().all()
    assert len(active_prefs) == 3


# ---------------------------------------------------------------------------
# ELEC-E002: Tie-breaking in ranked allocation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_elec_e002_tie_breaking_deterministic(
    mock_db: AsyncMock, tenant_id: uuid.UUID
) -> None:
    """ELEC-E002: When two students have same submitted_at, tie broken by deterministic hash of student_id."""
    # This test verifies that running the ranked algorithm twice with same inputs produces same result.
    from app.services.elective_service import ElectiveService

    service = ElectiveService(db=mock_db)
    # Verify tie-breaking function exists and is deterministic
    s1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
    s2 = uuid.UUID("00000000-0000-0000-0000-000000000002")
    run_id = uuid.uuid4()

    rank1 = service._tiebreak_rank(s1, run_id)
    rank2 = service._tiebreak_rank(s1, run_id)  # same call — must be identical
    assert rank1 == rank2  # deterministic
    assert service._tiebreak_rank(s1, run_id) != service._tiebreak_rank(s2, run_id)  # different students differ


# ---------------------------------------------------------------------------
# ELEC-E003: Student withdraws after allocation — capacity restored
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_elec_e003_withdraw_restores_capacity(
    mock_db: AsyncMock, tenant_id: uuid.UUID, student_id: uuid.UUID
) -> None:
    """ELEC-E003: Withdrawing after allocation removes the allocation row and restores capacity."""
    from app.services.elective_service import ElectiveService

    # Mock: execute returns result with a MagicMock allocation (not None, so the service proceeds)
    fake_alloc = MagicMock()
    fake_alloc.deleted_at = None  # Will be set by service
    fake_alloc.student_id = student_id
    fake_alloc.elective_id = uuid.uuid4()
    fake_alloc.block = "Block 1"

    result_with_alloc = MagicMock()
    result_with_alloc.scalar_one_or_none = MagicMock(return_value=fake_alloc)
    mock_db.execute = AsyncMock(return_value=result_with_alloc)

    service = ElectiveService(db=mock_db)
    allocation_id = uuid.uuid4()
    await service.withdraw_allocation(
        tenant_id=tenant_id,
        allocation_id=allocation_id,
        actor_id=student_id,
    )
    mock_db.flush.assert_awaited()
    # Verify deleted_at was set
    assert fake_alloc.deleted_at is not None


# ---------------------------------------------------------------------------
# ELEC-E004: Dry-run and live run use locked capacity independently
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_elec_e004_dry_run_does_not_write(
    mock_db: AsyncMock, tenant_id: uuid.UUID
) -> None:
    """ELEC-E004: Dry-run run_allocation makes no writes to elective_allocations."""
    from app.services.elective_service import ElectiveService
    from app.schemas.electives import AllocationRunRequest

    elective_id_a = str(uuid.uuid4())
    # Mock: execute returns rows for the elective lock query + empty prefs + empty allocated set
    call_count = 0
    def side_effect_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:  # statement timeout SET LOCAL
            result.fetchall = MagicMock(return_value=None)
            return result
        if call_count == 2:  # FOR SHARE lock query
            result.fetchall = MagicMock(return_value=[(elective_id_a, 5)])
            return result
        if call_count == 3:  # already_allocated check
            result.fetchall = MagicMock(return_value=[])
            return result
        if call_count == 4:  # preferences fetch
            result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
            return result
        result.fetchall = MagicMock(return_value=[])
        result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        return result

    mock_db.execute = AsyncMock(side_effect=lambda *a, **kw: side_effect_execute(*a, **kw))

    payload = AllocationRunRequest(
        curriculum_id=uuid.uuid4(),
        block="Block 1",
        algorithm="ranked",
        dry_run=True,
        force_reallocate=None,
    )
    service = ElectiveService(db=mock_db)
    result = await service.run_allocation(tenant_id=tenant_id, request=payload, actor_id=uuid.uuid4())

    assert result.dry_run is True
    # No rows should be added in dry-run mode
    mock_db.add.assert_not_called()
    mock_db.flush.assert_not_awaited()


# ---------------------------------------------------------------------------
# ELEC-E005: Submit preferences after block is already allocated → SNX-ELEC-002
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_elec_e005_submit_preferences_blocked_after_allocation(
    mock_db: AsyncMock, tenant_id: uuid.UUID, student_id: uuid.UUID
) -> None:
    """ELEC-E005: If block already allocated, submit_preferences must raise SNX-ELEC-002."""
    from app.services.elective_service import ElectiveService, ElectiveBlockAllocatedError
    from app.schemas.electives import PreferencesSubmitRequest, PreferenceItem

    # Mock: allocation exists for this student+block
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=MagicMock())  # existing allocation
    mock_db.execute = AsyncMock(return_value=mock_result)

    payload = PreferencesSubmitRequest(
        student_id=student_id,
        block="Block 1",
        preferences=[PreferenceItem(elective_id=uuid.uuid4(), rank_position=1)],
    )
    service = ElectiveService(db=mock_db)

    with pytest.raises(ElectiveBlockAllocatedError) as exc_info:
        await service.submit_preferences(tenant_id=tenant_id, payload=payload, actor_id=student_id)

    assert "SNX-ELEC-002" in exc_info.value.code


# ---------------------------------------------------------------------------
# ELEC-E006: Duplicate rank position in same block → validation error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_elec_e006_duplicate_rank_rejected(tenant_id: uuid.UUID, student_id: uuid.UUID) -> None:
    """ELEC-E006: Two preferences with same rank_position in same block must be rejected at schema level."""
    from pydantic import ValidationError
    from app.schemas.electives import PreferencesSubmitRequest, PreferenceItem

    elective_id_1 = uuid.uuid4()
    elective_id_2 = uuid.uuid4()

    with pytest.raises(ValidationError):
        PreferencesSubmitRequest(
            student_id=student_id,
            block="Block 1",
            preferences=[
                PreferenceItem(elective_id=elective_id_1, rank_position=1),
                PreferenceItem(elective_id=elective_id_2, rank_position=1),  # duplicate rank
            ],
        )


# ---------------------------------------------------------------------------
# ELEC-E007: Elective belongs to wrong block → validation error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_elec_e007_wrong_block_elective_rejected(
    test_db_session: AsyncSession, tenant_id: uuid.UUID, student_id: uuid.UUID
) -> None:
    """ELEC-E007: Preference referencing a Block 2 elective submitted for Block 1 must be rejected."""
    from app.services.elective_service import ElectiveService, ElectiveWrongBlockError
    from app.schemas.electives import PreferencesSubmitRequest, PreferenceItem
    from app.models.electives import Elective

    wrong_elective_id = uuid.uuid4()
    
    # Seed wrong elective (Block 2)
    elective = Elective(
        id=wrong_elective_id,
        tenant_id=tenant_id,
        curriculum_id=uuid.uuid4(),
        code=f"ELEC-{wrong_elective_id}",
        title="Elective",
        block="Block 2",  # Block 2!
        elective_type="clinical",
        capacity=10,
    )
    test_db_session.add(elective)
    await test_db_session.commit()

    payload = PreferencesSubmitRequest(
        student_id=student_id,
        block="Block 1",  # block requested is Block 1
        preferences=[PreferenceItem(elective_id=wrong_elective_id, rank_position=1)],
    )
    service = ElectiveService(db=test_db_session)

    with pytest.raises(ElectiveWrongBlockError) as exc_info:
        await service.submit_preferences(tenant_id=tenant_id, payload=payload, actor_id=student_id)

    assert "SNX-ELEC-003" in exc_info.value.code
