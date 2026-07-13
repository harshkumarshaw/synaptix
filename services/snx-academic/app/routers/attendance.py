"""
Attendance Router — Phase 2 (A-11).

Endpoints:
  POST   /attendance/mark            — Mark single attendance
  POST   /attendance/bulk-mark       — Bulk mark (end-of-class)
  GET    /attendance/eligibility     — NMC two-threshold eligibility check
  GET    /attendance/summary         — Summary for student+course+phase+category
  POST   /attendance/exemptions      — Grant exemption (Principal only)
  POST   /attendance/accommodations  — Create threshold override (Principal only)
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.attendance import (
    AttendanceBulkMarkRequest,
    AttendanceMarkRequest,
    AttendanceRecordOut,
    AttendanceSummaryOut,
    EligibilityCheckOut,
)
from app.services.attendance_service import AttendanceService
from packages.shared.auth.dependencies import get_current_user, require_roles
from packages.shared.auth.jwt import TokenPayload
from packages.shared.db.session import get_db
from packages.shared.errors import ResourceNotFoundError

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _get_attendance_service(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db=Depends(get_db),
) -> AttendanceService:
    """FastAPI dependency: construct AttendanceService with DB session and tenant context."""
    return AttendanceService(
        db=db,
        tenant_id=current_user.tenant_uuid,
        actor_id=current_user.user_uuid,
    )


@router.post(
    "/mark",
    response_model=AttendanceRecordOut,
    status_code=status.HTTP_201_CREATED,
    summary="Mark attendance for one student (manual or QR)",
)
async def mark_attendance(
    req: AttendanceMarkRequest,
    current_user: Annotated[
        TokenPayload, Depends(require_roles(["faculty", "hod", "institution_admin"]))
    ],
    service: Annotated[AttendanceService, Depends(_get_attendance_service)],
) -> AttendanceRecordOut:
    """Mark or upsert attendance for a single student.

    Idempotent — repeated calls update the record using conflict resolution
    (latest wall-clock assertion wins).
    """
    try:
        record = await service.mark_attendance(req)
        return AttendanceRecordOut.model_validate(record)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/bulk-mark",
    response_model=list[AttendanceRecordOut],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk mark attendance for multiple students in one event",
)
async def bulk_mark_attendance(
    req: AttendanceBulkMarkRequest,
    current_user: Annotated[
        TokenPayload, Depends(require_roles(["faculty", "hod", "institution_admin"]))
    ],
    service: Annotated[AttendanceService, Depends(_get_attendance_service)],
) -> list[AttendanceRecordOut]:
    """Bulk mark attendance — faculty end-of-class marking."""
    try:
        records = await service.bulk_mark_attendance(req)
        return [AttendanceRecordOut.model_validate(r) for r in records]
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


async def _resolve_student_id(db, student_id: uuid.UUID) -> uuid.UUID:
    """Resolve student's primary key (id) from user_id if needed."""
    from sqlalchemy import text

    res = await db.execute(
        text("SELECT id FROM students WHERE user_id = :sid OR id = :sid"), {"sid": student_id}
    )
    resolved = res.scalar()
    return resolved or student_id


@router.get(
    "/eligibility",
    response_model=EligibilityCheckOut,
    status_code=status.HTTP_200_OK,
    summary="Check NMC two-threshold attendance eligibility (75% theory / 80% practical)",
)
async def check_eligibility(
    student_id: uuid.UUID,
    course_id: uuid.UUID,
    professional_phase: str,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AttendanceService, Depends(_get_attendance_service)],
) -> EligibilityCheckOut:
    """Check hall-ticket attendance eligibility for a student.

    Returns pass/fail for theory (≥75%) and practical (≥80%) independently.
    """
    student_uuid = await _resolve_student_id(service.db, student_id)
    return await service.check_eligibility(student_uuid, course_id, professional_phase)


@router.get(
    "/summary",
    response_model=AttendanceSummaryOut | None,
    status_code=status.HTTP_200_OK,
    summary="Get attendance summary for student/course/phase/category",
)
async def get_attendance_summary(
    student_id: uuid.UUID,
    course_id: uuid.UUID,
    professional_phase: str,
    attendance_category: str,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[AttendanceService, Depends(_get_attendance_service)],
) -> AttendanceSummaryOut | None:
    """Fetch the attendance summary row. Returns null if no sessions recorded yet."""
    student_uuid = await _resolve_student_id(service.db, student_id)
    summary = await service.get_summary(
        student_uuid, course_id, professional_phase, attendance_category
    )
    if summary is None:
        return None
    return AttendanceSummaryOut.model_validate(summary)


@router.get(
    "/student/{student_id}/summary",
    status_code=status.HTTP_200_OK,
    summary="Get list of attendance summaries for a student",
)
async def get_student_attendance_summary(
    student_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db=Depends(get_db),
) -> list[dict]:
    """Fetch attendance summaries for a student across all courses."""
    from sqlalchemy import select

    from app.models.attendance import AttendanceSummary
    from app.models.course import Course

    student_uuid = await _resolve_student_id(db, student_id)

    stmt = (
        select(AttendanceSummary, Course.name, Course.subject_code)
        .join(Course, Course.id == AttendanceSummary.course_id)
        .where(AttendanceSummary.student_id == student_uuid)
    )
    result = await db.execute(stmt)
    rows = result.all()

    summaries = []
    for summary, course_name, subject_code in rows:
        category = summary.attendance_category.lower()
        threshold = 75.00 if category == "theory" else 80.00
        attendance_pct = float(summary.attendance_pct or 0.0)
        is_eligible = attendance_pct >= threshold

        summaries.append(
            {
                "student_id": str(summary.student_id),
                "course_id": str(summary.course_id),
                "course_name": course_name,
                "subject_code": subject_code,
                "attendance_category": summary.attendance_category,
                "sessions_conducted": summary.sessions_conducted,
                "sessions_present": summary.sessions_present,
                "sessions_excused": summary.sessions_excused,
                "sessions_medical": summary.sessions_medical,
                "sessions_official_duty": summary.sessions_official_duty,
                "attendance_pct": attendance_pct,
                "threshold": threshold,
                "is_eligible": is_eligible,
            }
        )

    return summaries
