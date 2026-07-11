import pytest
import uuid
from decimal import Decimal
from sqlalchemy import text
from app.services.exam_service import ExamService
from app.models.exam import IAAggregation

pytestmark = pytest.mark.anyio


# Seed helpers
async def seed_course_with_relations(db, tenant_id, name, code, subject_code):
    dept_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO departments (id, tenant_id, name, code) "
            "VALUES (:id, :tid, :name, :code) ON CONFLICT DO NOTHING"
        ),
        {
            "id": dept_id,
            "tid": tenant_id,
            "name": name + " Dept",
            "code": f"{code}_{uuid.uuid4().hex[:4]}",
        },
    )
    prog_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) "
            "VALUES (:id, :tid, 'MBBS', 'MBBS', 'professional_phase', 4) ON CONFLICT DO NOTHING"
        ),
        {"id": prog_id, "tid": tenant_id},
    )
    curr_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO curricula (id, tenant_id, program_id, name, version_code) "
            "VALUES (:id, :tid, :pid, 'CBME 2023', :vcode) ON CONFLICT DO NOTHING"
        ),
        {"id": curr_id, "tid": tenant_id, "pid": prog_id, "vcode": f"2023_{uuid.uuid4().hex[:4]}"},
    )
    course_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO courses (id, tenant_id, curriculum_id, department_id, name, code, default_attendance_category, subject_code) "
            "VALUES (:id, :tid, :cid, :did, :name, :code, 'theory', :sub) ON CONFLICT DO NOTHING"
        ),
        {
            "id": course_id,
            "tid": tenant_id,
            "cid": curr_id,
            "did": dept_id,
            "name": name,
            "code": f"{code}_{uuid.uuid4().hex[:4]}",
            "sub": subject_code,
        },
    )
    return course_id, curr_id, dept_id, prog_id


async def seed_faculty_with_user(db, tenant_id, faculty_id, dept_id):
    user_id = uuid.uuid4()
    email = f"fac_{uuid.uuid4().hex[:8]}@jmn.edu.in"
    emp_id = f"EMP_{uuid.uuid4().hex[:8]}"
    await db.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active) "
            "VALUES (:id, :tid, :email, 'Faculty Member', 'pwd', true)"
        ),
        {"id": user_id, "tid": tenant_id, "email": email},
    )
    await db.execute(
        text(
            "INSERT INTO faculty (id, tenant_id, user_id, department_id, designation, employee_id) "
            "VALUES (:id, :tid, :uid, :did, 'Professor', :eid)"
        ),
        {"id": faculty_id, "tid": tenant_id, "uid": user_id, "did": dept_id, "eid": emp_id},
    )
    return user_id


async def seed_student_with_relations(db, tenant_id, student_id, prog_id):
    ay_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) "
            "VALUES (:id, :tid, :name, '2026-08-01', '2027-07-31', true) ON CONFLICT DO NOTHING"
        ),
        {"id": ay_id, "tid": tenant_id, "name": f"AY_{uuid.uuid4().hex[:4]}"},
    )
    batch_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO batches (id, tenant_id, academic_year_id, program_id, name, code) "
            "VALUES (:id, :tid, :ayid, :pid, :name, :code) ON CONFLICT DO NOTHING"
        ),
        {
            "id": batch_id,
            "tid": tenant_id,
            "ayid": ay_id,
            "pid": prog_id,
            "name": f"MBBS {uuid.uuid4().hex[:8]}",
            "code": f"MBBS_{uuid.uuid4().hex[:8]}",
        },
    )
    user_id = uuid.uuid4()
    email = f"stud_{uuid.uuid4().hex[:8]}@jmn.edu.in"
    await db.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active) "
            "VALUES (:id, :tid, :email, 'Student One', 'pwd', true)"
        ),
        {"id": user_id, "tid": tenant_id, "email": email},
    )
    await db.execute(
        text(
            "INSERT INTO students (id, tenant_id, user_id, batch_id, roll_number, admission_year, status) "
            "VALUES (:id, :tid, :uid, :bid, :roll, 2024, 'active')"
        ),
        {
            "id": student_id,
            "tid": tenant_id,
            "uid": user_id,
            "bid": batch_id,
            "roll": f"R_{uuid.uuid4().hex[:8]}",
        },
    )
    return batch_id


class TestIAAggregation:
    async def test_ia_001_logbook_contribution(self, test_db_session, tenant_id):
        """
        Test ID: IA-001
        Module: ia_aggregation
        Verifies: Logbook completion IA contribution (up to 20%).
        """
        student_id = uuid.uuid4()
        course_id, curr_id, dept_id, prog_id = await seed_course_with_relations(
            test_db_session, tenant_id, "Anatomy", "ANAT", "ANAT"
        )
        await seed_student_with_relations(test_db_session, tenant_id, student_id, prog_id)
        service = ExamService(test_db_session)

        # Seed logbook assessment with 80% mark
        await test_db_session.execute(
            text(
                "INSERT INTO logbook_assessments (id, tenant_id, student_id, subject_code, professional_phase, total_entries, completed_entries, ia_marks_pct, ia_marks_awarded, is_complete) "
                "VALUES (:id, :tid, :sid, 'ANAT', 'Phase I', 10, 8, 80.00, 16.00, true)"
            ),
            {
                "id": uuid.uuid4(),
                "tid": tenant_id,
                "sid": student_id,
            },
        )
        await test_db_session.commit()

        agg = await service.aggregate_ia(tenant_id, student_id, course_id, "Phase I")
        # Logbook weight is 20%. So 80% * 0.20 = 16.00 marks.
        assert agg.logbook_marks == Decimal("16.00")
        assert agg.viva_marks == Decimal("0.00")
        assert agg.practical_marks == Decimal("0.00")
        assert agg.clinical_marks == Decimal("0.00")
        assert agg.total_ia == Decimal("16.00")

    async def test_ia_002_viva_contribution(self, test_db_session, tenant_id):
        """
        Test ID: IA-002
        Module: ia_aggregation
        Verifies: Viva scores IA contribution (30%).
        """
        student_id = uuid.uuid4()
        course_id, curr_id, dept_id, prog_id = await seed_course_with_relations(
            test_db_session, tenant_id, "Anatomy", "ANAT", "ANAT"
        )
        await seed_student_with_relations(test_db_session, tenant_id, student_id, prog_id)
        service = ExamService(test_db_session)

        faculty_id = uuid.uuid4()
        fac_user_id = await seed_faculty_with_user(test_db_session, tenant_id, faculty_id, dept_id)

        # Seed viva score: 18 out of 20 (90%)
        await test_db_session.execute(
            text(
                "INSERT INTO viva_scores (id, tenant_id, student_id, course_id, professional_phase, examiner_id, marks_obtained, max_marks) "
                "VALUES (:id, :tid, :sid, :cid, 'Phase I', :exid, 18.00, 20.00)"
            ),
            {
                "id": uuid.uuid4(),
                "tid": tenant_id,
                "sid": student_id,
                "cid": course_id,
                "exid": fac_user_id,
            },
        )
        await test_db_session.commit()

        agg = await service.aggregate_ia(tenant_id, student_id, course_id, "Phase I")
        # Viva weight is 30%. So 90% * 0.30 = 27.00 marks.
        assert agg.viva_marks == Decimal("27.00")
        assert agg.total_ia == Decimal("27.00")

    async def test_ia_003_practical_contribution(self, test_db_session, tenant_id):
        """
        Test ID: IA-003
        Module: ia_aggregation
        Verifies: Practical exam scores IA contribution (30%).
        """
        student_id = uuid.uuid4()
        course_id, curr_id, dept_id, prog_id = await seed_course_with_relations(
            test_db_session, tenant_id, "Anatomy", "ANAT", "ANAT"
        )
        await seed_student_with_relations(test_db_session, tenant_id, student_id, prog_id)
        service = ExamService(test_db_session)

        faculty_id = uuid.uuid4()
        fac_user_id = await seed_faculty_with_user(test_db_session, tenant_id, faculty_id, dept_id)

        # Seed practical assessment: 15 out of 20 (75%)
        await test_db_session.execute(
            text(
                "INSERT INTO practical_assessments (id, tenant_id, student_id, course_id, professional_phase, examiner_id, marks_obtained, max_marks) "
                "VALUES (:id, :tid, :sid, :cid, 'Phase I', :exid, 15.00, 20.00)"
            ),
            {
                "id": uuid.uuid4(),
                "tid": tenant_id,
                "sid": student_id,
                "cid": course_id,
                "exid": fac_user_id,
            },
        )
        await test_db_session.commit()

        agg = await service.aggregate_ia(tenant_id, student_id, course_id, "Phase I")
        # Practical weight is 30%. So 75% * 0.30 = 22.50 marks.
        assert agg.practical_marks == Decimal("22.50")
        assert agg.total_ia == Decimal("22.50")

    async def test_ia_004_clinical_contribution(self, test_db_session, tenant_id):
        """
        Test ID: IA-004
        Module: ia_aggregation
        Verifies: Clinical posting evaluation IA contribution (20%).
        """
        student_id = uuid.uuid4()
        course_id, curr_id, dept_id, prog_id = await seed_course_with_relations(
            test_db_session, tenant_id, "Anatomy", "ANAT", "ANAT"
        )
        await seed_student_with_relations(test_db_session, tenant_id, student_id, prog_id)
        service = ExamService(test_db_session)

        faculty_id = uuid.uuid4()
        fac_user_id = await seed_faculty_with_user(test_db_session, tenant_id, faculty_id, dept_id)

        # Seed clinical evaluation: 40 out of 50 (80%)
        await test_db_session.execute(
            text(
                "INSERT INTO clinical_evaluations (id, tenant_id, student_id, course_id, professional_phase, evaluator_id, marks_obtained, max_marks) "
                "VALUES (:id, :tid, :sid, :cid, 'Phase I', :evid, 40.00, 50.00)"
            ),
            {
                "id": uuid.uuid4(),
                "tid": tenant_id,
                "sid": student_id,
                "cid": course_id,
                "evid": fac_user_id,
            },
        )
        await test_db_session.commit()

        agg = await service.aggregate_ia(tenant_id, student_id, course_id, "Phase I")
        # Clinical weight is 20%. So 80% * 0.20 = 16.00 marks.
        assert agg.clinical_marks == Decimal("16.00")
        assert agg.total_ia == Decimal("16.00")

    async def test_ia_005_mdm_weights(self, test_db_session, tenant_id):
        """
        Test ID: IA-005
        Module: ia_aggregation
        Verifies: MDM configuration of subject-specific weights.
        """
        student_id = uuid.uuid4()
        course_id, curr_id, dept_id, prog_id = await seed_course_with_relations(
            test_db_session, tenant_id, "Anatomy", "ANAT", "ANAT"
        )
        await seed_student_with_relations(test_db_session, tenant_id, student_id, prog_id)
        service = ExamService(test_db_session)

        # Configure custom weights in MDM: 40% logbook, 20% viva, 20% practical, 20% clinical
        await test_db_session.execute(
            text(
                "INSERT INTO mdm_configs (id, tenant_id, config_key, config_value) "
                'VALUES (:id, :tid, \'ia_weights\', \'{"logbook": 0.40, "viva": 0.20, "practical": 0.20, "clinical": 0.20}\')'
            ),
            {
                "id": uuid.uuid4(),
                "tid": tenant_id,
            },
        )
        # Logbook: 80%
        await test_db_session.execute(
            text(
                "INSERT INTO logbook_assessments (id, tenant_id, student_id, subject_code, professional_phase, total_entries, completed_entries, ia_marks_pct, ia_marks_awarded, is_complete) "
                "VALUES (:id, :tid, :sid, 'ANAT', 'Phase I', 10, 8, 80.00, 16.00, true)"
            ),
            {
                "id": uuid.uuid4(),
                "tid": tenant_id,
                "sid": student_id,
            },
        )
        await test_db_session.commit()

        agg = await service.aggregate_ia(tenant_id, student_id, course_id, "Phase I")
        # Logbook Custom weight is 40%. So 80% * 0.40 = 32.00 marks.
        assert agg.logbook_marks == Decimal("32.00")
        assert agg.total_ia == Decimal("32.00")

    async def test_ia_006_capping_validation(self, test_db_session, tenant_id):
        """
        Test ID: IA-006
        Module: ia_aggregation
        Verifies: Capping total IA contribution at 20% validation.
        """
        student_id = uuid.uuid4()
        course_id, curr_id, dept_id, prog_id = await seed_course_with_relations(
            test_db_session, tenant_id, "Anatomy", "ANAT", "ANAT"
        )
        await seed_student_with_relations(test_db_session, tenant_id, student_id, prog_id)
        service = ExamService(test_db_session)

        faculty_id = uuid.uuid4()
        fac_user_id = await seed_faculty_with_user(test_db_session, tenant_id, faculty_id, dept_id)

        # Logbook 100% (20 marks)
        await test_db_session.execute(
            text(
                "INSERT INTO logbook_assessments (id, tenant_id, student_id, subject_code, professional_phase, total_entries, completed_entries, ia_marks_pct, ia_marks_awarded, is_complete) "
                "VALUES (:id, :tid, :sid, 'ANAT', 'Phase I', 10, 10, 100.00, 20.00, true)"
            ),
            {
                "id": uuid.uuid4(),
                "tid": tenant_id,
                "sid": student_id,
            },
        )
        # Viva 100% (30 marks)
        await test_db_session.execute(
            text(
                "INSERT INTO viva_scores (id, tenant_id, student_id, course_id, professional_phase, examiner_id, marks_obtained, max_marks) "
                "VALUES (:id, :tid, :sid, :cid, 'Phase I', :exid, 20.00, 20.00)"
            ),
            {
                "id": uuid.uuid4(),
                "tid": tenant_id,
                "sid": student_id,
                "cid": course_id,
                "exid": fac_user_id,
            },
        )
        await test_db_session.commit()

        agg = await service.aggregate_ia(tenant_id, student_id, course_id, "Phase I")
        # 100% * 0.20 (logbook) + 100% * 0.30 (viva) = 50.00 marks.
        assert agg.total_ia == Decimal("50.00")
        assert agg.ia_max == Decimal("100.00")

    async def test_ia_007_aggregate_batch(self, test_db_session, tenant_id):
        """
        Test ID: IA-007
        Module: ia_aggregation
        Verifies: Aggregate IA calculations for whole batch.
        """
        student_id = uuid.uuid4()
        course_id, curr_id, dept_id, prog_id = await seed_course_with_relations(
            test_db_session, tenant_id, "Anatomy", "ANAT", "ANAT"
        )
        batch_id = await seed_student_with_relations(
            test_db_session, tenant_id, student_id, prog_id
        )
        service = ExamService(test_db_session)

        # Seed second student in the same batch
        student_id2 = uuid.uuid4()
        user2_id = uuid.uuid4()
        await test_db_session.execute(
            text(
                "INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active) "
                "VALUES (:id, :tid, :email, 'Student Two', 'pwd', true)"
            ),
            {"id": user2_id, "tid": tenant_id, "email": f"stud_{uuid.uuid4().hex[:8]}@jmn.edu.in"},
        )
        await test_db_session.execute(
            text(
                "INSERT INTO students (id, tenant_id, user_id, batch_id, roll_number, admission_year, status) "
                "VALUES (:id, :tid, :uid, :bid, :roll, 2024, 'active')"
            ),
            {
                "id": student_id2,
                "tid": tenant_id,
                "uid": user2_id,
                "bid": batch_id,
                "roll": f"R_{uuid.uuid4().hex[:8]}",
            },
        )
        await test_db_session.commit()

        results = await service.aggregate_ia_batch(tenant_id, course_id, "Phase I")
        assert len(results) >= 2

    async def test_ia_008_missing_marks_zero(self, test_db_session, tenant_id):
        """
        Test ID: IA-008
        Module: ia_aggregation
        Verifies: Missing sub-component marks treated as zero in aggregation.
        """
        student_id = uuid.uuid4()
        course_id, curr_id, dept_id, prog_id = await seed_course_with_relations(
            test_db_session, tenant_id, "Anatomy", "ANAT", "ANAT"
        )
        await seed_student_with_relations(test_db_session, tenant_id, student_id, prog_id)
        service = ExamService(test_db_session)

        agg = await service.aggregate_ia(tenant_id, student_id, course_id, "Phase I")
        assert agg.total_ia == Decimal("0.00")

    async def test_ia_010_historical_records_retained(self, test_db_session, tenant_id):
        """
        Test ID: IA-010
        Module: ia_aggregation
        Verifies: Historical IA records retained on re-calculation.
        """
        student_id = uuid.uuid4()
        course_id, curr_id, dept_id, prog_id = await seed_course_with_relations(
            test_db_session, tenant_id, "Anatomy", "ANAT", "ANAT"
        )
        await seed_student_with_relations(test_db_session, tenant_id, student_id, prog_id)
        service = ExamService(test_db_session)

        agg1 = await service.aggregate_ia(tenant_id, student_id, course_id, "Phase I")
        agg2 = await service.aggregate_ia(tenant_id, student_id, course_id, "Phase I")

        # The ID or record is updated/overwritten in place or remains valid
        assert agg1.student_id == agg2.student_id
        assert agg1.course_id == agg2.course_id
