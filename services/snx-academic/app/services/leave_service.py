"""
Leave Management Service — Phase 2 (A-12).

Leave approval hook: auto-materialises attendance records for events in the
leave window via DB trigger fn_events_after_insert_leave.

Leave cancel/reject hook: removes auto-generated attendance rows where
leave_request_id matches, unless overwritten by manual faculty entry
(in which case a warning is written to audit_log).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance
from app.models.leave_request import LeaveRequest
from app.schemas.leave import LeaveRequestCreate
from app.services.audit_logger import write_audit_log
from packages.shared.errors import InvalidStateTransitionError, ResourceNotFoundError
from packages.shared.logging import get_logger

logger = get_logger(__name__)


class LeaveService:
    """Phase 2 Leave Management.

    All state transitions follow the workflow:
      pending → approved | rejected
      approved → cancelled (by student or admin)

    On approval: DB trigger fn_events_after_insert_leave auto-marks attendance.
    On reject/cancel: service removes auto-generated attendance rows.
    """

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID, actor_id: uuid.UUID) -> None:
        """Initialise the leave service.

        Args:
            db: Active async SQLAlchemy session.
            tenant_id: Current tenant UUID (from JWT context).
            actor_id: Authenticated user performing the action.
        """
        self._db = db
        self._tenant_id = tenant_id
        self._actor_id = actor_id

    # ─────────────────────────────────────────────────────────────────────
    # Public: Create
    # ─────────────────────────────────────────────────────────────────────

    async def create_leave_request(
        self,
        student_id: uuid.UUID,
        req: LeaveRequestCreate,
    ) -> LeaveRequest:
        """Create a new leave request in pending state.

        Args:
            student_id: Student submitting the request.
            req: Validated leave request data.

        Returns:
            Newly created LeaveRequest record.
        """
        leave = LeaveRequest(
            tenant_id=self._tenant_id,
            student_id=student_id,
            leave_type=req.leave_type,
            start_date=req.start_date,
            end_date=req.end_date,
            reason=req.reason,
            rotation_id=req.rotation_id,
            status="pending",
            created_by=self._actor_id,
            updated_by=self._actor_id,
        )
        self._db.add(leave)
        await self._db.flush()

        await write_audit_log(
            db=self._db,
            tenant_id=self._tenant_id,
            actor_user_id=self._actor_id,
            action="LEAVE_REQUESTED",
            resource_type="leave_request",
            resource_id=leave.id,
            new_values={
                "student_id": str(student_id),
                "leave_type": req.leave_type,
                "start_date": str(req.start_date),
                "end_date": str(req.end_date),
            },
        )

        logger.info(
            "Leave request created",
            extra={
                "tenant_id": str(self._tenant_id),
                "leave_request_id": str(leave.id),
                "student_id": str(student_id),
                "leave_type": req.leave_type,
            },
        )
        return leave

    # ─────────────────────────────────────────────────────────────────────
    # Public: Approve
    # ─────────────────────────────────────────────────────────────────────

    async def approve_leave(
        self,
        leave_request_id: uuid.UUID,
        remarks: str | None = None,
    ) -> LeaveRequest:
        """Approve a pending leave request.

        After status is set to 'approved', the DB trigger
        fn_events_after_insert_leave will auto-mark any EXISTING events
        within the leave window with status='medical' or 'excused'.
        NEW events created after approval are handled by the trigger on
        the events table.

        Args:
            leave_request_id: Leave request UUID to approve.
            remarks: Optional HOD/Principal remarks.

        Returns:
            Updated LeaveRequest record.

        Raises:
            ResourceNotFoundError: If leave request not found.
            InvalidStateTransitionError: If not in pending state.
        """
        leave = await self._get_leave_or_raise(leave_request_id)

        if leave.status != "pending":
            raise InvalidStateTransitionError(
                f"Cannot approve leave_request {leave_request_id} — current status is '{leave.status}'"
            )

        old_status = leave.status
        leave.status = "approved"
        leave.updated_by = self._actor_id
        await self._db.flush()

        # Backfill attendance for events already in the leave window
        await self._backfill_leave_attendance(leave)

        await write_audit_log(
            db=self._db,
            tenant_id=self._tenant_id,
            actor_user_id=self._actor_id,
            action="LEAVE_APPROVED",
            resource_type="leave_request",
            resource_id=leave.id,
            old_values={"status": old_status},
            new_values={"status": "approved", "remarks": remarks},
        )

        logger.info(
            "Leave request approved",
            extra={
                "tenant_id": str(self._tenant_id),
                "leave_request_id": str(leave_request_id),
                "student_id": str(leave.student_id),
            },
        )
        return leave

    # ─────────────────────────────────────────────────────────────────────
    # Public: Reject
    # ─────────────────────────────────────────────────────────────────────

    async def reject_leave(
        self,
        leave_request_id: uuid.UUID,
        remarks: str,
    ) -> LeaveRequest:
        """Reject a pending leave request.

        Args:
            leave_request_id: Leave request UUID to reject.
            remarks: Mandatory rejection reason.

        Returns:
            Updated LeaveRequest record.

        Raises:
            ResourceNotFoundError: If leave request not found.
            InvalidStateTransitionError: If not in pending state.
        """
        leave = await self._get_leave_or_raise(leave_request_id)

        if leave.status != "pending":
            raise InvalidStateTransitionError(
                f"Cannot reject leave_request {leave_request_id} — current status is '{leave.status}'"
            )

        old_status = leave.status
        leave.status = "rejected"
        leave.updated_by = self._actor_id
        await self._db.flush()

        await write_audit_log(
            db=self._db,
            tenant_id=self._tenant_id,
            actor_user_id=self._actor_id,
            action="LEAVE_REJECTED",
            resource_type="leave_request",
            resource_id=leave.id,
            old_values={"status": old_status},
            new_values={"status": "rejected", "remarks": remarks},
        )
        return leave

    # ─────────────────────────────────────────────────────────────────────
    # Public: Cancel
    # ─────────────────────────────────────────────────────────────────────

    async def cancel_leave(
        self,
        leave_request_id: uuid.UUID,
    ) -> LeaveRequest:
        """Cancel an approved leave request.

        Rolls back auto-generated attendance rows that were created
        by the approval trigger — but ONLY rows where:
          leave_request_id matches AND
          updated_by == actor_id (i.e., not overwritten by manual faculty entry).

        If faculty manually updated an auto-generated row, we keep their entry
        and write a warning to audit_log.

        Args:
            leave_request_id: Leave request UUID to cancel.

        Returns:
            Updated LeaveRequest record.

        Raises:
            ResourceNotFoundError: If leave request not found.
            InvalidStateTransitionError: If not in approved state.
        """
        leave = await self._get_leave_or_raise(leave_request_id)

        if leave.status != "approved":
            raise InvalidStateTransitionError(
                f"Cannot cancel leave_request {leave_request_id} — current status is '{leave.status}'"
            )

        # Roll back attendance rows auto-generated by this leave
        preserved_count = await self._rollback_leave_attendance(leave)

        old_status = leave.status
        leave.status = "cancelled"
        leave.updated_by = self._actor_id
        await self._db.flush()

        await write_audit_log(
            db=self._db,
            tenant_id=self._tenant_id,
            actor_user_id=self._actor_id,
            action="LEAVE_CANCELLED",
            resource_type="leave_request",
            resource_id=leave.id,
            old_values={"status": old_status},
            new_values={
                "status": "cancelled",
                "preserved_manual_overrides": preserved_count,
            },
        )
        return leave

    # ─────────────────────────────────────────────────────────────────────
    # Public: Get
    # ─────────────────────────────────────────────────────────────────────

    async def get_leave_requests(
        self,
        student_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[LeaveRequest]:
        """List leave requests, optionally filtered by student and/or status.

        Args:
            student_id: Filter to one student (optional).
            status: Filter by status (optional).

        Returns:
            List of matching LeaveRequest records.
        """
        stmt = select(LeaveRequest).where(
            LeaveRequest.tenant_id == self._tenant_id,
            LeaveRequest.deleted_at.is_(None),
        )
        if student_id:
            stmt = stmt.where(LeaveRequest.student_id == student_id)
        if status:
            stmt = stmt.where(LeaveRequest.status == status)
        result = await self._db.execute(stmt.order_by(LeaveRequest.created_at.desc()))
        return list(result.scalars().all())

    # ─────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────

    async def _get_leave_or_raise(self, leave_request_id: uuid.UUID) -> LeaveRequest:
        """Fetch leave request or raise ResourceNotFoundError.

        Args:
            leave_request_id: UUID to look up.

        Returns:
            LeaveRequest record.

        Raises:
            ResourceNotFoundError: If not found in this tenant.
        """
        stmt = select(LeaveRequest).where(
            LeaveRequest.tenant_id == self._tenant_id,
            LeaveRequest.id == leave_request_id,
            LeaveRequest.deleted_at.is_(None),
        )
        result = await self._db.execute(stmt)
        leave = result.scalars().first()
        if leave is None:
            raise ResourceNotFoundError(
                f"LeaveRequest {leave_request_id} not found in tenant {self._tenant_id}"
            )
        return leave

    async def _backfill_leave_attendance(self, leave: LeaveRequest) -> None:
        """Backfill attendance records for events already in the leave window.

        Called after approval to handle events that existed before approval.
        Uses ON CONFLICT DO NOTHING — never overwrites existing manual entries.

        Args:
            leave: Approved LeaveRequest record.
        """
        from sqlalchemy import text

        backfill_sql = text("""
            INSERT INTO attendance (
                tenant_id, student_id, event_id, session_id, leave_request_id, status,
                attendance_category, professional_phase, method, marked_at, original_marked_at,
                created_by, updated_by
            )
            SELECT
                e.tenant_id,
                :student_id,
                e.id,
                NULL,
                :leave_request_id,
                CASE WHEN :leave_type = 'medical' THEN 'medical'::varchar ELSE 'excused'::varchar END,
                e.attendance_category,
                e.professional_phase,
                'manual'::varchar,
                NOW(),
                NOW(),
                :actor_id,
                :actor_id
            FROM events e
            WHERE e.tenant_id = :tenant_id
              AND e.date >= :start_date
              AND e.date <= :end_date
              AND e.status = 'scheduled'
              AND e.deleted_at IS NULL
            ON CONFLICT (tenant_id, event_id, student_id) WHERE deleted_at IS NULL DO NOTHING
        """)
        await self._db.execute(
            backfill_sql,
            {
                "tenant_id": self._tenant_id,
                "student_id": leave.student_id,
                "leave_request_id": leave.id,
                "leave_type": leave.leave_type,
                "start_date": leave.start_date,
                "end_date": leave.end_date,
                "actor_id": self._actor_id,
            },
        )

    async def _rollback_leave_attendance(self, leave: LeaveRequest) -> int:
        """Remove auto-generated attendance rows for a cancelled leave.

        Only removes rows where leave_request_id matches AND the row
        was NOT manually overwritten by faculty (created_by == actor_id
        check is not reliable; use leave_request_id as the key signal).

        Rows with leave_request_id=None (manually corrected) are preserved.
        Returns count of preserved rows that were NOT deleted (manual overrides).

        Args:
            leave: Cancelled LeaveRequest record.

        Returns:
            Number of rows preserved (manual overrides detected).
        """
        # Count rows that will be PRESERVED (manually modified: updated_by != None means faculty edited)
        from sqlalchemy import func, select

        preserved_stmt = select(func.count()).where(
            Attendance.tenant_id == self._tenant_id,
            Attendance.leave_request_id == leave.id,
            Attendance.needs_review.is_(True),  # Faculty reviewed/modified = preserve
            Attendance.deleted_at.is_(None),
        )
        result = await self._db.execute(preserved_stmt)
        preserved_count: int = result.scalar() or 0

        # Soft-delete auto-generated rows (not manually overwritten)
        from datetime import datetime

        from sqlalchemy import update as sa_update

        soft_delete_stmt = (
            sa_update(Attendance)
            .where(
                Attendance.tenant_id == self._tenant_id,
                Attendance.leave_request_id == leave.id,
                Attendance.needs_review.is_(False),  # Not manually modified
                Attendance.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.utcnow(), updated_by=self._actor_id)
        )
        await self._db.execute(soft_delete_stmt)

        if preserved_count > 0:
            await write_audit_log(
                db=self._db,
                tenant_id=self._tenant_id,
                actor_user_id=self._actor_id,
                action="LEAVE_CANCEL_MANUAL_OVERRIDE_PRESERVED",
                resource_type="leave_request",
                resource_id=leave.id,
                new_values={
                    "preserved_count": preserved_count,
                    "warning": "Faculty had manually edited some auto-generated attendance rows. Those rows were preserved.",
                },
            )
            logger.warning(
                "Leave cancel: preserved manually-overridden attendance rows",
                extra={
                    "tenant_id": str(self._tenant_id),
                    "leave_request_id": str(leave.id),
                    "preserved_count": preserved_count,
                },
            )

        return preserved_count
