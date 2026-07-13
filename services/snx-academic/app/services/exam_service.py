from __future__ import annotations

import base64
import hashlib
import io
import uuid
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceSummary
from app.models.course import Course
from app.models.exam import (
    ClinicalEvaluation,
    ExamEligibility,
    Examination,
    ExamModeration,
    ExamResult,
    ExamSchedule,
    IAAggregation,
    MarkSheet,
    PracticalAssessment,
    VivaScore,
)
from app.models.stubs import DigitalAsset, LogbookAssessment, MdmConfig, Student
from app.services.audit_logger import write_audit_log
from packages.shared.db.session import get_db
from packages.shared.errors import SynaptixError
from packages.shared.logging import get_logger

logger = get_logger(__name__)


class ExamServiceError(SynaptixError):
    """Exception raised for errors in the ExamService."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        self.code = f"SNX-EXM-{code}"
        super().__init__(message, details)


class ExamService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
        self.db = db

    async def create_examination(
        self,
        tenant_id: uuid.UUID,
        curriculum_id: uuid.UUID,
        course_id: uuid.UUID,
        exam_type: str,
        exam_session: str,
        academic_year: str,
        exam_date: date,
        theory_max_marks: int,
        practical_max_marks: int,
        theory_pass_marks: int,
        practical_pass_marks: int,
        grace_marks_allowed: int = 5,
        status: str = "scheduled",
        actor_user_id: uuid.UUID | None = None,
    ) -> Examination:
        # Create Examination record
        exam = Examination(
            tenant_id=tenant_id,
            curriculum_id=curriculum_id,
            course_id=course_id,
            exam_type=exam_type,
            exam_session=exam_session,
            academic_year=academic_year,
            exam_date=exam_date,
            theory_max_marks=theory_max_marks,
            practical_max_marks=practical_max_marks,
            theory_pass_marks=theory_pass_marks,
            practical_pass_marks=practical_pass_marks,
            grace_marks_allowed=grace_marks_allowed,
            status=status,
        )
        self.db.add(exam)
        await self.db.flush()

        await write_audit_log(
            self.db,
            tenant_id,
            actor_user_id,
            "CREATE",
            "examinations",
            exam.id,
            new_values={
                "curriculum_id": str(curriculum_id),
                "course_id": str(course_id),
                "exam_type": exam_type,
                "exam_session": exam_session,
                "academic_year": academic_year,
            },
        )
        return exam

    async def create_exam_schedule(
        self,
        tenant_id: uuid.UUID,
        examination_id: uuid.UUID,
        room_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        invigilator_id: uuid.UUID,
        actor_user_id: uuid.UUID | None = None,
    ) -> ExamSchedule:  # noqa: PLR0915
        # Ensure exam exists
        exam = await self.db.get(Examination, examination_id)
        if not exam:
            raise ExamServiceError("001", "Examination not found")

        # 1. Room Availability Check
        room_clash_stmt = select(ExamSchedule).where(
            ExamSchedule.tenant_id == tenant_id,
            ExamSchedule.room_id == room_id,
            ExamSchedule.start_time < end_time,
            ExamSchedule.end_time > start_time,
            ExamSchedule.deleted_at.is_(None),
        )
        room_clash_res = await self.db.execute(room_clash_stmt)
        if room_clash_res.scalars().first():
            raise ExamServiceError("011", "Room is already booked for another exam at this time")

        # 2. Invigilator Clash Check
        inv_clash_stmt = select(ExamSchedule).where(
            ExamSchedule.tenant_id == tenant_id,
            ExamSchedule.invigilator_id == invigilator_id,
            ExamSchedule.start_time < end_time,
            ExamSchedule.end_time > start_time,
            ExamSchedule.deleted_at.is_(None),
        )
        inv_clash_res = await self.db.execute(inv_clash_stmt)
        if inv_clash_res.scalars().first():
            raise ExamServiceError(
                "012", "Invigilator is already assigned to another exam at this time"
            )

        # 3. Student / Curriculum Clash Check
        # Overlapping exams in the same curriculum (same batch of students)
        stud_clash_stmt = (
            select(ExamSchedule)
            .join(Examination, Examination.id == ExamSchedule.examination_id)
            .where(
                ExamSchedule.tenant_id == tenant_id,
                Examination.curriculum_id == exam.curriculum_id,
                ExamSchedule.start_time < end_time,
                ExamSchedule.end_time > start_time,
                ExamSchedule.deleted_at.is_(None),
            )
        )
        stud_clash_res = await self.db.execute(stud_clash_stmt)
        if stud_clash_res.scalars().first():
            raise ExamServiceError(
                "013", "Student group is already scheduled for another exam at this time"
            )

        # 4. Theory 1-day Gap Check (consecutive days constraint for theory exams)
        if exam.exam_type in ("professional", "terminal"):
            theory_gap_stmt = (
                select(ExamSchedule)
                .join(Examination, Examination.id == ExamSchedule.examination_id)
                .where(
                    ExamSchedule.tenant_id == tenant_id,
                    Examination.curriculum_id == exam.curriculum_id,
                    Examination.exam_type.in_(["professional", "terminal"]),
                    ExamSchedule.deleted_at.is_(None),
                )
            )
            theory_gap_res = await self.db.execute(theory_gap_stmt)
            for other_schedule in theory_gap_res.scalars().all():
                day_diff = abs((other_schedule.start_time.date() - start_time.date()).days)
                if day_diff < 2:  # Needs at least 1 day in between, so difference must be >= 2 days
                    raise ExamServiceError(
                        "014", "Theory exams must have at least a 1-day gap between them"
                    )

        # Create schedule
        schedule = ExamSchedule(
            tenant_id=tenant_id,
            examination_id=examination_id,
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            invigilator_id=invigilator_id,
        )
        self.db.add(schedule)
        await self.db.flush()

        await write_audit_log(
            self.db,
            tenant_id,
            actor_user_id,
            "CREATE",
            "exam_schedules",
            schedule.id,
            new_values={
                "examination_id": str(examination_id),
                "room_id": str(room_id),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "invigilator_id": str(invigilator_id),
            },
        )
        return schedule

    async def aggregate_ia(  # noqa: PLR0915
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        course_id: uuid.UUID,
        professional_phase: str,
        actor_user_id: uuid.UUID | None = None,
    ) -> IAAggregation:  # noqa: PLR0915
        # Retrieve Course code
        course = await self.db.get(Course, course_id)
        if not course:
            raise ExamServiceError("002", "Course not found")

        # 1. Fetch Logbook assessment (marks pct)
        logbook_stmt = select(LogbookAssessment).where(
            LogbookAssessment.tenant_id == tenant_id,
            LogbookAssessment.student_id == student_id,
            LogbookAssessment.subject_code == course.subject_code,
            LogbookAssessment.professional_phase == professional_phase,
        )
        logbook_res = await self.db.execute(logbook_stmt)
        logbook_ass = logbook_res.scalars().first()
        logbook_pct = logbook_ass.ia_marks_pct if logbook_ass else Decimal("0.00")

        # 2. Fetch Viva scores
        viva_stmt = select(VivaScore).where(
            VivaScore.tenant_id == tenant_id,
            VivaScore.student_id == student_id,
            VivaScore.course_id == course_id,
            VivaScore.professional_phase == professional_phase,
            VivaScore.deleted_at.is_(None),
        )
        viva_res = await self.db.execute(viva_stmt)
        viva_scores = viva_res.scalars().all()
        if viva_scores:
            viva_pct = Decimal(
                sum(v.marks_obtained for v in viva_scores)
                / sum(v.max_marks for v in viva_scores)
                * 100
            )
        else:
            viva_pct = Decimal("0.00")

        # 3. Fetch Practical assessments
        pract_stmt = select(PracticalAssessment).where(
            PracticalAssessment.tenant_id == tenant_id,
            PracticalAssessment.student_id == student_id,
            PracticalAssessment.course_id == course_id,
            PracticalAssessment.professional_phase == professional_phase,
            PracticalAssessment.deleted_at.is_(None),
        )
        pract_res = await self.db.execute(pract_stmt)
        pract_scores = pract_res.scalars().all()
        if pract_scores:
            pract_pct = Decimal(
                sum(p.marks_obtained for p in pract_scores)
                / sum(p.max_marks for p in pract_scores)
                * 100
            )
        else:
            pract_pct = Decimal("0.00")

        # 4. Fetch Clinical evaluations
        clin_stmt = select(ClinicalEvaluation).where(
            ClinicalEvaluation.tenant_id == tenant_id,
            ClinicalEvaluation.student_id == student_id,
            ClinicalEvaluation.course_id == course_id,
            ClinicalEvaluation.professional_phase == professional_phase,
            ClinicalEvaluation.deleted_at.is_(None),
        )
        clin_res = await self.db.execute(clin_stmt)
        clin_scores = clin_res.scalars().all()
        if clin_scores:
            clin_pct = Decimal(
                sum(c.marks_obtained for c in clin_scores)
                / sum(c.max_marks for c in clin_scores)
                * 100
            )
        else:
            clin_pct = Decimal("0.00")

        # Get weights from MDM configurations
        logbook_wt = Decimal("0.20")
        viva_wt = Decimal("0.30")
        pract_wt = Decimal("0.30")
        clin_wt = Decimal("0.20")

        mdm_stmt = select(MdmConfig).where(
            MdmConfig.tenant_id == tenant_id,
            MdmConfig.config_key == "ia_weights",
            MdmConfig.deleted_at.is_(None),
        )
        mdm_res = await self.db.execute(mdm_stmt)
        mdm_conf = mdm_res.scalars().first()
        if mdm_conf:
            weights = mdm_conf.config_value
            logbook_wt = Decimal(str(weights.get("logbook", 0.20)))
            viva_wt = Decimal(str(weights.get("viva", 0.30)))
            pract_wt = Decimal(str(weights.get("practical", 0.30)))
            clin_wt = Decimal(str(weights.get("clinical", 0.20)))

        # Weighted calculation out of 100
        logbook_marks = logbook_pct * logbook_wt
        viva_marks = viva_pct * viva_wt
        practical_marks = pract_pct * pract_wt
        clinical_marks = clin_pct * clin_wt

        total_ia = logbook_marks + viva_marks + practical_marks + clinical_marks
        ia_max = Decimal("100.00")
        is_eligible = total_ia >= Decimal("50.00")

        # Upsert into ia_aggregation table
        stmt_upsert = select(IAAggregation).where(
            IAAggregation.tenant_id == tenant_id,
            IAAggregation.student_id == student_id,
            IAAggregation.course_id == course_id,
            IAAggregation.professional_phase == professional_phase,
        )
        res_upsert = await self.db.execute(stmt_upsert)
        agg = res_upsert.scalars().first()

        if not agg:
            agg = IAAggregation(
                tenant_id=tenant_id,
                student_id=student_id,
                course_id=course_id,
                professional_phase=professional_phase,
                logbook_marks=logbook_marks,
                viva_marks=viva_marks,
                practical_marks=practical_marks,
                clinical_marks=clinical_marks,
                total_ia=total_ia,
                ia_max=ia_max,
                is_eligible=is_eligible,
            )
            self.db.add(agg)
        else:
            agg.logbook_marks = logbook_marks
            agg.viva_marks = viva_marks
            agg.practical_marks = practical_marks
            agg.clinical_marks = clinical_marks
            agg.total_ia = total_ia
            agg.ia_max = ia_max
            agg.is_eligible = is_eligible

        await self.db.flush()

        await write_audit_log(
            self.db,
            tenant_id,
            actor_user_id,
            "UPSERT",
            "ia_aggregation",
            student_id,  # Composite key, student_id used as representative resource_id
            new_values={
                "student_id": str(student_id),
                "course_id": str(course_id),
                "total_ia": str(total_ia),
                "is_eligible": is_eligible,
            },
        )
        return agg

    async def aggregate_ia_batch(
        self,
        tenant_id: uuid.UUID,
        course_id: uuid.UUID,
        professional_phase: str,
        actor_user_id: uuid.UUID | None = None,
    ) -> list[IAAggregation]:
        course = await self.db.get(Course, course_id)
        if not course:
            raise ExamServiceError("002", "Course not found")

        stmt = select(Student).where(Student.tenant_id == tenant_id, Student.status == "active")
        res = await self.db.execute(stmt)
        students = res.scalars().all()

        results = []
        for s in students:
            agg = await self.aggregate_ia(
                tenant_id, s.id, course_id, professional_phase, actor_user_id
            )
            results.append(agg)
        return results

    async def check_student_eligibility(  # noqa: PLR0912, PLR0915
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        examination_id: uuid.UUID,
        actor_user_id: uuid.UUID | None = None,
    ) -> ExamEligibility:  # noqa: PLR0912, PLR0915
        # Get Examination
        exam = await self.db.get(Examination, examination_id)
        if not exam or exam.tenant_id != tenant_id:
            raise ExamServiceError("001", "Examination not found")

        # Check student tenant
        student_obj = await self.db.get(Student, student_id)
        if not student_obj or student_obj.tenant_id != tenant_id:
            raise ExamServiceError("003", "Student not found")

        course = await self.db.get(Course, exam.course_id)
        if not course:
            raise ExamServiceError("002", "Course not found")

        # Resolve phase from examination academic year/curriculum structure if needed
        # We'll use "Phase I" as default phase or fetch it if defined. Let's assume Phase I or get it.
        # Since attendance summary uses professional_phase, let's check what phase is defined.
        # VivaScore/PracticalAssessment models use professional_phase field. Let's use 'Phase I' as default,
        # or resolve from existing summaries/scores. Let's fetch one from attendance summary or default.
        professional_phase = "Phase I"
        stmt_phase = select(AttendanceSummary.professional_phase).where(
            AttendanceSummary.tenant_id == tenant_id,
            AttendanceSummary.student_id == student_id,
            AttendanceSummary.course_id == exam.course_id,
        )
        res_phase = await self.db.execute(stmt_phase)
        resolved_phase = res_phase.scalars().first()
        if resolved_phase:
            professional_phase = resolved_phase

        blocking_reasons: Any = []

        # 1. Attendance Check
        stmt_att = select(AttendanceSummary).where(
            AttendanceSummary.tenant_id == tenant_id,
            AttendanceSummary.student_id == student_id,
            AttendanceSummary.course_id == exam.course_id,
            AttendanceSummary.professional_phase == professional_phase,
        )
        res_att = await self.db.execute(stmt_att)
        summaries = res_att.scalars().all()

        if not summaries:
            blocking_reasons.append(
                {
                    "code": "no_attendance_record",
                    "message": "No attendance records found for this course",
                    "resolution": "Register attendance in classes",
                }
            )
        else:
            for s in summaries:
                category = s.attendance_category.lower()
                pct = s.attendance_pct or Decimal("0.00")
                if category == "theory":
                    if pct < Decimal("75.00"):
                        blocking_reasons.append(
                            {
                                "code": "theory_attendance_shortfall",
                                "message": f"Theory attendance of {pct}% is below required 75%",
                                "resolution": "Request extra classes or academic exemption",
                            }
                        )
                elif category in ("practical", "clinical", "doap", "ece", "elective"):
                    if pct < Decimal("80.00"):
                        blocking_reasons.append(
                            {
                                "code": "practical_attendance_shortfall",
                                "message": f"Practical/clinical attendance of {pct}% is below required 80%",
                                "resolution": "Request extra clinical postings or practical sessions",
                            }
                        )

        # 2. Logbook Completion
        stmt_log = select(LogbookAssessment).where(
            LogbookAssessment.tenant_id == tenant_id,
            LogbookAssessment.student_id == student_id,
            LogbookAssessment.subject_code == course.subject_code,
            LogbookAssessment.professional_phase == professional_phase,
        )
        res_log = await self.db.execute(stmt_log)
        logbook_ass = res_log.scalars().first()
        if not logbook_ass or not logbook_ass.is_complete:
            blocking_reasons.append(
                {
                    "code": "logbook_incomplete",
                    "message": "Logbook for this subject is not certified/complete",
                    "resolution": "Complete all mandatory logbook competencies and obtain supervisor sign-off",
                }
            )

        # 3. IA Marks Check
        stmt_ia = select(IAAggregation).where(
            IAAggregation.tenant_id == tenant_id,
            IAAggregation.student_id == student_id,
            IAAggregation.course_id == exam.course_id,
            IAAggregation.professional_phase == professional_phase,
        )
        res_ia = await self.db.execute(stmt_ia)
        ia_agg = res_ia.scalars().first()
        if not ia_agg:
            blocking_reasons.append(
                {
                    "code": "no_ia_aggregation",
                    "message": "Internal Assessment aggregation not found",
                    "resolution": "Trigger IA aggregation calculation for the student",
                }
            )
        elif not ia_agg.is_eligible:
            blocking_reasons.append(
                {
                    "code": "ia_shortfall",
                    "message": f"IA marks of {ia_agg.total_ia}/{ia_agg.ia_max} are below the required 50%",
                    "resolution": "Request remedial IA assessment",
                }
            )

        # 4. Disciplinary Suspension
        student_obj = await self.db.get(Student, student_id)
        if student_obj and student_obj.status == "suspended":
            blocking_reasons.append(
                {
                    "code": "disciplinary_suspension",
                    "message": "Student is under active disciplinary suspension",
                    "resolution": "Resolve disciplinary proceedings with Dean/Principal office",
                }
            )

        # 5. Prerequisite Check
        prereqs = get_prerequisites(course.subject_code)
        for prereq_code in prereqs:
            stmt_prereq_course = select(Course).where(
                Course.tenant_id == tenant_id,
                Course.code == prereq_code,
            )
            res_prereq_course = await self.db.execute(stmt_prereq_course)
            prereq_course = res_prereq_course.scalars().first()
            if prereq_course:
                stmt_res = (
                    select(ExamResult)
                    .join(Examination, Examination.id == ExamResult.examination_id)
                    .where(
                        ExamResult.tenant_id == tenant_id,
                        ExamResult.student_id == student_id,
                        Examination.course_id == prereq_course.id,
                        ExamResult.status == "published",
                        ExamResult.overall_grade.in_(
                            ["pass", "distinction", "PASS", "DISTINCTION"]
                        ),
                    )
                )
                res_res = await self.db.execute(stmt_res)
                if not res_res.scalars().first():
                    blocking_reasons.append(
                        {
                            "code": "prerequisite_missing",
                            "message": f"Prerequisite subject {prereq_code} has not been passed",
                            "resolution": "Pass prerequisite university examination",
                        }
                    )

        is_eligible = len(blocking_reasons) == 0

        # Upsert eligibility
        stmt_elig = select(ExamEligibility).where(
            ExamEligibility.tenant_id == tenant_id,
            ExamEligibility.student_id == student_id,
            ExamEligibility.examination_id == examination_id,
        )
        res_elig = await self.db.execute(stmt_elig)
        elig = res_elig.scalars().first()

        if not elig:
            elig = ExamEligibility(
                tenant_id=tenant_id,
                student_id=student_id,
                examination_id=examination_id,
                is_eligible=is_eligible,
                blocking_reasons=blocking_reasons if not is_eligible else None,
                checked_at=datetime.utcnow(),
                checked_by=actor_user_id,
            )
            self.db.add(elig)
        else:
            elig.is_eligible = is_eligible
            elig.blocking_reasons = blocking_reasons if not is_eligible else None
            elig.checked_at = datetime.utcnow()
            elig.checked_by = actor_user_id

        await self.db.flush()

        await write_audit_log(
            self.db,
            tenant_id,
            actor_user_id,
            "UPSERT",
            "exam_eligibility",
            student_id,
            new_values={
                "student_id": str(student_id),
                "examination_id": str(examination_id),
                "is_eligible": is_eligible,
            },
        )
        return elig

    async def override_eligibility(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        examination_id: uuid.UUID,
        role: str,
        reason: str,
        actor_user_id: uuid.UUID,
    ) -> ExamEligibility:
        # Check permissions: only Principal or Dean can override
        if role not in ("principal", "dean"):
            raise ExamServiceError("003", "Unauthorized role for eligibility override")

        stmt_elig = select(ExamEligibility).where(
            ExamEligibility.tenant_id == tenant_id,
            ExamEligibility.student_id == student_id,
            ExamEligibility.examination_id == examination_id,
        )
        res_elig = await self.db.execute(stmt_elig)
        elig = res_elig.scalars().first()

        old_values = {}
        if elig:
            old_values = {
                "is_eligible": elig.is_eligible,
                "blocking_reasons": elig.blocking_reasons,
            }

        # Override to eligible
        if not elig:
            elig = ExamEligibility(
                tenant_id=tenant_id,
                student_id=student_id,
                examination_id=examination_id,
                is_eligible=True,
                blocking_reasons={"overridden": True, "overridden_by": role, "reason": reason},
                checked_at=datetime.utcnow(),
                checked_by=actor_user_id,
            )
            self.db.add(elig)
        else:
            elig.is_eligible = True
            elig.blocking_reasons = {"overridden": True, "overridden_by": role, "reason": reason}
            elig.checked_at = datetime.utcnow()
            elig.checked_by = actor_user_id

        await self.db.flush()

        await write_audit_log(
            self.db,
            tenant_id,
            actor_user_id,
            "OVERRIDE_ELIGIBILITY",
            "exam_eligibility",
            student_id,
            old_values=old_values,
            new_values={
                "is_eligible": True,
                "overridden_by": role,
                "reason": reason,
            },
        )
        return elig

    async def run_batch_eligibility(
        self,
        tenant_id: uuid.UUID,
        examination_id: uuid.UUID,
        actor_user_id: uuid.UUID | None = None,
    ) -> list[uuid.UUID]:
        exam = await self.db.get(Examination, examination_id)
        if not exam:
            raise ExamServiceError("001", "Examination not found")

        stmt = select(Student).where(Student.tenant_id == tenant_id, Student.status == "active")
        res = await self.db.execute(stmt)
        students = res.scalars().all()

        eligible_ids = []
        for s in students:
            elig = await self.check_student_eligibility(
                tenant_id, s.id, examination_id, actor_user_id
            )
            if elig.is_eligible:
                eligible_ids.append(s.id)
        return eligible_ids

    async def generate_hall_ticket(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID, examination_id: uuid.UUID
    ) -> dict[str, Any]:
        # Check for an existing eligibility record first (honours overrides)
        stmt_elig = select(ExamEligibility).where(
            ExamEligibility.tenant_id == tenant_id,
            ExamEligibility.student_id == student_id,
            ExamEligibility.examination_id == examination_id,
        )
        res_elig = await self.db.execute(stmt_elig)
        stored_elig = res_elig.scalars().first()

        if stored_elig and stored_elig.is_eligible:
            return {
                "student_id": str(student_id),
                "examination_id": str(examination_id),
                "status": "generated",
            }

        # Re-run eligibility check if no stored record or stored is not eligible (and no override)
        if (
            stored_elig
            and stored_elig.blocking_reasons
            and stored_elig.blocking_reasons.get("overridden")
        ):
            # Already overridden but is_eligible is False — should not happen, but be safe
            return {
                "student_id": str(student_id),
                "examination_id": str(examination_id),
                "status": "generated",
            }

        elig = await self.check_student_eligibility(tenant_id, student_id, examination_id)
        if not elig.is_eligible:
            raise ExamServiceError("020", "Student is ineligible for hall ticket")
        return {
            "student_id": str(student_id),
            "examination_id": str(examination_id),
            "status": "generated",
        }

    async def aggregate_station_marks(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID, course_id: uuid.UUID
    ) -> Decimal:
        stmt = select(PracticalAssessment).where(
            PracticalAssessment.tenant_id == tenant_id,
            PracticalAssessment.student_id == student_id,
            PracticalAssessment.course_id == course_id,
            PracticalAssessment.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        scores = res.scalars().all()
        if not scores:
            return Decimal("0.00")
        return sum((s.marks_obtained for s in scores), Decimal("0.00"))

    # ------------------------------------------------------------------
    # R4.3 — Result Processing + Grade Calculation (ADR-040, 041, 045)
    # ------------------------------------------------------------------

    async def submit_result(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        examination_id: uuid.UUID,
        theory_marks: Decimal,
        practical_marks: Decimal,
        actor_user_id: uuid.UUID | None = None,
    ) -> ExamResult:
        """Examiner submits raw marks. Grace marks auto-applied if eligible (ADR-040/041)."""
        stmt_elig = select(ExamEligibility).where(
            ExamEligibility.tenant_id == tenant_id,
            ExamEligibility.student_id == student_id,
            ExamEligibility.examination_id == examination_id,
        )
        res_elig = await self.db.execute(stmt_elig)
        elig = res_elig.scalars().first()
        if not elig or not elig.is_eligible:
            raise ExamServiceError("030", "Student does not have a valid eligibility grant.")

        exam = await self.db.get(Examination, examination_id)
        if not exam or exam.tenant_id != tenant_id:
            raise ExamServiceError("001", "Examination not found.")

        theory_max = Decimal(str(exam.theory_max_marks))
        practical_max = Decimal(str(exam.practical_max_marks))
        is_supplementary = exam.exam_type == "supplementary"
        grace_limit = 0 if is_supplementary else exam.grace_marks_allowed

        # Apply grace marks to theory if narrowly failing (ADR-041: no grace in supplementary)
        grace_applied = 0
        final_theory = theory_marks
        final_practical = practical_marks

        if compute_grade(theory_marks, theory_max) == "fail" and not is_supplementary:
            shortfall = exam.theory_pass_marks - int(theory_marks)
            if 0 < shortfall <= grace_limit:
                grace_applied = shortfall
                final_theory = theory_marks + Decimal(str(grace_applied))

        theory_grade = compute_grade(final_theory, theory_max)
        practical_grade = compute_grade(final_practical, practical_max)

        if theory_grade == "fail" or practical_grade == "fail":
            overall_grade = "fail"
        elif theory_grade == "distinction" and practical_grade == "distinction":
            overall_grade = "distinction"
        else:
            overall_grade = "pass"

        stmt_attempts = select(func.count(ExamResult.id)).where(
            ExamResult.tenant_id == tenant_id,
            ExamResult.student_id == student_id,
            ExamResult.examination_id == examination_id,
            ExamResult.deleted_at.is_(None),
        )
        cnt_res = await self.db.execute(stmt_attempts)
        attempt_number = (cnt_res.scalar() or 0) + 1

        if is_supplementary and attempt_number > 4:
            raise ExamServiceError("032", "Maximum of 4 supplementary attempts reached (ADR-041).")

        total_marks = final_theory + final_practical
        result = ExamResult(
            tenant_id=tenant_id,
            student_id=student_id,
            examination_id=examination_id,
            theory_marks=final_theory,
            practical_marks=final_practical,
            total_marks=total_marks,
            theory_grade=theory_grade,
            practical_grade=practical_grade,
            overall_grade=overall_grade,
            grace_marks_applied=grace_applied,
            attempt_number=attempt_number,
            status="draft",
        )
        self.db.add(result)
        await self.db.flush()

        await write_audit_log(
            self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="SUBMIT_RESULT",
            resource_type="exam_result",
            resource_id=result.id,
            new_values={
                "student_id": str(student_id),
                "examination_id": str(examination_id),
                "theory_marks": float(final_theory),
                "practical_marks": float(final_practical),
                "overall_grade": overall_grade,
                "grace_marks_applied": grace_applied,
                "attempt_number": attempt_number,
            },
        )
        await self.db.commit()
        await self.db.refresh(result)
        return result

    async def record_moderation(
        self,
        tenant_id: uuid.UUID,
        exam_result_id: uuid.UUID,
        examiner_1_marks: Decimal,
        examiner_2_marks: Decimal,
        max_marks: Decimal,
        examiner_3_marks: Decimal | None = None,
        actor_user_id: uuid.UUID | None = None,
    ) -> ExamModeration:
        """Record multi-examiner moderation. >15% gap requires third examiner (ADR-048)."""
        final_marks, method = moderate_marks(
            examiner_1_marks, examiner_2_marks, max_marks, examiner_3_marks
        )
        moderation = ExamModeration(
            tenant_id=tenant_id,
            exam_result_id=exam_result_id,
            examiner_1_marks=examiner_1_marks,
            examiner_2_marks=examiner_2_marks,
            examiner_3_marks=examiner_3_marks,
            moderation_method=method,
            final_marks=final_marks,
        )
        self.db.add(moderation)
        await self.db.flush()
        await write_audit_log(
            self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="RECORD_MODERATION",
            resource_type="exam_moderation",
            resource_id=moderation.id,
            new_values={
                "exam_result_id": str(exam_result_id),
                "moderation_method": method,
                "final_marks": float(final_marks),
                "examiner_3_marks": float(examiner_3_marks) if examiner_3_marks else None,
            },
        )
        await self.db.commit()
        await self.db.refresh(moderation)
        return moderation

    async def _transition_result_status(
        self,
        tenant_id: uuid.UUID,
        exam_result_id: uuid.UUID,
        expected_status: str,
        new_status: str,
        action: str,
        actor_user_id: uuid.UUID | None = None,
    ) -> ExamResult:
        """Internal: advance result workflow status with audit log."""
        result = await self.db.get(ExamResult, exam_result_id)
        if not result or result.tenant_id != tenant_id:
            raise ExamServiceError("033", "Exam result not found.")
        if result.status != expected_status:
            raise ExamServiceError(
                "034",
                f"Result must be in '{expected_status}' state to perform '{action}'.",
                {"current_status": result.status},
            )
        old_status = result.status
        result.status = new_status
        await self.db.flush()
        await write_audit_log(
            self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action.upper(),
            resource_type="exam_result",
            resource_id=exam_result_id,
            old_values={"status": old_status},
            new_values={"status": new_status},
        )
        await self.db.commit()
        await self.db.refresh(result)
        return result

    async def verify_result(
        self,
        tenant_id: uuid.UUID,
        exam_result_id: uuid.UUID,
        actor_user_id: uuid.UUID | None = None,
    ) -> ExamResult:
        """HOD verifies draft result (draft → verified, ADR-045)."""
        return await self._transition_result_status(
            tenant_id, exam_result_id, "draft", "verified", "verify_result", actor_user_id
        )

    async def approve_result(
        self,
        tenant_id: uuid.UUID,
        exam_result_id: uuid.UUID,
        actor_user_id: uuid.UUID | None = None,
    ) -> ExamResult:
        """Principal approves verified result (verified → approved, ADR-045)."""
        return await self._transition_result_status(
            tenant_id, exam_result_id, "verified", "approved", "approve_result", actor_user_id
        )

    async def publish_results(
        self,
        tenant_id: uuid.UUID,
        examination_id: uuid.UUID,
        actor_user_id: uuid.UUID | None = None,
    ) -> int:
        """Publish all approved results for an examination (approved → published, ADR-045)."""
        stmt = select(ExamResult).where(
            ExamResult.tenant_id == tenant_id,
            ExamResult.examination_id == examination_id,
            ExamResult.status == "approved",
            ExamResult.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        results = res.scalars().all()
        for r in results:
            r.status = "published"
            await write_audit_log(
                self.db,
                tenant_id=tenant_id,
                actor_user_id=actor_user_id,
                action="PUBLISH_RESULT",
                resource_type="exam_result",
                resource_id=r.id,
                old_values={"status": "approved"},
                new_values={"status": "published"},
            )
        if results:
            await self.db.flush()
            await self.db.commit()
        return len(results)

    # ------------------------------------------------------------------
    # R4.4 — Mark Sheet PDF Generation (ADR-042)
    # ------------------------------------------------------------------

    async def generate_mark_sheet(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        academic_year: str,
        actor_user_id: uuid.UUID | None = None,
    ) -> MarkSheet:
        """Generate WeasyPrint PDF mark sheet for student+academic_year (ADR-042).

        Retrieves all published results, renders HTML, embeds QR verification code,
        stores as digital_asset, and records the mark_sheet metadata row.
        """
        stmt_results = (
            select(ExamResult)
            .join(
                Examination,
                and_(
                    Examination.id == ExamResult.examination_id,
                    Examination.tenant_id == ExamResult.tenant_id,
                ),
            )
            .where(
                ExamResult.tenant_id == tenant_id,
                ExamResult.student_id == student_id,
                Examination.academic_year == academic_year,
                ExamResult.status == "published",
                ExamResult.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt_results)
        results = res.scalars().all()

        if not results:
            raise ExamServiceError(
                "040",
                "No published results found for this student and academic year.",
                {"student_id": str(student_id), "academic_year": academic_year},
            )

        verification_code = hashlib.sha256(
            f"{tenant_id}:{student_id}:{academic_year}".encode()
        ).hexdigest()[:32]

        html_content = _render_mark_sheet_html(
            tenant_id=tenant_id,
            student_id=student_id,
            academic_year=academic_year,
            results=results,
            verification_code=verification_code,
        )
        pdf_bytes = _render_pdf(html_content)
        sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()

        storage_dir = Path("storage") / "mark_sheets" / str(tenant_id)
        storage_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"marksheet_{student_id}_{academic_year.replace('-', '_')}.pdf"
        storage_path = str(storage_dir / file_name)
        Path(storage_path).write_bytes(pdf_bytes)

        uploader_id = actor_user_id or uuid.UUID("00000000-0000-0000-0000-000000000001")
        asset = DigitalAsset(
            tenant_id=tenant_id,
            file_name=file_name,
            file_type="application/pdf",
            file_size=len(pdf_bytes),
            storage_path=storage_path,
            uploaded_by=uploader_id,
            sha256=sha256_hash,
            meta_attributes={
                "generated_for": str(student_id),
                "academic_year": academic_year,
                "verification_code": verification_code,
            },
        )
        self.db.add(asset)
        await self.db.flush()

        mark_sheet = MarkSheet(
            tenant_id=tenant_id,
            student_id=student_id,
            academic_year=academic_year,
            pdf_asset_id=asset.id,
            qr_verification_code=verification_code,
            generated_by=actor_user_id,
        )
        self.db.add(mark_sheet)
        await self.db.flush()

        await write_audit_log(
            self.db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="GENERATE_MARK_SHEET",
            resource_type="mark_sheet",
            resource_id=mark_sheet.id,
            new_values={
                "student_id": str(student_id),
                "academic_year": academic_year,
                "pdf_asset_id": str(asset.id),
                "verification_code": verification_code,
            },
        )
        await self.db.commit()
        await self.db.refresh(mark_sheet)
        return mark_sheet


def get_prerequisites(course_code: str) -> list[str]:
    prereqs = {
        "PATH": ["ANAT", "PHYS"],
        "MICR": ["ANAT", "PHYS"],
        "PHAR": ["ANAT", "PHYS"],
        "MEDICINE": ["PATH", "PHAR"],
        "SURGERY": ["PATH", "PHAR"],
        "OBGYN": ["PATH", "PHAR"],
        "PEDIATRICS": ["PATH", "PHAR"],
    }
    return prereqs.get(course_code.upper(), [])


# ---------------------------------------------------------------------------
# Grade calculation helpers (pure functions, ADR-040)
# ---------------------------------------------------------------------------

_DISTINCTION_PCT = Decimal("75")
_PASS_PCT = Decimal("50")


def compute_grade(marks_obtained: Decimal, max_marks: Decimal) -> str:
    """Compute NMC grade from raw marks.

    Args:
        marks_obtained: Actual marks obtained (may include grace).
        max_marks: Maximum marks possible.

    Returns:
        Grade string: 'distinction', 'pass', or 'fail'.
    """
    if max_marks == 0:
        return "fail"
    pct = (marks_obtained / max_marks) * Decimal("100")
    if pct >= _DISTINCTION_PCT:
        return "distinction"
    if pct >= _PASS_PCT:
        return "pass"
    return "fail"


def moderate_marks(
    examiner_1_marks: Decimal,
    examiner_2_marks: Decimal,
    max_marks: Decimal,
    examiner_3_marks: Decimal | None = None,
) -> tuple[Decimal, str]:
    """Apply multi-examiner moderation per ADR-048.

    If |e1 - e2| / max_marks <= 15%: average of e1 and e2.
    If |e1 - e2| / max_marks > 15%: third examiner required.
      - When e3 provided: average of the two closest scores.
      - When e3 absent: raises ExamServiceError requesting third examiner.

    Returns:
        (final_marks, moderation_method)
    """
    diff = abs(examiner_1_marks - examiner_2_marks)
    threshold = max_marks * Decimal("0.15")

    if diff <= threshold:
        final = (examiner_1_marks + examiner_2_marks) / Decimal("2")
        final = final.quantize(Decimal("0.01"))
        return final, "average_two"

    # Gap > 15% — need third examiner
    if examiner_3_marks is None:
        raise ExamServiceError(
            "031",
            "Gap between examiners exceeds 15%. Third examiner mandatory (ADR-048).",
            {"examiner_1": float(examiner_1_marks), "examiner_2": float(examiner_2_marks)},
        )

    # Three examiners: average of the two closest marks
    pairs = [
        (abs(examiner_1_marks - examiner_3_marks), examiner_1_marks, examiner_3_marks),
        (abs(examiner_2_marks - examiner_3_marks), examiner_2_marks, examiner_3_marks),
        (abs(examiner_1_marks - examiner_2_marks), examiner_1_marks, examiner_2_marks),
    ]
    pairs.sort()
    _, a, b = pairs[0]
    final = ((a + b) / Decimal("2")).quantize(Decimal("0.01"))
    return final, "closest_pair_three"


# ---------------------------------------------------------------------------
# Mark sheet rendering helpers (ADR-042)
# ---------------------------------------------------------------------------


def _render_mark_sheet_html(
    tenant_id: uuid.UUID,
    student_id: uuid.UUID,
    academic_year: str,
    results: Sequence[Any],
    verification_code: str,
) -> str:
    """Render HTML mark sheet for PDF generation with QR code embedding."""
    import qrcode

    verify_url = f"https://synaptix.app/verify/{verification_code}"
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    rows_html = ""
    for r in results:
        grade_class = {"distinction": "grade-d", "pass": "grade-p", "fail": "grade-f"}.get(
            r.overall_grade or "fail", "grade-f"
        )
        grace_note = f" (+{r.grace_marks_applied}G)" if r.grace_marks_applied else ""
        rows_html += (
            f"<tr>"
            f"<td>{r.examination_id}</td>"
            f"<td>{r.theory_marks or '—'}{grace_note}</td>"
            f"<td>{r.practical_marks or '—'}</td>"
            f"<td>{r.total_marks or '—'}</td>"
            f"<td class='{grade_class}'>{(r.overall_grade or 'fail').upper()}</td>"
            f"</tr>"
        )

    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'/>"
        f"<title>Mark Sheet {academic_year}</title>"
        "<style>"
        "body{font-family:Arial,sans-serif;font-size:12px;margin:20mm;color:#111}"
        "h1{text-align:center;font-size:18px}"
        "h2{text-align:center;font-size:14px;color:#555;margin-top:0}"
        "table.r{width:100%;border-collapse:collapse;margin-top:16px}"
        "table.r th{background:#1a1a2e;color:#fff;padding:6px 10px;text-align:left}"
        "table.r td{border:1px solid #ccc;padding:5px 10px}"
        "table.r tr:nth-child(even){background:#f7f7f7}"
        ".grade-d{color:#1a6b2a;font-weight:bold}"
        ".grade-p{color:#0055a5;font-weight:bold}"
        ".grade-f{color:#cc0000;font-weight:bold}"
        ".qr{text-align:right;margin-top:20px}"
        ".footer{margin-top:30px;font-size:10px;color:#888;text-align:center}"
        "</style></head><body>"
        "<h1>Nirmala Foundation — Academic Mark Sheet</h1>"
        f"<h2>Academic Year: {academic_year}</h2>"
        f"<p><strong>Student:</strong> {student_id} | <strong>Tenant:</strong> {tenant_id}</p>"
        "<table class='r'><thead><tr>"
        "<th>Examination</th><th>Theory</th><th>Practical</th><th>Total</th><th>Grade</th>"
        f"</tr></thead><tbody>{rows_html}</tbody></table>"
        "<div class='qr'>"
        "<p style='font-size:10px;color:#888'>Scan to verify</p>"
        f"<img src='data:image/png;base64,{qr_b64}' width='80' height='80' alt='QR'/>"
        f"<p style='font-size:9px;color:#aaa'>{verification_code}</p>"
        "</div>"
        f"<div class='footer'>Verify at: {verify_url}</div>"
        "</body></html>"
    )


def _render_pdf(html_content: str) -> bytes:
    """Convert HTML string to PDF bytes using WeasyPrint.

    Args:
        html_content: Complete HTML document string.

    Returns:
        PDF content as raw bytes.
    """
    from weasyprint import HTML as WeasyprintHTML  # noqa: N811

    return cast(bytes, WeasyprintHTML(string=html_content).write_pdf())
