"""
Integration Tests — Leave Management (Phase 2).

Tests: LEV-001, LEV-002, LEV-003, LEV-004, LEV-E001

All tests require a live PostgreSQL test database.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from app.schemas.leave import LeaveRequestCreate
from app.services.leave_service import LeaveService
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.errors import InvalidStateTransitionError, ResourceNotFoundError

pytestmark = pytest.mark.anyio


async def _seed_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    await db.execute(
        text("""
            INSERT INTO tenants (id, name, code, institution_type, regulatory_body, is_active, created_at, updated_at)
            VALUES (:id, 'JMN Test', 'JMN', 'medical', 'NMC', true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": tenant_id},
    )


async def _seed_student(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    batch_id: uuid.UUID,
    student_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    ay_id, prog_id, cur_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    await db.execute(
        text("""
            INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current)
            VALUES (:id, :tid, '2024-25', '2024-08-01', '2025-07-31', true)
            ON CONFLICT DO NOTHING
        """),
        {"id": ay_id, "tid": tenant_id},
    )
    await db.execute(
        text("""
            INSERT INTO programs (id, tenant_id, name, code, type, duration_years)
            VALUES (:id, :tid, 'MBBS', 'MBBS', 'professional_phase', 4)
            ON CONFLICT DO NOTHING
        """),
        {"id": prog_id, "tid": tenant_id},
    )
    await db.execute(
        text("""
            INSERT INTO curricula (id, tenant_id, program_id, name, version_code)
            VALUES (:id, :tid, :pid, 'CBME 2023', '2023')
            ON CONFLICT DO NOTHING
        """),
        {"id": cur_id, "tid": tenant_id, "pid": prog_id},
    )
    await db.execute(
        text("""
            INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code)
            VALUES (:id, :tid, :ayid, :pid, 'MBBS-2024', 'MBBS2024')
            ON CONFLICT DO NOTHING
        """),
        {"id": batch_id, "tid": tenant_id, "pid": prog_id, "ayid": ay_id},
    )
    await db.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, :email, 'Test Student', 'hashed', true)
            ON CONFLICT DO NOTHING
        """),
        {"id": user_id, "tid": tenant_id, "email": f"student_{user_id}@test.com"},
    )
    await db.execute(
        text("""
            INSERT INTO students (id, tenant_id, user_id, batch_id, roll_number, admission_year, status)
            VALUES (:id, :tid, :uid, :bid, :roll, 2024, 'active')
            ON CONFLICT DO NOTHING
        """),
        {
            "id": student_id,
            "tid": tenant_id,
            "uid": user_id,
            "bid": batch_id,
            "roll": f"R_{str(student_id)[:8]}",
        },
    )


# ---------------------------------------------------------------------------
# LEV-001: Student creates leave request
# ---------------------------------------------------------------------------


async def test_lev_001_create_leave_request(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """LEV-001: Student can submit a leave request in pending state."""
    await _seed_tenant(db_session, tenant_id)
    student_id = uuid.uuid4()
    batch_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await _seed_student(db_session, tenant_id, batch_id, student_id, user_id)
    await db_session.commit()

    service = LeaveService(db=db_session, tenant_id=tenant_id, actor_id=user_id)
    today = date.today()
    req = LeaveRequestCreate(
        leave_type="medical",
        start_date=today,
        end_date=today + timedelta(days=2),
        reason="Fever — doctor's certificate attached",
    )
    leave = await service.create_leave_request(student_id=student_id, req=req)
    await db_session.flush()
    await db_session.refresh(leave)

    assert leave.student_id == student_id
    assert leave.status == "pending"
    assert leave.leave_type == "medical"
    assert leave.tenant_id == tenant_id
    await db_session.commit()


# ---------------------------------------------------------------------------
# LEV-002: HOD approves leave request
# ---------------------------------------------------------------------------


async def test_lev_002_approve_leave_request(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """LEV-002: HOD can approve a pending leave request. Status → 'approved'."""
    await _seed_tenant(db_session, tenant_id)
    hod_id = uuid.uuid4()
    student_id = uuid.uuid4()
    batch_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await _seed_student(db_session, tenant_id, batch_id, student_id, user_id)
    # Seed HOD user
    await db_session.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, :email, 'Test HOD', 'hashed', true)
            ON CONFLICT DO NOTHING
        """),
        {"id": hod_id, "tid": tenant_id, "email": f"hod_{hod_id}@test.com"},
    )
    await db_session.commit()

    # Student creates request
    student_svc = LeaveService(db=db_session, tenant_id=tenant_id, actor_id=user_id)
    today = date.today()
    req = LeaveRequestCreate(
        leave_type="academic",
        start_date=today,
        end_date=today,
        reason="Academic conference participation",
    )
    leave = await student_svc.create_leave_request(student_id=student_id, req=req)
    await db_session.commit()

    # HOD approves
    hod_svc = LeaveService(db=db_session, tenant_id=tenant_id, actor_id=hod_id)
    approved = await hod_svc.approve_leave(leave.id, remarks="Approved for conference")
    await db_session.flush()
    await db_session.refresh(approved)

    assert approved.status == "approved"
    await db_session.commit()


# ---------------------------------------------------------------------------
# LEV-003: Rejecting a leave request
# ---------------------------------------------------------------------------


async def test_lev_003_reject_leave_request(db_session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """LEV-003: HOD can reject a pending leave request. Status → 'rejected'."""
    await _seed_tenant(db_session, tenant_id)
    hod_id = uuid.uuid4()
    student_id = uuid.uuid4()
    batch_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await _seed_student(db_session, tenant_id, batch_id, student_id, user_id)
    # Seed HOD user
    await db_session.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, :email, 'Test HOD', 'hashed', true)
            ON CONFLICT DO NOTHING
        """),
        {"id": hod_id, "tid": tenant_id, "email": f"hod_{hod_id}@test.com"},
    )
    await db_session.commit()

    student_svc = LeaveService(db=db_session, tenant_id=tenant_id, actor_id=user_id)
    req = LeaveRequestCreate(
        leave_type="casual",
        start_date=date.today(),
        end_date=date.today(),
        reason="Personal work at home — need leave",
    )
    leave = await student_svc.create_leave_request(student_id=student_id, req=req)
    await db_session.commit()

    hod_svc = LeaveService(db=db_session, tenant_id=tenant_id, actor_id=hod_id)
    rejected = await hod_svc.reject_leave(leave.id, remarks="Attendance already below threshold")
    await db_session.flush()
    await db_session.refresh(rejected)

    assert rejected.status == "rejected"
    await db_session.commit()


# ---------------------------------------------------------------------------
# LEV-004: Cannot approve an already-rejected leave
# ---------------------------------------------------------------------------


async def test_lev_004_cannot_approve_rejected_leave(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """LEV-004: Approving an already-rejected leave raises InvalidStateTransitionError."""
    await _seed_tenant(db_session, tenant_id)
    hod_id = uuid.uuid4()
    student_id = uuid.uuid4()
    batch_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await _seed_student(db_session, tenant_id, batch_id, student_id, user_id)
    # Seed HOD user
    await db_session.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, :email, 'Test HOD', 'hashed', true)
            ON CONFLICT DO NOTHING
        """),
        {"id": hod_id, "tid": tenant_id, "email": f"hod_{hod_id}@test.com"},
    )
    await db_session.commit()

    student_svc = LeaveService(db=db_session, tenant_id=tenant_id, actor_id=user_id)
    req = LeaveRequestCreate(
        leave_type="casual",
        start_date=date.today(),
        end_date=date.today(),
        reason="Personal errand to complete today",
    )
    leave = await student_svc.create_leave_request(student_id=student_id, req=req)
    await db_session.commit()

    hod_svc = LeaveService(db=db_session, tenant_id=tenant_id, actor_id=hod_id)
    await hod_svc.reject_leave(leave.id, remarks="Not valid reason")
    await db_session.commit()

    # Now try to approve — should fail
    with pytest.raises(InvalidStateTransitionError):
        await hod_svc.approve_leave(leave.id)


# ---------------------------------------------------------------------------
# LEV-E001: Leave spanning conducted sessions — validation
# ---------------------------------------------------------------------------


async def test_lev_e001_leave_not_found_raises_error(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """LEV-E001: Approving a non-existent leave request raises ResourceNotFoundError."""
    await _seed_tenant(db_session, tenant_id)
    await db_session.commit()

    svc = LeaveService(db=db_session, tenant_id=tenant_id, actor_id=uuid.uuid4())
    fake_id = uuid.uuid4()

    with pytest.raises(ResourceNotFoundError):
        await svc.approve_leave(fake_id)
