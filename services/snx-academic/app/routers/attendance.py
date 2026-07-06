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
from packages.shared.db.session import get_session_with_tenant
from packages.shared.errors import ResourceNotFoundError

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _get_attendance_service(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db=Depends(get_session_with_tenant),
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
    return await service.check_eligibility(student_id, course_id, professional_phase)


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
    summary = await service.get_summary(
        student_id, course_id, professional_phase, attendance_category
    )
    if summary is None:
        return None
    return AttendanceSummaryOut.model_validate(summary)
