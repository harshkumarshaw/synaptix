import pytest
import uuid
import datetime
from decimal import Decimal
from sqlalchemy import text
from app.services.exam_service import ExamService, ExamServiceError
from app.models.exam import ExamEligibility

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


async def seed_eligibility_base(db, tenant_id, student_id):
    course_id, curr_id, dept_id, prog_id = await seed_course_with_relations(
        db, tenant_id, "Anatomy", "ANAT", "ANAT"
    )
    await seed_student_with_relations(db, tenant_id, student_id, prog_id)

    # Examination
    exam_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO examinations (id, tenant_id, curriculum_id, course_id, exam_type, exam_session, academic_year, exam_date, theory_max_marks, practical_max_marks, theory_pass_marks, practical_pass_marks, status) "
            "VALUES (:id, :tid, :cid, :coid, 'professional', 'Dec 2026', '2026-2027', '2026-12-15', 100, 100, 50, 50, 'scheduled')"
        ),
        {
            "id": exam_id,
            "tid": tenant_id,
            "cid": curr_id,
            "coid": course_id,
        },
    )
    await db.commit()
    return course_id, exam_id, curr_id, dept_id, prog_id


class TestExamEligibility:
    async def test_elig_001_attendance_requirements(self, test_db_session, tenant_id):
        """
        Test ID: ELIG-001
        Module: exam_eligibility
        Verifies: Eligibility check: attendance requirements met.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Seed attendance summaries: 76% theory, 81% practical -> meets threshold
        await test_db_session.execute(
            text(
                "INSERT INTO attendance_summary (tenant_id, student_id, course_id, professional_phase, attendance_category, sessions_conducted, sessions_present) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 'theory', 100, 76), (:tid, :sid, :cid, 'Phase I', 'practical', 100, 81)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        # Logbook: complete
        await test_db_session.execute(
            text(
                "INSERT INTO logbook_assessments (id, tenant_id, student_id, subject_code, professional_phase, total_entries, completed_entries, ia_marks_pct, ia_marks_awarded, is_complete) "
                "VALUES (:id, :tid, :sid, 'ANAT', 'Phase I', 10, 8, 80.00, 16.00, true)"
            ),
            {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id},
        )
        # IA Aggregation: meets 50% threshold
        await test_db_session.execute(
            text(
                "INSERT INTO ia_aggregation (tenant_id, student_id, course_id, professional_phase, total_ia, ia_max, is_eligible) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 55.00, 100.00, true)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        await test_db_session.commit()

        elig = await service.check_student_eligibility(tenant_id, student_id, exam_id)
        assert elig.is_eligible is True
        assert elig.blocking_reasons is None

    async def test_elig_002_certified_logbooks(self, test_db_session, tenant_id):
        """
        Test ID: ELIG-002
        Module: exam_eligibility
        Verifies: Eligibility check: certified logbooks.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Seed attendance summaries (valid)
        await test_db_session.execute(
            text(
                "INSERT INTO attendance_summary (tenant_id, student_id, course_id, professional_phase, attendance_category, sessions_conducted, sessions_present) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 'theory', 100, 76), (:tid, :sid, :cid, 'Phase I', 'practical', 100, 81)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        # Logbook: incomplete
        await test_db_session.execute(
            text(
                "INSERT INTO logbook_assessments (id, tenant_id, student_id, subject_code, professional_phase, total_entries, completed_entries, ia_marks_pct, ia_marks_awarded, is_complete) "
                "VALUES (:id, :tid, :sid, 'ANAT', 'Phase I', 10, 8, 80.00, 16.00, false)"
            ),
            {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id},
        )
        # IA Aggregation
        await test_db_session.execute(
            text(
                "INSERT INTO ia_aggregation (tenant_id, student_id, course_id, professional_phase, total_ia, ia_max, is_eligible) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 55.00, 100.00, true)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        await test_db_session.commit()

        elig = await service.check_student_eligibility(tenant_id, student_id, exam_id)
        assert elig.is_eligible is False
        assert any(r["code"] == "logbook_incomplete" for r in elig.blocking_reasons)

    async def test_elig_003_aggregate_ia_marks(self, test_db_session, tenant_id):
        """
        Test ID: ELIG-003
        Module: exam_eligibility
        Verifies: Eligibility check: aggregate IA marks >= 50%.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Seed attendance summaries (valid)
        await test_db_session.execute(
            text(
                "INSERT INTO attendance_summary (tenant_id, student_id, course_id, professional_phase, attendance_category, sessions_conducted, sessions_present) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 'theory', 100, 76), (:tid, :sid, :cid, 'Phase I', 'practical', 100, 81)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        # Logbook: complete
        await test_db_session.execute(
            text(
                "INSERT INTO logbook_assessments (id, tenant_id, student_id, subject_code, professional_phase, total_entries, completed_entries, ia_marks_pct, ia_marks_awarded, is_complete) "
                "VALUES (:id, :tid, :sid, 'ANAT', 'Phase I', 10, 8, 80.00, 16.00, true)"
            ),
            {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id},
        )
        # IA Aggregation: less than 50%
        await test_db_session.execute(
            text(
                "INSERT INTO ia_aggregation (tenant_id, student_id, course_id, professional_phase, total_ia, ia_max, is_eligible) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 45.00, 100.00, false)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        await test_db_session.commit()

        elig = await service.check_student_eligibility(tenant_id, student_id, exam_id)
        assert elig.is_eligible is False
        assert any(r["code"] == "ia_shortfall" for r in elig.blocking_reasons)

    async def test_elig_004_disciplinary_suspension(self, test_db_session, tenant_id):
        """
        Test ID: ELIG-004
        Module: exam_eligibility
        Verifies: Eligibility check: no active disciplinary suspension.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Set student status to suspended
        await test_db_session.execute(
            text("UPDATE students SET status = 'suspended' WHERE id = :sid"), {"sid": student_id}
        )
        # Seed attendance summaries (valid)
        await test_db_session.execute(
            text(
                "INSERT INTO attendance_summary (tenant_id, student_id, course_id, professional_phase, attendance_category, sessions_conducted, sessions_present) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 'theory', 100, 76), (:tid, :sid, :cid, 'Phase I', 'practical', 100, 81)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        # Logbook: complete
        await test_db_session.execute(
            text(
                "INSERT INTO logbook_assessments (id, tenant_id, student_id, subject_code, professional_phase, total_entries, completed_entries, ia_marks_pct, ia_marks_awarded, is_complete) "
                "VALUES (:id, :tid, :sid, 'ANAT', 'Phase I', 10, 8, 80.00, 16.00, true)"
            ),
            {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id},
        )
        # IA Aggregation
        await test_db_session.execute(
            text(
                "INSERT INTO ia_aggregation (tenant_id, student_id, course_id, professional_phase, total_ia, ia_max, is_eligible) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 55.00, 100.00, true)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        await test_db_session.commit()

        elig = await service.check_student_eligibility(tenant_id, student_id, exam_id)
        assert elig.is_eligible is False
        assert any(r["code"] == "disciplinary_suspension" for r in elig.blocking_reasons)

    async def test_elig_005_prerequisite_courses(self, test_db_session, tenant_id):
        """
        Test ID: ELIG-005
        Module: exam_eligibility
        Verifies: Eligibility check: prerequisite courses passed.
        """
        student_id = uuid.uuid4()
        # Seed PATH course
        path_course_id, path_curr_id, path_dept_id, prog_id = await seed_course_with_relations(
            test_db_session, tenant_id, "Pathology", "PATH", "PATH"
        )
        # Seed ANAT course (which is prerequisite of PATH) under same curriculum
        anat_course_id = uuid.uuid4()
        await test_db_session.execute(
            text(
                "INSERT INTO courses (id, tenant_id, curriculum_id, department_id, name, code, default_attendance_category, subject_code) "
                "VALUES (:id, :tid, :cid, :did, 'Anatomy', 'ANAT', 'theory', 'ANAT')"
            ),
            {"id": anat_course_id, "tid": tenant_id, "cid": path_curr_id, "did": path_dept_id},
        )
        # Seed student
        await seed_student_with_relations(test_db_session, tenant_id, student_id, prog_id)

        # Seed Examination for PATH
        exam_id = uuid.uuid4()
        await test_db_session.execute(
            text(
                "INSERT INTO examinations (id, tenant_id, curriculum_id, course_id, exam_type, exam_session, academic_year, exam_date, theory_max_marks, practical_max_marks, theory_pass_marks, practical_pass_marks, status) "
                "VALUES (:id, :tid, :cid, :coid, 'professional', 'Dec 2026', '2026-2027', '2026-12-15', 100, 100, 50, 50, 'scheduled')"
            ),
            {"id": exam_id, "tid": tenant_id, "cid": path_curr_id, "coid": path_course_id},
        )
        # Seed attendance for PATH (valid)
        await test_db_session.execute(
            text(
                "INSERT INTO attendance_summary (tenant_id, student_id, course_id, professional_phase, attendance_category, sessions_conducted, sessions_present) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 'theory', 100, 76), (:tid, :sid, :cid, 'Phase I', 'practical', 100, 81)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": path_course_id},
        )
        # Logbook for PATH: complete
        await test_db_session.execute(
            text(
                "INSERT INTO logbook_assessments (id, tenant_id, student_id, subject_code, professional_phase, total_entries, completed_entries, ia_marks_pct, ia_marks_awarded, is_complete) "
                "VALUES (:id, :tid, :sid, 'PATH', 'Phase I', 10, 8, 80.00, 16.00, true)"
            ),
            {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id},
        )
        # IA Aggregation for PATH: meets threshold
        await test_db_session.execute(
            text(
                "INSERT INTO ia_aggregation (tenant_id, student_id, course_id, professional_phase, total_ia, ia_max, is_eligible) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 55.00, 100.00, true)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": path_course_id},
        )
        await test_db_session.commit()

        service = ExamService(test_db_session)
        # ANAT prerequisite is missing!
        elig = await service.check_student_eligibility(tenant_id, student_id, exam_id)
        assert elig.is_eligible is False
        assert any(r["code"] == "prerequisite_missing" for r in elig.blocking_reasons)

        # Seed passed ANAT exam result
        anat_exam_id = uuid.uuid4()
        await test_db_session.execute(
            text(
                "INSERT INTO examinations (id, tenant_id, curriculum_id, course_id, exam_type, exam_session, academic_year, exam_date, theory_max_marks, practical_max_marks, theory_pass_marks, practical_pass_marks, status) "
                "VALUES (:id, :tid, :cid, :coid, 'professional', 'Dec 2026', '2026-2027', '2026-12-15', 100, 100, 50, 50, 'scheduled')"
            ),
            {"id": anat_exam_id, "tid": tenant_id, "cid": path_curr_id, "coid": anat_course_id},
        )
        await test_db_session.execute(
            text(
                "INSERT INTO exam_results (id, tenant_id, student_id, examination_id, overall_grade, status) "
                "VALUES (:id, :tid, :sid, :exid, 'pass', 'published')"
            ),
            {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id, "exid": anat_exam_id},
        )
        await test_db_session.commit()

        # Prerequisite check should now pass!
        elig2 = await service.check_student_eligibility(tenant_id, student_id, exam_id)
        assert not any(r["code"] == "prerequisite_missing" for r in (elig2.blocking_reasons or []))

    async def test_elig_006_blocking_reasons(self, test_db_session, tenant_id):
        """
        Test ID: ELIG-006
        Module: exam_eligibility
        Verifies: Eligibility returns detailed blocking reasons on failure.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # No attendance seeded -> fail
        elig = await service.check_student_eligibility(tenant_id, student_id, exam_id)
        assert elig.is_eligible is False
        assert len(elig.blocking_reasons) > 0

    async def test_elig_007_batch_run(self, test_db_session, tenant_id):
        """
        Test ID: ELIG-007
        Module: exam_eligibility
        Verifies: Eligibility batch run returns list of eligible student IDs.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Seed second student (ineligible)
        student_id2 = uuid.uuid4()
        user2_id = uuid.uuid4()
        # Find batch_id seeded
        res_batch = await test_db_session.execute(
            text("SELECT batch_id FROM students WHERE id = :sid"), {"sid": student_id}
        )
        batch_id = res_batch.scalars().first()

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
        # Seed attendance summaries for student 1 (eligible)
        await test_db_session.execute(
            text(
                "INSERT INTO attendance_summary (tenant_id, student_id, course_id, professional_phase, attendance_category, sessions_conducted, sessions_present) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 'theory', 100, 76), (:tid, :sid, :cid, 'Phase I', 'practical', 100, 81)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        # Logbook for student 1
        await test_db_session.execute(
            text(
                "INSERT INTO logbook_assessments (id, tenant_id, student_id, subject_code, professional_phase, total_entries, completed_entries, ia_marks_pct, ia_marks_awarded, is_complete) "
                "VALUES (:id, :tid, :sid, 'ANAT', 'Phase I', 10, 8, 80.00, 16.00, true)"
            ),
            {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id},
        )
        # IA Aggregation for student 1
        await test_db_session.execute(
            text(
                "INSERT INTO ia_aggregation (tenant_id, student_id, course_id, professional_phase, total_ia, ia_max, is_eligible) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 55.00, 100.00, true)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        await test_db_session.commit()

        eligible_ids = await service.run_batch_eligibility(tenant_id, exam_id)
        assert student_id in eligible_ids
        assert student_id2 not in eligible_ids

    async def test_elig_008_principal_override(self, test_db_session, tenant_id):
        """
        Test ID: ELIG-008
        Module: exam_eligibility
        Verifies: Principal overrides exam eligibility with audit log.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Ineligible initially
        elig = await service.check_student_eligibility(tenant_id, student_id, exam_id)
        assert elig.is_eligible is False

        # Override
        actor_id = uuid.uuid4()
        elig_overridden = await service.override_eligibility(
            tenant_id=tenant_id,
            student_id=student_id,
            examination_id=exam_id,
            role="principal",
            reason="Dean exemption granted for medical reasons",
            actor_user_id=actor_id,
        )
        assert elig_overridden.is_eligible is True

    async def test_elig_009_dean_override(self, test_db_session, tenant_id):
        """
        Test ID: ELIG-009
        Module: exam_eligibility
        Verifies: Dean overrides exam eligibility with audit log.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Override
        actor_id = uuid.uuid4()
        elig_overridden = await service.override_eligibility(
            tenant_id=tenant_id,
            student_id=student_id,
            examination_id=exam_id,
            role="dean",
            reason="Exemption approved",
            actor_user_id=actor_id,
        )
        assert elig_overridden.is_eligible is True

    async def test_elig_010_cross_tenant_isolation(self, test_db_session, tenant_id):
        """
        Test ID: ELIG-010
        Module: exam_eligibility
        Verifies: Cross-tenant student eligibility isolation.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Seed other tenant
        other_tenant_id = uuid.uuid4()
        await test_db_session.execute(
            text(
                "INSERT INTO tenants (id, name, code, institution_type, regulatory_body, is_active) "
                "VALUES (:id, :name, :code, 'medical', 'NMC', true)"
            ),
            {
                "id": other_tenant_id,
                "name": f"Tenant_{uuid.uuid4().hex[:6]}",
                "code": f"T_{uuid.uuid4().hex[:4]}",
            },
        )
        await test_db_session.commit()

        # Query other tenant examination (should fail with examination not found or reject)
        with pytest.raises(ExamServiceError):
            await service.check_student_eligibility(other_tenant_id, student_id, exam_id)

    async def test_exm_002_generate_hall_tickets(self, test_db_session, tenant_id):
        """
        Test ID: EXM-002
        Module: examination_management
        Verifies: Generate hall tickets for eligible students.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Seed attendance summaries (valid)
        await test_db_session.execute(
            text(
                "INSERT INTO attendance_summary (tenant_id, student_id, course_id, professional_phase, attendance_category, sessions_conducted, sessions_present) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 'theory', 100, 76), (:tid, :sid, :cid, 'Phase I', 'practical', 100, 81)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        # Logbook: complete
        await test_db_session.execute(
            text(
                "INSERT INTO logbook_assessments (id, tenant_id, student_id, subject_code, professional_phase, total_entries, completed_entries, ia_marks_pct, ia_marks_awarded, is_complete) "
                "VALUES (:id, :tid, :sid, 'ANAT', 'Phase I', 10, 8, 80.00, 16.00, true)"
            ),
            {"id": uuid.uuid4(), "tid": tenant_id, "sid": student_id},
        )
        # IA Aggregation
        await test_db_session.execute(
            text(
                "INSERT INTO ia_aggregation (tenant_id, student_id, course_id, professional_phase, total_ia, ia_max, is_eligible) "
                "VALUES (:tid, :sid, :cid, 'Phase I', 55.00, 100.00, true)"
            ),
            {"tid": tenant_id, "sid": student_id, "cid": course_id},
        )
        await test_db_session.commit()

        ticket = await service.generate_hall_ticket(tenant_id, student_id, exam_id)
        assert ticket["status"] == "generated"

    async def test_exm_003_hall_ticket_not_generated(self, test_db_session, tenant_id):
        """
        Test ID: EXM-003
        Module: examination_management
        Verifies: Hall ticket NOT generated for ineligible student.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Ineligible
        with pytest.raises(ExamServiceError):
            await service.generate_hall_ticket(tenant_id, student_id, exam_id)

    async def test_exm_004_principal_exemption_flow(self, test_db_session, tenant_id):
        """
        Test ID: EXM-004
        Module: examination_management
        Verifies: Principal exemption flow: ineligible student gets hall ticket with audit log.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        # Override
        actor_id = uuid.uuid4()
        await service.override_eligibility(
            tenant_id=tenant_id,
            student_id=student_id,
            examination_id=exam_id,
            role="principal",
            reason="Exemption approved",
            actor_user_id=actor_id,
        )

        ticket = await service.generate_hall_ticket(tenant_id, student_id, exam_id)
        assert ticket["status"] == "generated"

    async def test_exm_008_ospe_marks_aggregation(self, test_db_session, tenant_id):
        """
        Test ID: EXM-008
        Module: examination_management
        Verifies: OSPE station-level marks correctly aggregated.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        faculty_id = uuid.uuid4()
        fac_user_id = await seed_faculty_with_user(test_db_session, tenant_id, faculty_id, dept_id)

        # Seed practical assessment station 1
        await test_db_session.execute(
            text(
                "INSERT INTO practical_assessments (id, tenant_id, student_id, course_id, professional_phase, examiner_id, marks_obtained, max_marks) "
                "VALUES (:id, :tid, :sid, :cid, 'Phase I', :exid, 10.00, 20.00)"
            ),
            {
                "id": uuid.uuid4(),
                "tid": tenant_id,
                "sid": student_id,
                "cid": course_id,
                "exid": fac_user_id,
            },
        )
        # Seed practical assessment station 2
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

        total = await service.aggregate_station_marks(tenant_id, student_id, course_id)
        assert total == Decimal("25.00")

    async def test_exm_009_osce_marks_aggregation(self, test_db_session, tenant_id):
        """
        Test ID: EXM-009
        Module: examination_management
        Verifies: OSCE station-level marks correctly aggregated.
        """
        student_id = uuid.uuid4()
        course_id, exam_id, curr_id, dept_id, prog_id = await seed_eligibility_base(
            test_db_session, tenant_id, student_id
        )
        service = ExamService(test_db_session)

        faculty_id = uuid.uuid4()
        fac_user_id = await seed_faculty_with_user(test_db_session, tenant_id, faculty_id, dept_id)

        # Seed practical assessments (acting as OSCE stations)
        await test_db_session.execute(
            text(
                "INSERT INTO practical_assessments (id, tenant_id, student_id, course_id, professional_phase, examiner_id, marks_obtained, max_marks) "
                "VALUES (:id, :tid, :sid, :cid, 'Phase I', :exid, 8.50, 10.00)"
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

        total = await service.aggregate_station_marks(tenant_id, student_id, course_id)
        assert total == Decimal("8.50")
