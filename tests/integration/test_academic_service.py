import uuid
from datetime import date, time
import pytest
from sqlalchemy import select

from app.models.academic_year import AcademicYear
from app.models.program import Program
from app.models.curriculum import Curriculum
from app.models.course import Course
from app.models.batch import Batch
from app.models.section import Section
from app.models.timetable_slot import TimetableSlot
from app.models.timetable_entry import TimetableEntry
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.user import User
from app.models.tenant import Tenant

from app.services.academic_service import AcademicService


@pytest.mark.anyio
async def test_academic_service_flows(db_session, tenant_id):
    """Test academic structure and timetable slot configuration via AcademicService."""
    academic_service = AcademicService(db_session)

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

    # 2. Seed Academic Year
    ay = AcademicYear(
        tenant_id=tenant_id,
        name="2026-2027",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 7, 31),
        is_current=True,
    )
    db_session.add(ay)
    await db_session.commit()
    await db_session.refresh(ay)

    # 3. Seed Program
    prog = Program(
        tenant_id=tenant_id,
        name="MBBS",
        code="MBBS-CBME",
        type="professional_phase",
        duration_years=5,
    )
    db_session.add(prog)
    await db_session.commit()
    await db_session.refresh(prog)

    # 4. Seed Curriculum
    curr = Curriculum(
        tenant_id=tenant_id,
        program_id=prog.id,
        name="NMC CBME 2023",
        version_code="CBME-2023",
    )
    db_session.add(curr)
    await db_session.commit()
    await db_session.refresh(curr)

    # 5. Seed Department
    dept = Department(
        tenant_id=tenant_id,
        name="Anatomy",
        code="ANAT",
    )
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    # 6. Seed Course
    course = Course(
        tenant_id=tenant_id,
        curriculum_id=curr.id,
        name="Human Anatomy I",
        code="ANAT-101",
        department_id=dept.id,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)

    # 7. Seed Batch & Section
    batch = Batch(
        tenant_id=tenant_id,
        academic_year_id=ay.id,
        program_id=prog.id,
        name="MBBS 2026 Batch",
        code="MBBS-2026",
    )
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    sect = Section(
        tenant_id=tenant_id,
        batch_id=batch.id,
        name="Section A",
    )
    db_session.add(sect)
    await db_session.commit()
    await db_session.refresh(sect)

    # 8. Seed Users for Faculty
    faculty_user = User(
        tenant_id=tenant_id,
        email="faculty_anat@jmn.edu",
        full_name="Dr. Jane Anatomist",
        password_hash="hashedpassword123",
        is_active=True,
    )
    db_session.add(faculty_user)
    await db_session.commit()
    await db_session.refresh(faculty_user)

    # 9. Seed Faculty profile
    faculty = Faculty(
        tenant_id=tenant_id,
        user_id=faculty_user.id,
        department_id=dept.id,
        designation="Professor",
        employee_id="EMP-ANAT-01",
    )
    db_session.add(faculty)
    await db_session.commit()
    await db_session.refresh(faculty)

    # 10. Seed Timetable Slot & Entry
    slot = TimetableSlot(
        tenant_id=tenant_id,
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        end_time=time(10, 0),
        name="Lecture 1",
    )
    db_session.add(slot)
    await db_session.commit()
    await db_session.refresh(slot)

    entry = TimetableEntry(
        tenant_id=tenant_id,
        batch_id=batch.id,
        course_id=course.id,
        faculty_id=faculty.id,
        slot_id=slot.id,
        room_number="Lecture Hall 1",
    )
    db_session.add(entry)
    await db_session.commit()

    # ── Verify Academic Service ──
    programs = await academic_service.get_programs(tenant_id)
    assert len(programs) > 0
    assert prog.id in [p.id for p in programs]

    courses = await academic_service.get_courses(tenant_id)
    assert len(courses) > 0
    assert course.id in [c.id for c in courses]

    batches = await academic_service.get_batches(tenant_id)
    assert len(batches) > 0
    assert batch.id in [b.id for b in batches]

    timetable = await academic_service.get_timetable(tenant_id, batch.id)
    assert len(timetable) == 1
    assert timetable[0].course_id == course.id
    assert timetable[0].faculty_id == faculty.id
    assert timetable[0].slot_id == slot.id
