"""
Attendance Engine Service — Phase 2 (A-11).

Core rules (Commandment 3 — never violate):
  - Theory attendance minimum: 75%
  - Practical / Clinical / DOAP / ECE attendance minimum: 80%
  - Thresholds are INDEPENDENT — both must pass for eligibility
  - Denominator = conducted sessions only (not planned/cancelled)

Conflict resolution (offline vs online sync):
  - Latest wall-clock assertion wins:
    GREATEST(COALESCE(original_marked_at, marked_at), marked_at)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceAccommodation, AttendanceSummary
from app.schemas.attendance import (
    AttendanceBulkMarkRequest,
    AttendanceMarkRequest,
    EligibilityCheckOut,
)
from app.services.audit_logger import write_audit_log
from packages.shared.logging import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# NMC Threshold constants — NEVER change these without NMC authorisation
# ─────────────────────────────────────────────────────────────────────────────
THEORY_THRESHOLD = Decimal("75.00")
PRACTICAL_THRESHOLD = Decimal("80.00")

# Categories that use the 80% practical threshold (Commandment 3)
PRACTICAL_CATEGORIES = frozenset({"practical", "clinical", "doap", "ece"})
# Categories that use the 75% theory threshold
THEORY_CATEGORIES = frozenset({"theory"})
# Categories tracked separately (not hall-ticket-gating by this threshold check)
SEPARATE_CATEGORIES = frozenset({"aetcom", "foundation_course", "elective"})


class AttendanceService:
    """Phase 2 Attendance Engine.

    All methods require an active AsyncSession scoped to the current tenant.
    Tenant isolation is enforced by TenantContextMiddleware upstream;
    all queries additionally filter by tenant_id explicitly (Commandment 1).
    """

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID, actor_id: uuid.UUID | None) -> None:
        """Initialise the attendance service.

        Args:
            db: Active async SQLAlchemy session.
            tenant_id: Current tenant UUID (from JWT context).
            actor_id: Authenticated user performing the action.
        """
        self._db = db
        self._tenant_id = tenant_id
        self._actor_id = actor_id

    # ─────────────────────────────────────────────────────────────────────
    # Public: Mark attendance
    # ─────────────────────────────────────────────────────────────────────

    async def mark_attendance(self, req: AttendanceMarkRequest) -> Attendance:
        """Mark attendance for one student at one event.

        Uses PostgreSQL ON CONFLICT DO UPDATE for upsert semantics.
        Conflict resolution: latest wall-clock assertion wins.

        Args:
            req: Validated attendance mark request.

        Returns:
            The upserted Attendance record.
        """
        now = datetime.utcnow()
        original_ts = req.original_marked_at or now

        stmt = (
            pg_insert(Attendance)
            .values(
                tenant_id=self._tenant_id,
                student_id=req.student_id,
                event_id=req.event_id,
                session_id=req.session_id,
                status=req.status,
                attendance_category=req.attendance_category,
                professional_phase=req.professional_phase,
                method=req.method,
                geo_lat=req.geo_lat,
                geo_lng=req.geo_lng,
                device_id=req.device_id,
                qr_token=req.qr_token,
                marked_at=now,
                original_marked_at=original_ts,
                needs_review=False,
                created_by=self._actor_id,
                updated_by=self._actor_id,
            )
            .on_conflict_do_update(
                constraint="uq_attendance_event_student",
                set_={
                    "status": pg_insert(Attendance).excluded.status,
                    "method": pg_insert(Attendance).excluded.method,
                    "marked_at": now,
                    "updated_by": self._actor_id,
                    # Conflict resolution: keep the later original timestamp
                    "original_marked_at": text(
                        "GREATEST(COALESCE(attendance.original_marked_at, attendance.marked_at), EXCLUDED.marked_at)"
                    ),
                    "needs_review": text(
                        # Flag for review if method changes (e.g., offline→online conflict)
                        "attendance.method != EXCLUDED.method"
                    ),
                },
            )
            .returning(Attendance)
        )

        result = await self._db.execute(stmt)
        attendance = result.scalars().one()
        await self._db.flush()

        # Recalculate summary for this student+course+phase+category
        await self._recalculate_summary(
            student_id=req.student_id,
            event_id=req.event_id,
            attendance_category=req.attendance_category,
            professional_phase=req.professional_phase,
        )

        await write_audit_log(
            db=self._db,
            tenant_id=self._tenant_id,
            actor_user_id=self._actor_id,
            action="ATTENDANCE_MARKED",
            resource_type="attendance",
            resource_id=attendance.id,
            new_values={
                "student_id": str(req.student_id),
                "event_id": str(req.event_id),
                "status": req.status,
                "method": req.method,
            },
        )

        logger.info(
            "Attendance marked",
            extra={
                "tenant_id": str(self._tenant_id),
                "student_id": str(req.student_id),
                "event_id": str(req.event_id),
                "status": req.status,
            },
        )
        return attendance

    async def bulk_mark_attendance(self, req: AttendanceBulkMarkRequest) -> list[Attendance]:
        """Mark attendance for multiple students in one batch.

        Runs each mark_attendance in sequence; wraps in caller's transaction.
        Faculty bulk-marking at end of session is the primary use case.

        Args:
            req: Bulk mark request with list of student records.

        Returns:
            List of upserted Attendance records.
        """
        results: list[Attendance] = []
        for record in req.records:
            single = AttendanceMarkRequest(
                student_id=record.student_id,
                event_id=req.event_id,
                status=record.status,
                attendance_category=req.attendance_category,
                professional_phase=req.professional_phase,
                method=req.method,
                original_marked_at=record.original_marked_at,
            )
            att = await self.mark_attendance(single)
            results.append(att)
        return results

    # ─────────────────────────────────────────────────────────────────────
    # Public: Eligibility check (NMC two-threshold)
    # ─────────────────────────────────────────────────────────────────────

    async def check_eligibility(
        self,
        student_id: uuid.UUID,
        course_id: uuid.UUID,
        professional_phase: str,
    ) -> EligibilityCheckOut:
        """Check NMC attendance eligibility for a student in a course+phase.

        Two independent thresholds (Commandment 3):
        - Theory:    sessions_pct >= 75.00%
        - Practical: sessions_pct >= 80.00%

        Denominator = conducted sessions only (status='conducted' on events table).
        Accommodations (threshold overrides) are applied if active.

        Args:
            student_id: Student UUID.
            course_id: Course UUID.
            professional_phase: e.g. 'Phase II'.

        Returns:
            EligibilityCheckOut with per-threshold pass/fail results.
        """
        # Get theory summary
        theory_summary = await self._get_summary(
            student_id, course_id, professional_phase, "theory"
        )
        # Get practical summary (aggregates practical + clinical + doap + ece)
        practical_pct = await self._get_aggregate_practical_pct(
            student_id, course_id, professional_phase
        )

        # Check for active accommodations (threshold overrides)
        theory_threshold, practical_threshold = await self._get_effective_thresholds(
            student_id, professional_phase
        )

        theory_pct = theory_summary.attendance_pct if theory_summary else Decimal("0.00")
        is_theory_ok = theory_pct >= theory_threshold
        is_practical_ok = practical_pct >= practical_threshold

        failures: list[str] = []
        if not is_theory_ok:
            failures.append(
                f"Theory attendance {theory_pct:.2f}% is below the required {theory_threshold:.2f}% minimum"
            )
        if not is_practical_ok:
            failures.append(
                f"Practical attendance {practical_pct:.2f}% is below the required {practical_threshold:.2f}% minimum"
            )

        return EligibilityCheckOut(
            student_id=student_id,
            is_theory_eligible=is_theory_ok,
            theory_pct=theory_pct,
            theory_threshold=theory_threshold,
            is_practical_eligible=is_practical_ok,
            practical_pct=practical_pct,
            practical_threshold=practical_threshold,
            is_eligible=is_theory_ok and is_practical_ok,
            failures=failures,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Public: Summary query helpers
    # ─────────────────────────────────────────────────────────────────────

    async def get_summary(
        self,
        student_id: uuid.UUID,
        course_id: uuid.UUID,
        professional_phase: str,
        attendance_category: str,
    ) -> AttendanceSummary | None:
        """Fetch the attendance summary row for a student/course/phase/category.

        Args:
            student_id: Student UUID.
            course_id: Course UUID.
            professional_phase: Phase name.
            attendance_category: Attendance category.

        Returns:
            AttendanceSummary or None if no records yet.
        """
        return await self._get_summary(
            student_id, course_id, professional_phase, attendance_category
        )

    # ─────────────────────────────────────────────────────────────────────
    # Private: Summary recalculation
    # ─────────────────────────────────────────────────────────────────────

    async def _recalculate_summary(
        self,
        student_id: uuid.UUID,
        event_id: uuid.UUID,
        attendance_category: str,
        professional_phase: str,
    ) -> None:
        """Recalculate attendance_summary from raw attendance rows.

        Resolves course_id from events.course_ids (via event_courses join).
        Uses raw SQL for performance — no N+1 queries (Performance standard §8).

        Args:
            student_id: Student UUID.
            event_id: Event UUID (used to find course_id).
            attendance_category: Category being updated.
            professional_phase: Phase being updated.
        """
        upsert_sql = text("""
            INSERT INTO attendance_summary (
                tenant_id, student_id, course_id, professional_phase, attendance_category,
                sessions_conducted, sessions_present, sessions_excused,
                sessions_official_duty, sessions_medical, last_recalculated_at
            )
            SELECT
                a.tenant_id,
                a.student_id,
                ec.course_id,
                a.professional_phase,
                a.attendance_category,
                COUNT(*) FILTER (WHERE e.status = 'conducted' AND a.deleted_at IS NULL) AS sessions_conducted,
                COUNT(*) FILTER (WHERE e.status = 'conducted' AND a.status = 'present' AND a.deleted_at IS NULL) AS sessions_present,
                COUNT(*) FILTER (WHERE e.status = 'conducted' AND a.status = 'excused' AND a.deleted_at IS NULL) AS sessions_excused,
                COUNT(*) FILTER (WHERE e.status = 'conducted' AND a.status = 'official_duty' AND a.deleted_at IS NULL) AS sessions_official_duty,
                COUNT(*) FILTER (WHERE e.status = 'conducted' AND a.status = 'medical' AND a.deleted_at IS NULL) AS sessions_medical,
                NOW()
            FROM attendance a
            JOIN events e ON e.tenant_id = a.tenant_id AND e.id = a.event_id
            JOIN event_courses ec ON ec.tenant_id = e.tenant_id AND ec.event_id = e.id
            WHERE a.tenant_id = :tenant_id
              AND a.student_id = :student_id
              AND a.attendance_category = :attendance_category
              AND a.professional_phase = :professional_phase
            GROUP BY a.tenant_id, a.student_id, ec.course_id, a.professional_phase, a.attendance_category
            ON CONFLICT (tenant_id, student_id, course_id, professional_phase, attendance_category)
            DO UPDATE SET
                sessions_conducted = EXCLUDED.sessions_conducted,
                sessions_present = EXCLUDED.sessions_present,
                sessions_excused = EXCLUDED.sessions_excused,
                sessions_official_duty = EXCLUDED.sessions_official_duty,
                sessions_medical = EXCLUDED.sessions_medical,
                last_recalculated_at = NOW()
        """)
        await self._db.execute(
            upsert_sql,
            {
                "tenant_id": self._tenant_id,
                "student_id": student_id,
                "attendance_category": attendance_category,
                "professional_phase": professional_phase,
            },
        )

    async def _get_summary(
        self,
        student_id: uuid.UUID,
        course_id: uuid.UUID,
        professional_phase: str,
        attendance_category: str,
    ) -> AttendanceSummary | None:
        """Fetch a single attendance summary row.

        Args:
            student_id: Student UUID.
            course_id: Course UUID.
            professional_phase: Phase name.
            attendance_category: Category name.

        Returns:
            AttendanceSummary row or None.
        """
        stmt = select(AttendanceSummary).where(
            AttendanceSummary.tenant_id == self._tenant_id,
            AttendanceSummary.student_id == student_id,
            AttendanceSummary.course_id == course_id,
            AttendanceSummary.professional_phase == professional_phase,
            AttendanceSummary.attendance_category == attendance_category,
        )
        result = await self._db.execute(stmt)
        return result.scalars().first()

    async def _get_aggregate_practical_pct(
        self,
        student_id: uuid.UUID,
        course_id: uuid.UUID,
        professional_phase: str,
    ) -> Decimal:
        """Aggregate practical attendance % across all practical categories.

        Aggregates: practical, clinical, doap, ece into a single percentage.
        Denominator = total conducted sessions across all practical categories.

        Args:
            student_id: Student UUID.
            course_id: Course UUID.
            professional_phase: Phase name.

        Returns:
            Aggregate practical attendance percentage.
        """
        sql = text("""
            SELECT
                CASE WHEN SUM(sessions_conducted) = 0 THEN 0.00
                     ELSE ROUND(
                         100.0 * SUM(sessions_present + sessions_excused + sessions_official_duty + sessions_medical)::numeric
                         / SUM(sessions_conducted), 2
                     )
                END AS practical_pct
            FROM attendance_summary
            WHERE tenant_id = :tenant_id
              AND student_id = :student_id
              AND course_id = :course_id
              AND professional_phase = :professional_phase
              AND attendance_category IN ('practical', 'clinical', 'doap', 'ece')
              AND deleted_at IS NULL
        """)
        result = await self._db.execute(
            sql,
            {
                "tenant_id": self._tenant_id,
                "student_id": student_id,
                "course_id": course_id,
                "professional_phase": professional_phase,
            },
        )
        row = result.one_or_none()
        if row is None or row.practical_pct is None:
            return Decimal("0.00")
        return Decimal(str(row.practical_pct))

    async def _get_effective_thresholds(
        self,
        student_id: uuid.UUID,
        professional_phase: str,  # noqa: ARG002 — reserved for phase-specific future overrides
    ) -> tuple[Decimal, Decimal]:
        """Get effective thresholds for a student, applying any active accommodations.

        If an active accommodation exists for this student, use its overrides.
        Overrides can only LOWER thresholds (checked at DB level and schema level).

        Args:
            student_id: Student UUID.
            professional_phase: Current phase (reserved for future phase-specific overrides).

        Returns:
            Tuple of (theory_threshold, practical_threshold).
        """
        from datetime import date

        today = date.today()
        stmt = select(AttendanceAccommodation).where(
            AttendanceAccommodation.tenant_id == self._tenant_id,
            AttendanceAccommodation.student_id == student_id,
            AttendanceAccommodation.effective_from <= today,
            AttendanceAccommodation.effective_until >= today,
            AttendanceAccommodation.deleted_at.is_(None),
        )
        result = await self._db.execute(stmt)
        accommodation = result.scalars().first()

        if accommodation:
            theory = accommodation.theory_threshold_override or THEORY_THRESHOLD
            practical = accommodation.practical_threshold_override or PRACTICAL_THRESHOLD
            return theory, practical

        return THEORY_THRESHOLD, PRACTICAL_THRESHOLD
