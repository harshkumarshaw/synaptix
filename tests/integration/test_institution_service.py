import uuid
import pytest
from sqlalchemy import select

from packages.shared.errors import StudentNotFoundError
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.user import User
from app.models.batch import Batch
from app.models.section import Section
from app.models.tenant import Tenant
from app.services.institution_service import InstitutionService


@pytest.mark.anyio
async def test_institution_service_flows(db_session, tenant_id):
    """Test department, faculty, and student profile retrieval and status updates."""
    institution_service = InstitutionService(db_session)

    # 1. Ensure Tenant exists
    tenant = await db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(
            id=tenant_id,
            code="JMN",
            name="JMN Medical College",
            institution_type="medical",
            regulatory_body="NMC",
        )
        db_session.add(tenant)
        await db_session.commit()

    # 1b. Clean up existing test data for this tenant to ensure idempotency
    from sqlalchemy import text
    await db_session.execute(text("DELETE FROM timetable_entries WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM timetable_slots WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM students WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM faculty WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM users WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM sections WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM batches WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM courses WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM departments WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM curricula WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM programs WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.execute(text("DELETE FROM academic_years WHERE tenant_id = :id"), {"id": tenant_id})
    await db_session.commit()

    # 2. Seed Department
    dept = Department(
        tenant_id=tenant_id,
        name="Anatomy",
        code="ANAT",
    )
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    # 3. Seed Batch & Section
    # Raw SQL inserts to bypass FK requirements since AcademicYear/Program tables are not in this service's scope
    # Wait, we can just insert them using SQLAlchemy models Batch and Section! We just need to define dummy IDs.
    # To bypass academic_year and program FK constraints, let's create a temporary program and academic year
    # or let's use the DB directly because those tables exist in the database!
    # Yes! The DB schema contains academic_years and programs. So we can insert them or use raw connection,
    # or we can import them from packages/shared if they were there (but they aren't).
    # Since those tables exist, let's just insert them using raw SQL or define dummy objects using SQLAlchemy metadata!
    # Let's insert them using raw connection SQL to make it extremely independent of other models:
    from sqlalchemy import text
    ay_id = uuid.uuid4()
    prog_id = uuid.uuid4()
    
    await db_session.execute(
        text(
            "INSERT INTO academic_years (id, tenant_id, name, start_date, end_date) "
            "VALUES (:id, :tenant_id, '2026-2027', '2026-08-01', '2027-07-31')"
        ),
        {"id": ay_id, "tenant_id": tenant_id}
    )
    await db_session.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) "
            "VALUES (:id, :tenant_id, 'MBBS', 'MBBS-CBME', 'professional_phase', 5)"
        ),
        {"id": prog_id, "tenant_id": tenant_id}
    )
    
    batch = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="MBBS 2026 Batch",
        code="MBBS-2026",
    )
    # Map the academic_year_id and program_id dynamically by setting attributes
    setattr(batch, "academic_year_id", ay_id)
    setattr(batch, "program_id", prog_id)
    db_session.add(batch)
    await db_session.commit()

    sect = Section(
        tenant_id=tenant_id,
        batch_id=batch.id,
        name="Section A",
    )
    db_session.add(sect)
    await db_session.commit()

    # 4. Seed Users for Faculty and Student
    faculty_user = User(
        tenant_id=tenant_id,
        email="faculty_anat@jmn.edu",
        full_name="Dr. Jane Anatomist",
        is_active=True,
    )
    student_user = User(
        tenant_id=tenant_id,
        email="student_1@jmn.edu",
        full_name="John Doe",
        is_active=True,
    )
    db_session.add(faculty_user)
    db_session.add(student_user)
    await db_session.commit()

    # 5. Seed Faculty and Student profiles
    faculty = Faculty(
        tenant_id=tenant_id,
        user_id=faculty_user.id,
        department_id=dept.id,
        designation="Professor",
        employee_id="EMP-ANAT-01",
    )
    student = Student(
        tenant_id=tenant_id,
        user_id=student_user.id,
        batch_id=batch.id,
        section_id=sect.id,
        roll_number="JMN-2026-001",
        admission_year=2026,
        status="active",
    )
    db_session.add(faculty)
    db_session.add(student)
    await db_session.commit()

    # ── Verify Institution Service ──
    departments = await institution_service.get_departments(tenant_id)
    assert len(departments) > 0
    assert dept.id in [d.id for d in departments]

    faculties = await institution_service.get_faculty(tenant_id)
    assert len(faculties) > 0
    assert faculty.id in [f.id for f in faculties]

    students = await institution_service.get_students(tenant_id)
    assert len(students) > 0
    assert student.id in [s.id for s in students]

    # Test Student status update
    updated_student = await institution_service.update_student_status(
        tenant_id, student.id, "detained"
    )
    assert updated_student.status == "detained"

    # Test not found Student update
    with pytest.raises(StudentNotFoundError):
        await institution_service.update_student_status(
            tenant_id, uuid.uuid4(), "active"
        )
