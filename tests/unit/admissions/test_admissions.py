import uuid

import pytest
from app.schemas.admissions import AdmissionApplicationCreate
from app.services.admission_service import AdmissionService, AdmissionServiceError
from sqlalchemy import text


async def seed_user(db_session, tenant_id, user_id):
    await db_session.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES (:id, :t_id, :email, 'Admin User', true)"
        ),
        {"id": user_id, "t_id": tenant_id, "email": f"admin_{user_id}@jmn.edu"},
    )
    await db_session.commit()


@pytest.mark.anyio
async def test_adm_001_create_application(db_session, tenant_id):
    """
    Test ID: ADM-001
    Verifies: Create admission application.
    """
    user_id = uuid.uuid4()
    await seed_user(db_session, tenant_id, user_id)

    # Seed program
    prog_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-ADM', 'professional_phase', 5)"
        ),
        {"id": prog_id, "t_id": tenant_id},
    )
    await db_session.commit()

    service = AdmissionService(db_session)
    data = AdmissionApplicationCreate(
        application_number="APP-1001", student_name="Jane Doe", applied_for_program_id=prog_id
    )

    res = await service.create_application(tenant_id, user_id, data)
    assert res.application_number == "APP-1001"
    assert res.student_name == "Jane Doe"
    assert res.applied_for_program_id == prog_id


@pytest.mark.anyio
async def test_adm_002_list_applications_pagination(db_session, tenant_id):
    """
    Test ID: ADM-002
    Verifies: List admission applications with pagination.
    """
    user_id = uuid.uuid4()
    await seed_user(db_session, tenant_id, user_id)

    prog_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-ADM2', 'professional_phase', 5)"
        ),
        {"id": prog_id, "t_id": tenant_id},
    )
    await db_session.commit()

    service = AdmissionService(db_session)

    # Create 3 applications
    for i in range(3):
        data = AdmissionApplicationCreate(
            application_number=f"APP-200{i}",
            student_name=f"Student {i}",
            applied_for_program_id=prog_id,
        )
        await service.create_application(tenant_id, user_id, data)

    res = await service.list_applications(tenant_id, offset=0, limit=2)
    assert len(res) == 2
    # The first 2 of 3 applications (limit=2). Since all are created in the same
    # instant, order may vary — assert the set of returned numbers is a subset of
    # the 3 created and that pagination limits correctly to 2 results.
    returned_numbers = {r.application_number for r in res}
    all_numbers = {"APP-2000", "APP-2001", "APP-2002"}
    assert returned_numbers.issubset(all_numbers), (
        f"ADM-002: Unexpected application numbers returned: {returned_numbers}"
    )
    assert len(returned_numbers) == 2, "ADM-002: Pagination limit=2 should return exactly 2 records"


@pytest.mark.anyio
async def test_adm_003_get_application_by_id(db_session, tenant_id):
    """
    Test ID: ADM-003
    Verifies: Get admission application by ID.
    """
    user_id = uuid.uuid4()
    await seed_user(db_session, tenant_id, user_id)

    prog_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-ADM3', 'professional_phase', 5)"
        ),
        {"id": prog_id, "t_id": tenant_id},
    )
    await db_session.commit()

    service = AdmissionService(db_session)
    data = AdmissionApplicationCreate(
        application_number="APP-3001", student_name="Bob Smith", applied_for_program_id=prog_id
    )
    created = await service.create_application(tenant_id, user_id, data)

    res = await service.get_application(tenant_id, created.id)
    assert res.id == created.id
    assert res.student_name == "Bob Smith"


@pytest.mark.anyio
async def test_adm_004_unique_application_number(db_session, tenant_id):
    """
    Test ID: ADM-004
    Verifies: Unique application_number per tenant enforced.
    """
    user_id = uuid.uuid4()
    await seed_user(db_session, tenant_id, user_id)

    prog_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) VALUES (:id, :t_id, 'MBBS', 'MBBS-CBME-ADM4', 'professional_phase', 5)"
        ),
        {"id": prog_id, "t_id": tenant_id},
    )
    await db_session.commit()

    service = AdmissionService(db_session)
    data1 = AdmissionApplicationCreate(
        application_number="APP-DUP", student_name="Alice Blue", applied_for_program_id=prog_id
    )
    data2 = AdmissionApplicationCreate(
        application_number="APP-DUP", student_name="Charlie Green", applied_for_program_id=prog_id
    )

    await service.create_application(tenant_id, user_id, data1)

    # Need to rollback the failed sql statement inside service or transaction block
    with pytest.raises(AdmissionServiceError) as exc:
        await service.create_application(tenant_id, user_id, data2)
    assert "already exists" in str(exc.value)
