"""
Synaptix Domain Error Hierarchy.

All domain exceptions must:
1. Inherit from SynaptixError
2. Have a unique SNX-XXX-NNN error code
3. Be documented in conventions/ERROR_HANDLING.md
4. Have a corresponding test in tests/

Never use bare Exception, ValueError, or stdlib exceptions for domain logic.
Never swallow exceptions silently.

Usage:
    from packages.shared.errors import SynaptixError, TenantNotFoundError

    raise TenantNotFoundError(
        "Tenant {id} not found",
        details={"tenant_id": str(tenant_id)}
    )
"""

from __future__ import annotations

from typing import Any


class SynaptixError(Exception):
    """Base class for all Synaptix domain exceptions.

    Every domain exception must:
    - Inherit from this class
    - Set a unique `code` class attribute (format: SNX-XXX-NNN)
    - Pass a human-readable message and optional structured `details`

    Attributes:
        code: Unique error code, e.g. "SNX-ATT-001".
        message: Human-readable error description.
        details: Optional structured data for the error response.
    """

    code: str = "SNX-GEN-000"

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Human-readable description of the error.
            details: Optional structured dict with context (e.g., current vs required values).
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the error to the standard API error envelope format.

        Returns:
            Dict with keys: code, message, details.
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ============================================================================
# Tenant Errors (SNX-TNT-XXX)
# ============================================================================


class TenantNotFoundError(SynaptixError):
    """Raised when the requested tenant does not exist."""

    code = "SNX-TNT-001"


class TenantContextMissingError(SynaptixError):
    """Raised when a request arrives without a valid tenant context.

    This should NEVER happen in production if middleware is configured correctly.
    If this is raised, it indicates a missing @require_tenant_context decorator.
    """

    code = "SNX-TNT-002"


class TenantIsolationViolationError(SynaptixError):
    """Raised when a cross-tenant data access is detected and blocked.

    This is a CRITICAL security error. Must be logged and alerted.
    """

    code = "SNX-TNT-003"


# ============================================================================
# Authentication Errors (SNX-AUTH-XXX)
# ============================================================================


class AuthenticationError(SynaptixError):
    """Raised when authentication fails (invalid credentials, expired token)."""

    code = "SNX-AUTH-001"


class TokenExpiredError(SynaptixError):
    """Raised when a JWT token has expired."""

    code = "SNX-AUTH-002"


class TokenInvalidError(SynaptixError):
    """Raised when a JWT token is malformed or signature is invalid."""

    code = "SNX-AUTH-003"


class MFARequiredError(SynaptixError):
    """Raised when MFA is required but not completed for a privileged role."""

    code = "SNX-AUTH-004"


class MFACodeInvalidError(SynaptixError):
    """Raised when the provided MFA code (TOTP) is incorrect or expired."""

    code = "SNX-AUTH-005"


class PermissionDeniedError(SynaptixError):
    """Raised when a user lacks the required permission for an operation."""

    code = "SNX-AUTH-006"


class AccountDisabledError(SynaptixError):
    """Raised when a user account has been disabled by an administrator."""

    code = "SNX-AUTH-007"


# ============================================================================
# Attendance Errors (SNX-ATT-XXX)
# ============================================================================


class AttendanceShortfallError(SynaptixError):
    """Raised when a student's attendance is below the required threshold.

    NMC mandates:
    - 75% minimum for theory attendance
    - 80% minimum for practical/clinical/DOAP/ECE attendance

    Details should include: current_pct, required_pct, subject_code, category.
    """

    code = "SNX-ATT-001"


class AttendanceCategoryMismatchError(SynaptixError):
    """Raised when an attendance record is submitted with an invalid category
    for the given session type (e.g., 'theory' category for a practical session).
    """

    code = "SNX-ATT-002"


class AttendanceAlreadyMarkedError(SynaptixError):
    """Raised when attendance for a student-session pair is already recorded."""

    code = "SNX-ATT-003"


class AttendanceConflictError(SynaptixError):
    """Raised when an offline sync creates an irreconcilable conflict.

    Under normal circumstances the latest-wins rule resolves conflicts.
    This error is raised only when both parties claim the same timestamp
    and produce different statuses.
    """

    code = "SNX-ATT-006"


class QRCodeExpiredError(SynaptixError):
    """Raised when a student scans an expired QR code for attendance."""

    code = "SNX-ATT-004"


class QRCodeInvalidError(SynaptixError):
    """Raised when the QR code HMAC signature verification fails."""

    code = "SNX-ATT-005"


# ============================================================================
# Eligibility Errors (SNX-ELG-XXX)
# ============================================================================


class HallTicketIneligibleError(SynaptixError):
    """Raised when a student fails the hall ticket eligibility check.

    Details should enumerate every failing criterion.
    """

    code = "SNX-ELG-001"


class NExTIneligibleError(SynaptixError):
    """Raised when a student fails the NExT eligibility check.

    NExT requires all hall ticket criteria PLUS elective logbooks for both blocks.
    Details should enumerate every failing criterion.
    """

    code = "SNX-ELG-002"


class LogbookIncompleteError(SynaptixError):
    """Raised when a student's logbook is not submitted or not assessed,
    blocking hall ticket issuance.
    """

    code = "SNX-ELG-003"


class CRMIIneligibleError(SynaptixError):
    """Raised when an intern fails CRMI completion criteria.

    CRMI requires 7 mandatory rotations, 75% per rotation, ≤15 days total leave.
    """

    code = "SNX-ELG-004"


# ============================================================================
# Resource / Not Found Errors (SNX-RES-XXX)
# ============================================================================


class ResourceNotFoundError(SynaptixError):
    """Raised when a requested resource does not exist.

    Generic fallback for resource-not-found when no specific error exists.
    """

    code = "SNX-RES-001"


class StudentNotFoundError(SynaptixError):
    """Raised when the specified student does not exist."""

    code = "SNX-RES-002"


class FacultyNotFoundError(SynaptixError):
    """Raised when the specified faculty member does not exist."""

    code = "SNX-RES-003"


class SessionNotFoundError(SynaptixError):
    """Raised when the specified academic session/event does not exist."""

    code = "SNX-RES-004"


class BatchNotFoundError(SynaptixError):
    """Raised when the specified batch does not exist."""

    code = "SNX-RES-005"


# ============================================================================
# Workflow / State Errors (SNX-WFL-XXX)
# ============================================================================


class InvalidStateTransitionError(SynaptixError):
    """Raised when a state machine receives an invalid transition.

    E.g., trying to mark attendance for a session that has not started.
    """

    code = "SNX-WFL-001"


class WorkflowNotFoundError(SynaptixError):
    """Raised when the requested workflow definition does not exist."""

    code = "SNX-WFL-002"


class ApprovalRequiredError(SynaptixError):
    """Raised when an action requires approval before it can proceed."""

    code = "SNX-WFL-003"


# ============================================================================
# Validation Errors (SNX-VAL-XXX)
# ============================================================================


class ValidationError(SynaptixError):
    """Raised when business logic validation fails beyond Pydantic's scope.

    Do not use for simple field validation (Pydantic handles that).
    Use for cross-field or cross-entity business rules.
    """

    code = "SNX-VAL-001"


class DuplicateRecordError(SynaptixError):
    """Raised when trying to create a record that already exists (unique constraint)."""

    code = "SNX-VAL-002"
