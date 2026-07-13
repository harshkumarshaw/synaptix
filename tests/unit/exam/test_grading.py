"""
Test ID group: RES-001..006, EXM-010, RES-009
Module: exam_results
Phase: 3 R4.3 — Grade Calculation, Grace Marks, Workflow, Moderation
"""

from __future__ import annotations

import uuid
import pytest
from decimal import Decimal
from sqlalchemy import text

from app.services.exam_service import (
    ExamService,
    ExamServiceError,
    compute_grade,
    moderate_marks,
)
from app.models.exam import ExamEligibility

pytestmark = pytest.mark.anyio

# ---------------------------------------------------------------------------
# Seeding helpers (reusing the same unique-ID pattern from test_eligibility.py)
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def _seed_exam_base(db, tenant_id: uuid.UUID):
    """Create minimum viable exam setup matching real schema.

    Returns (student_id, examination_id)
    """
    suffix = uuid.uuid4().hex[:8]

    dept_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO departments (id, tenant_id, name, code) "
            "VALUES (:id, :tid, :name, :code) ON CONFLICT DO NOTHING"
        ),
        {"id": dept_id, "tid": tenant_id, "name": f"Dept {suffix}", "code": f"D{suffix[:6]}"},
    )

    prog_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO programs (id, tenant_id, name, code, type, duration_years) "
            "VALUES (:id, :tid, :name, :code, 'professional_phase', 5) ON CONFLICT DO NOTHING"
        ),
        {"id": prog_id, "tid": tenant_id, "name": f"MBBS {suffix}", "code": f"P{suffix[:6]}"},
    )

    curr_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO curricula (id, tenant_id, program_id, name, version_code) "
            "VALUES (:id, :tid, :pid, :name, :vcode) ON CONFLICT DO NOTHING"
        ),
        {
            "id": curr_id,
            "tid": tenant_id,
            "pid": prog_id,
            "name": f"Curr {suffix}",
            "vcode": f"2024_{suffix[:4]}",
        },
    )

    course_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO courses (id, tenant_id, curriculum_id, department_id, name, code, "
            "default_attendance_category, subject_code) "
            "VALUES (:id, :tid, :cid, :did, :name, :code, 'theory', 'ANAT') ON CONFLICT DO NOTHING"
        ),
        {
            "id": course_id,
            "tid": tenant_id,
            "cid": curr_id,
            "did": dept_id,
            "name": f"ANAT {suffix}",
            "code": f"ANAT_{suffix}",
        },
    )

    ay_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO academic_years (id, tenant_id, name, start_date, end_date, is_current) "
            "VALUES (:id, :tid, :name, '2026-06-01', '2027-05-31', true) ON CONFLICT DO NOTHING"
        ),
        {"id": ay_id, "tid": tenant_id, "name": f"AY{suffix}"},
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
            "name": f"Batch {suffix}",
            "code": f"MBBS_{suffix}",
        },
    )

    user_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active) "
            "VALUES (:id, :tid, :email, 'Test Student', 'pwd', true)"
        ),
        {"id": user_id, "tid": tenant_id, "email": f"stu_{suffix}@jmn.edu.in"},
    )

    student_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO students (id, tenant_id, user_id, batch_id, roll_number, admission_year, status) "
            "VALUES (:id, :tid, :uid, :bid, :rno, 2024, 'active')"
        ),
        {
            "id": student_id,
            "tid": tenant_id,
            "uid": user_id,
            "bid": batch_id,
            "rno": f"R{suffix}",
        },
    )

    exam_id = uuid.uuid4()
    await db.execute(
        text(
            "INSERT INTO examinations (id, tenant_id, curriculum_id, course_id, exam_type, "
            "exam_session, academic_year, exam_date, theory_max_marks, practical_max_marks, "
            "theory_pass_marks, practical_pass_marks, grace_marks_allowed, status) "
            "VALUES (:id, :tid, :cid, :coid, 'terminal', 'Winter', '2026-27', '2026-11-01', "
            "100, 50, 50, 25, 5, 'scheduled') ON CONFLICT DO NOTHING"
        ),
        {"id": exam_id, "tid": tenant_id, "cid": curr_id, "coid": course_id},
    )

    # Grant eligibility so submit_result can proceed
    await db.execute(
        text(
            "INSERT INTO exam_eligibility (tenant_id, student_id, examination_id, is_eligible) "
            "VALUES (:tid, :sid, :eid, true) "
            "ON CONFLICT (tenant_id, student_id, examination_id) DO UPDATE SET is_eligible = true"
        ),
        {"tid": tenant_id, "sid": student_id, "eid": exam_id},
    )
    await db.commit()
    return student_id, exam_id


# ---------------------------------------------------------------------------
# RES-001: Distinction (≥75%)
# ---------------------------------------------------------------------------


class TestExamGrading:
    async def test_res_001_distinction(self, test_db_session):
        """
        Test ID: RES-001
        Module: exam_results
        Verifies: Grading: Distinction (>=75%) calculation.
        """
        tenant_id = TENANT_ID
        student_id, exam_id = await _seed_exam_base(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        # theory_max=100, theory 75/100 = 75% → distinction
        # practical_max=50, practical 40/50 = 80% → distinction
        result = await service.submit_result(
            tenant_id,
            student_id,
            exam_id,
            theory_marks=Decimal("75"),
            practical_marks=Decimal("40"),
        )
        assert result.theory_grade == "distinction"
        assert result.practical_grade == "distinction"
        assert result.overall_grade == "distinction"

    async def test_res_002_pass(self, test_db_session):
        """
        Test ID: RES-002
        Module: exam_results
        Verifies: Grading: Pass (50%-74%) calculation.
        """
        tenant_id = TENANT_ID
        student_id, exam_id = await _seed_exam_base(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        # theory 60/100 = 60% → pass; practical 30/50 = 60% → pass
        result = await service.submit_result(
            tenant_id,
            student_id,
            exam_id,
            theory_marks=Decimal("60"),
            practical_marks=Decimal("30"),
        )
        assert result.theory_grade == "pass"
        assert result.practical_grade == "pass"
        assert result.overall_grade == "pass"

    async def test_res_003_fail(self, test_db_session):
        """
        Test ID: RES-003
        Module: exam_results
        Verifies: Grading: Fail (<50%) calculation.
        """
        tenant_id = TENANT_ID
        student_id, exam_id = await _seed_exam_base(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        # theory 40/100 = 40% → fail (shortfall=10 > grace_limit=5 → no grace)
        result = await service.submit_result(
            tenant_id,
            student_id,
            exam_id,
            theory_marks=Decimal("40"),
            practical_marks=Decimal("30"),
        )
        assert result.theory_grade == "fail"
        assert result.overall_grade == "fail"

    async def test_res_004_independent_pass(self, test_db_session):
        """
        Test ID: RES-004
        Module: exam_results
        Verifies: Theory and practical parts evaluated and passed independently.
        Student who passes theory but fails practical must overall fail.
        """
        tenant_id = TENANT_ID
        student_id, exam_id = await _seed_exam_base(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        # theory 70/100 = 70% → pass, practical 10/50 = 20% → fail
        result = await service.submit_result(
            tenant_id,
            student_id,
            exam_id,
            theory_marks=Decimal("70"),
            practical_marks=Decimal("10"),
        )
        assert result.theory_grade == "pass"
        assert result.practical_grade == "fail"
        assert result.overall_grade == "fail", "Must fail overall if any component fails"

    async def test_exm_010_grace_marks(self, test_db_session):
        """
        Test ID: EXM-010
        Module: examination_management
        Verifies: Grace marks policy correctly applied.
        Student who narrowly fails theory (shortfall ≤5) gets grace marks
        and passes. Grace not applicable in supplementary exams.
        """
        tenant_id = TENANT_ID
        student_id, exam_id = await _seed_exam_base(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        # theory_pass_marks=50, theory=47 → shortfall=3 ≤ grace_limit=5 → grace=3 applied
        result = await service.submit_result(
            tenant_id,
            student_id,
            exam_id,
            theory_marks=Decimal("47"),
            practical_marks=Decimal("30"),
        )
        assert result.grace_marks_applied == 3
        assert result.theory_marks == Decimal("50")  # 47 + 3
        assert result.theory_grade == "pass"

        # Verify pure helpers (unit level)
        assert compute_grade(Decimal("75"), Decimal("100")) == "distinction"
        assert compute_grade(Decimal("60"), Decimal("100")) == "pass"
        assert compute_grade(Decimal("40"), Decimal("100")) == "fail"


# ---------------------------------------------------------------------------
# RES-005/006/009: Moderation
# ---------------------------------------------------------------------------


class TestExamModeration:
    async def test_res_005_two_examiners(self, test_db_session):
        """
        Test ID: RES-005
        Module: exam_results
        Verifies: Multi-examiner moderation: average of two if <=15% diff.
        """
        tenant_id = TENANT_ID
        student_id, exam_id = await _seed_exam_base(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        result = await service.submit_result(
            tenant_id,
            student_id,
            exam_id,
            theory_marks=Decimal("60"),
            practical_marks=Decimal("30"),
        )

        # 60 vs 65 on max=100 → diff=5 ≤ 15 → average_two
        mod = await service.record_moderation(
            tenant_id=tenant_id,
            exam_result_id=result.id,
            examiner_1_marks=Decimal("60"),
            examiner_2_marks=Decimal("65"),
            max_marks=Decimal("100"),
        )
        assert mod.moderation_method == "average_two"
        assert mod.final_marks == Decimal("62.50")

    async def test_res_006_three_examiners(self, test_db_session):
        """
        Test ID: RES-006
        Module: exam_results
        Verifies: Multi-examiner moderation: third examiner if >15% diff.
        """
        tenant_id = TENANT_ID
        student_id, exam_id = await _seed_exam_base(test_db_session, tenant_id)
        service = ExamService(test_db_session)

        result = await service.submit_result(
            tenant_id,
            student_id,
            exam_id,
            theory_marks=Decimal("60"),
            practical_marks=Decimal("30"),
        )

        # 40 vs 70 on max=100 → diff=30 > 15 → third examiner mandatory
        with pytest.raises(ExamServiceError) as exc_info:
            await service.record_moderation(
                tenant_id=tenant_id,
                exam_result_id=result.id,
                examiner_1_marks=Decimal("40"),
                examiner_2_marks=Decimal("70"),
                max_marks=Decimal("100"),
                # no examiner_3_marks → should raise
            )
        assert "Third examiner mandatory" in str(exc_info.value)

        # With third examiner: closest pair of (40, 70, 60) → (40,60) diff=20, (60,70) diff=10
        # closest: 60 & 70 → avg 65
        mod = await service.record_moderation(
            tenant_id=tenant_id,
            exam_result_id=result.id,
            examiner_1_marks=Decimal("40"),
            examiner_2_marks=Decimal("70"),
            max_marks=Decimal("100"),
            examiner_3_marks=Decimal("60"),
        )
        assert mod.moderation_method == "closest_pair_three"
        assert mod.final_marks == Decimal("65.00")

    async def test_res_009_grace_marks_limits(self, test_db_session):
        """
        Test ID: RES-009
        Module: exam_results
        Verifies: Grace marks policy: max 5 marks applied; no grace in supplementary.
        """
        # --- Unit: pure helper ---
        assert compute_grade(Decimal("75"), Decimal("100")) == "distinction"
        assert compute_grade(Decimal("50"), Decimal("100")) == "pass"
        assert compute_grade(Decimal("49"), Decimal("100")) == "fail"

        # --- moderate_marks helper (pure, no DB needed) ---
        final, method = moderate_marks(Decimal("80"), Decimal("85"), Decimal("100"))
        assert method == "average_two"
        assert final == Decimal("82.50")

        # --- Integration: grace not applied in supplementary ---
        tenant_id = TENANT_ID
        student_id, exam_id = await _seed_exam_base(test_db_session, tenant_id)

        # Upgrade the exam to supplementary
        await test_db_session.execute(
            text("UPDATE examinations SET exam_type = 'supplementary' WHERE id = :eid"),
            {"eid": exam_id},
        )
        await test_db_session.commit()

        service = ExamService(test_db_session)
        # theory 47/100 → normally would qualify for grace, but not in supplementary
        result = await service.submit_result(
            tenant_id,
            student_id,
            exam_id,
            theory_marks=Decimal("47"),
            practical_marks=Decimal("30"),
        )
        assert result.grace_marks_applied == 0, "No grace marks in supplementary (ADR-041)"
        assert result.theory_marks == Decimal("47")
        assert result.theory_grade == "fail"
