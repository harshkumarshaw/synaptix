import pytest
import uuid
import datetime
from datetime import UTC
from sqlalchemy import text
from app.services.exam_service import ExamService, ExamServiceError
from app.models.exam import Examination, ExamSchedule

pytestmark = pytest.mark.anyio


# Seed helper
async def seed_base_data(db, tenant_id):
    # Seed tenant
    await db.execute(
        text(
            "INSERT INTO tenants (id, name, code, institution_type, regulatory_body, is_active) "
            "VALUES (:id, 'JMN', 'JMN', 'medical', 'NMC', true) ON CONFLICT DO NOTHING"
        ),
        {"id": tenant_id},
    )
    # Seed department
    dept_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO departments (id, tenant_id, name, code) "
            "VALUES (:id, :tid, 'Anatomy', 'ANAT') ON CONFLICT DO NOTHING"
        ),
        {"id": dept_id, "tid": tenant_id},
    )
    # Seed program
    prog_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) "
            "VALUES (:id, :tid, 'MBBS', 'MBBS', 'professional_phase', 4) ON CONFLICT DO NOTHING"
        ),
        {"id": prog_id, "tid": tenant_id},
    )
    # Seed curriculum
    curr_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO curricula (id, tenant_id, program_id, name, version_code) "
            "VALUES (:id, :tid, :pid, 'CBME 2023', '2023') ON CONFLICT DO NOTHING"
        ),
        {"id": curr_id, "tid": tenant_id, "pid": prog_id},
    )
    # Seed course
    course_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO courses (id, tenant_id, curriculum_id, department_id, name, code, default_attendance_category, subject_code) "
            "VALUES (:id, :tid, :cid, :did, 'Anatomy', 'ANAT', 'theory', 'ANAT') ON CONFLICT DO NOTHING"
        ),
        {"id": course_id, "tid": tenant_id, "cid": curr_id, "did": dept_id},
    )
    # Seed user
    user_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active) "
            "VALUES (:id, :tid, 'prof@jmn.edu.in', 'Prof. Ray', 'hash', true) ON CONFLICT DO NOTHING"
        ),
        {"id": user_id, "tid": tenant_id},
    )
    # Seed faculty
    faculty_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO faculty (id, tenant_id, user_id, department_id, designation, employee_id) "
            "VALUES (:id, :tid, :uid, :did, 'Professor', 'EMP001') ON CONFLICT DO NOTHING"
        ),
        {"id": faculty_id, "tid": tenant_id, "uid": user_id, "did": dept_id},
    )
    await db.commit()
    return curr_id, course_id, user_id


class TestExamScheduling:
    async def test_exm_001_create_examination(self, test_db_session, tenant_id):
        """
        Test ID: EXM-001
        Module: examination_management
        Verifies: Create exam schedule.
        """
        curr_id, course_id, user_id = await seed_base_data(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        # Create exam
        exam = await service.create_examination(
            tenant_id=tenant_id,
            curriculum_id=curr_id,
            course_id=course_id,
            exam_type="professional",
            exam_session="Dec 2026",
            academic_year="2026-2027",
            exam_date=datetime.date(2026, 12, 15),
            theory_max_marks=100,
            practical_max_marks=100,
            theory_pass_marks=50,
            practical_pass_marks=50,
        )

        assert exam.id is not None
        assert exam.status == "scheduled"
        assert exam.exam_type == "professional"

        # Create schedule
        room_id = uuid.uuid4()
        start_time = datetime.datetime(2026, 12, 15, 9, 0, tzinfo=UTC)
        end_time = datetime.datetime(2026, 12, 15, 12, 0, tzinfo=UTC)

        sched = await service.create_exam_schedule(
            tenant_id=tenant_id,
            examination_id=exam.id,
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            invigilator_id=user_id,
        )

        assert sched.id is not None
        assert sched.room_id == room_id
        assert sched.invigilator_id == user_id

    async def test_exm_011_room_availability(self, test_db_session, tenant_id):
        """
        Test ID: EXM-011
        Module: examination_management
        Verifies: Exam scheduling: room availability check.
        """
        curr_id, course_id, user_id = await seed_base_data(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        # Create exam 1
        exam1 = await service.create_examination(
            tenant_id=tenant_id,
            curriculum_id=curr_id,
            course_id=course_id,
            exam_type="professional",
            exam_session="Dec 2026",
            academic_year="2026-2027",
            exam_date=datetime.date(2026, 12, 15),
            theory_max_marks=100,
            practical_max_marks=100,
            theory_pass_marks=50,
            practical_pass_marks=50,
        )

        room_id = uuid.uuid4()
        start_time = datetime.datetime(2026, 12, 15, 9, 0, tzinfo=UTC)
        end_time = datetime.datetime(2026, 12, 15, 12, 0, tzinfo=UTC)

        await service.create_exam_schedule(
            tenant_id=tenant_id,
            examination_id=exam1.id,
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            invigilator_id=user_id,
        )

        # Create exam 2 (should clash on room)
        exam2 = await service.create_examination(
            tenant_id=tenant_id,
            curriculum_id=curr_id,
            course_id=course_id,
            exam_type="professional",
            exam_session="Dec 2026",
            academic_year="2026-2027",
            exam_date=datetime.date(2026, 12, 15),
            theory_max_marks=100,
            practical_max_marks=100,
            theory_pass_marks=50,
            practical_pass_marks=50,
        )

        with pytest.raises(ExamServiceError) as exc_info:
            await service.create_exam_schedule(
                tenant_id=tenant_id,
                examination_id=exam2.id,
                room_id=room_id,
                start_time=start_time + datetime.timedelta(hours=1),  # Overlapping
                end_time=end_time + datetime.timedelta(hours=1),
                invigilator_id=uuid.uuid4(),
            )
        assert exc_info.value.code == "SNX-EXM-011"

    async def test_exm_012_invigilator_clash(self, test_db_session, tenant_id):
        """
        Test ID: EXM-012
        Module: examination_management
        Verifies: Exam scheduling: invigilator clash check.
        """
        curr_id, course_id, user_id = await seed_base_data(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        # Create exam 1
        exam1 = await service.create_examination(
            tenant_id=tenant_id,
            curriculum_id=curr_id,
            course_id=course_id,
            exam_type="professional",
            exam_session="Dec 2026",
            academic_year="2026-2027",
            exam_date=datetime.date(2026, 12, 15),
            theory_max_marks=100,
            practical_max_marks=100,
            theory_pass_marks=50,
            practical_pass_marks=50,
        )

        room_id1 = uuid.uuid4()
        start_time = datetime.datetime(2026, 12, 15, 9, 0, tzinfo=UTC)
        end_time = datetime.datetime(2026, 12, 15, 12, 0, tzinfo=UTC)

        await service.create_exam_schedule(
            tenant_id=tenant_id,
            examination_id=exam1.id,
            room_id=room_id1,
            start_time=start_time,
            end_time=end_time,
            invigilator_id=user_id,
        )

        # Create exam 2 (should clash on invigilator)
        exam2 = await service.create_examination(
            tenant_id=tenant_id,
            curriculum_id=curr_id,
            course_id=course_id,
            exam_type="professional",
            exam_session="Dec 2026",
            academic_year="2026-2027",
            exam_date=datetime.date(2026, 12, 15),
            theory_max_marks=100,
            practical_max_marks=100,
            theory_pass_marks=50,
            practical_pass_marks=50,
        )

        room_id2 = uuid.uuid4()
        with pytest.raises(ExamServiceError) as exc_info:
            await service.create_exam_schedule(
                tenant_id=tenant_id,
                examination_id=exam2.id,
                room_id=room_id2,
                start_time=start_time,  # Overlapping
                end_time=end_time,
                invigilator_id=user_id,
            )
        assert exc_info.value.code == "SNX-EXM-012"

    async def test_exm_013_student_clash(self, test_db_session, tenant_id):
        """
        Test ID: EXM-013
        Module: examination_management
        Verifies: Exam scheduling: student clash check.
        """
        curr_id, course_id, user_id = await seed_base_data(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        # Create exam 1
        exam1 = await service.create_examination(
            tenant_id=tenant_id,
            curriculum_id=curr_id,
            course_id=course_id,
            exam_type="professional",
            exam_session="Dec 2026",
            academic_year="2026-2027",
            exam_date=datetime.date(2026, 12, 15),
            theory_max_marks=100,
            practical_max_marks=100,
            theory_pass_marks=50,
            practical_pass_marks=50,
        )

        room_id1 = uuid.uuid4()
        start_time = datetime.datetime(2026, 12, 15, 9, 0, tzinfo=UTC)
        end_time = datetime.datetime(2026, 12, 15, 12, 0, tzinfo=UTC)

        await service.create_exam_schedule(
            tenant_id=tenant_id,
            examination_id=exam1.id,
            room_id=room_id1,
            start_time=start_time,
            end_time=end_time,
            invigilator_id=user_id,
        )

        # Create exam 2 (overlapping time in same curriculum -> student group overlap)
        exam2 = await service.create_examination(
            tenant_id=tenant_id,
            curriculum_id=curr_id,
            course_id=course_id,
            exam_type="professional",
            exam_session="Dec 2026",
            academic_year="2026-2027",
            exam_date=datetime.date(2026, 12, 15),
            theory_max_marks=100,
            practical_max_marks=100,
            theory_pass_marks=50,
            practical_pass_marks=50,
        )

        with pytest.raises(ExamServiceError) as exc_info:
            await service.create_exam_schedule(
                tenant_id=tenant_id,
                examination_id=exam2.id,
                room_id=uuid.uuid4(),
                start_time=start_time,
                end_time=end_time,
                invigilator_id=uuid.uuid4(),
            )
        assert exc_info.value.code == "SNX-EXM-013"

        # Create exam 3 (scheduled on consecutive day -> gap < 1 day check)
        exam3 = await service.create_examination(
            tenant_id=tenant_id,
            curriculum_id=curr_id,
            course_id=course_id,
            exam_type="professional",
            exam_session="Dec 2026",
            academic_year="2026-2027",
            exam_date=datetime.date(2026, 12, 16),
            theory_max_marks=100,
            practical_max_marks=100,
            theory_pass_marks=50,
            practical_pass_marks=50,
        )

        with pytest.raises(ExamServiceError) as exc_info_gap:
            await service.create_exam_schedule(
                tenant_id=tenant_id,
                examination_id=exam3.id,
                room_id=uuid.uuid4(),
                start_time=start_time + datetime.timedelta(days=1),  # consecutive day
                end_time=end_time + datetime.timedelta(days=1),
                invigilator_id=uuid.uuid4(),
            )
        assert exc_info_gap.value.code == "SNX-EXM-014"
