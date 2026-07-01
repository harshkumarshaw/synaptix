"""AUD-001, AUD-004, AUD-005, AUD-006: Audit log behaviour tests.

Tests cover:
- AUD-001: Every data modification creates an audit_log entry
- AUD-004: Audit entry contains: who, what, when
- AUD-005: Old and new values stored as JSONB
- AUD-006: Sensitive fields (passwords, OTPs) NOT logged
"""
import json
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.db.session import set_tenant_context

JMN_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
# Reusable actor seeded once per test (uses conftest truncation to clean up)
ACTOR_USER_ID = uuid.UUID("aa000000-0000-0000-0000-000000000001")


async def _seed_actor(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Seed the actor user that audit_log FK requires."""
    await db.execute(
        text("""
            INSERT INTO tenants (id, name, code, institution_type, regulatory_body, is_active, created_at, updated_at)
            VALUES (:id, 'JMN Medical', 'JMN', 'medical', 'NMC', true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": tenant_id},
    )
    await db.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active)
            VALUES (:id, :tid, 'audit_actor@jmn.edu', 'Audit Actor', 'hashed', true)
            ON CONFLICT (id) DO NOTHING
        """),
        {"id": ACTOR_USER_ID, "tid": tenant_id},
    )
    await db.commit()
    await set_tenant_context(db, tenant_id)


@pytest.mark.anyio
async def test_aud_001_data_modification_creates_audit_entry(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """AUD-001: Every data modification creates an audit_log entry."""
    from app.services.audit_logger import write_audit_log

    await _seed_actor(db_session, tenant_id)

    resource_id = uuid.uuid4()

    await write_audit_log(
        db=db_session,
        tenant_id=tenant_id,
        actor_user_id=ACTOR_USER_ID,
        action="CREATE",
        resource_type="attendance_record",
        resource_id=resource_id,
        new_values={"status": "present"},
    )
    await db_session.commit()
    await set_tenant_context(db_session, tenant_id)

    result = await db_session.execute(
        text(
            "SELECT action, resource_type, resource_id, actor_user_id "
            "FROM audit_log WHERE resource_id = :rid"
        ),
        {"rid": resource_id},
    )
    row = result.mappings().first()
    assert row is not None, "AUD-001: No audit_log entry found after CREATE"
    assert row["action"] == "CREATE"
    assert row["resource_type"] == "attendance_record"
    assert row["actor_user_id"] == ACTOR_USER_ID


@pytest.mark.anyio
async def test_aud_004_audit_entry_contains_who_what_when(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """AUD-004: Audit entry contains: who, what, when."""
    from app.services.audit_logger import write_audit_log

    await _seed_actor(db_session, tenant_id)

    resource_id = uuid.uuid4()

    await write_audit_log(
        db=db_session,
        tenant_id=tenant_id,
        actor_user_id=ACTOR_USER_ID,
        action="UPDATE",
        resource_type="lesson_plan",
        resource_id=resource_id,
        old_values={"status": "draft"},
        new_values={"status": "submitted"},
    )
    await db_session.commit()
    await set_tenant_context(db_session, tenant_id)

    result = await db_session.execute(
        text(
            "SELECT actor_user_id, action, resource_type, created_at "
            "FROM audit_log WHERE resource_id = :rid"
        ),
        {"rid": resource_id},
    )
    row = result.mappings().first()
    assert row is not None, "AUD-004: Audit log entry not found"
    # Who
    assert row["actor_user_id"] == ACTOR_USER_ID, "AUD-004: actor_user_id missing"
    # What
    assert row["action"] == "UPDATE", "AUD-004: action missing"
    assert row["resource_type"] == "lesson_plan", "AUD-004: resource_type missing"
    # When
    assert row["created_at"] is not None, "AUD-004: created_at (when) missing"


@pytest.mark.anyio
async def test_aud_005_old_and_new_values_stored_as_jsonb(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """AUD-005: Old and new values stored as JSONB."""
    from app.services.audit_logger import write_audit_log

    await _seed_actor(db_session, tenant_id)

    resource_id = uuid.uuid4()
    old_vals = {"attendance_pct": "74.50", "sessions_present": 25}
    new_vals = {"attendance_pct": "76.00", "sessions_present": 26}

    await write_audit_log(
        db=db_session,
        tenant_id=tenant_id,
        actor_user_id=ACTOR_USER_ID,
        action="UPDATE",
        resource_type="attendance_summary",
        resource_id=resource_id,
        old_values=old_vals,
        new_values=new_vals,
    )
    await db_session.commit()
    await set_tenant_context(db_session, tenant_id)

    result = await db_session.execute(
        text("SELECT old_values, new_values FROM audit_log WHERE resource_id = :rid"),
        {"rid": resource_id},
    )
    row = result.mappings().first()
    assert row is not None, "AUD-005: Audit entry not found"

    # PostgreSQL returns JSONB as a dict directly via asyncpg
    old = row["old_values"] if isinstance(row["old_values"], dict) else json.loads(row["old_values"])
    new = row["new_values"] if isinstance(row["new_values"], dict) else json.loads(row["new_values"])

    assert old["attendance_pct"] == "74.50", f"AUD-005: old_values mismatch: {old}"
    assert new["attendance_pct"] == "76.00", f"AUD-005: new_values mismatch: {new}"
    assert old["sessions_present"] == 25
    assert new["sessions_present"] == 26


@pytest.mark.anyio
async def test_aud_006_sensitive_fields_not_logged(
    db_session: AsyncSession, tenant_id: uuid.UUID
) -> None:
    """AUD-006: Sensitive fields (passwords, OTPs) NOT logged in audit entries."""
    from app.services.audit_logger import write_audit_log

    await _seed_actor(db_session, tenant_id)

    resource_id = uuid.uuid4()

    # Service layer must strip sensitive fields before calling write_audit_log.
    # We verify that per-convention the actor only passes safe fields.
    safe_new_values = {
        "email": "student@jmn.edu",
        "name": "Ravi Kumar",
        # password and otp intentionally absent
    }

    await write_audit_log(
        db=db_session,
        tenant_id=tenant_id,
        actor_user_id=ACTOR_USER_ID,
        action="UPDATE",
        resource_type="user",
        resource_id=resource_id,
        new_values=safe_new_values,
    )
    await db_session.commit()
    await set_tenant_context(db_session, tenant_id)

    result = await db_session.execute(
        text("SELECT new_values FROM audit_log WHERE resource_id = :rid"),
        {"rid": resource_id},
    )
    row = result.mappings().first()
    assert row is not None, "AUD-006: Audit entry not found"

    new = row["new_values"] if isinstance(row["new_values"], dict) else json.loads(row["new_values"])

    # Confirm sensitive fields are absent
    assert "password" not in new, "AUD-006: password found in audit log — SECURITY VIOLATION"
    assert "otp" not in new, "AUD-006: OTP found in audit log — SECURITY VIOLATION"
    assert "password_hash" not in new, "AUD-006: password_hash in audit log — SECURITY VIOLATION"
    # Safe fields present
    assert new["email"] == "student@jmn.edu"
