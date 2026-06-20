# Error Handling Conventions — Synaptix

## Three Layers of Errors

### Layer 1: Validation Errors (Pydantic) → 400

```python
from pydantic import BaseModel, Field, field_validator

class MarkAttendanceRequest(BaseModel):
    student_id: UUID
    event_id: UUID
    status: AttendanceStatus
    method: AttendanceMethod
    
    @field_validator('status')
    @classmethod
    def status_must_be_valid(cls, v: AttendanceStatus) -> AttendanceStatus:
        # Pydantic auto-validates enum membership; add custom rules here
        return v
```

Pydantic errors auto-return 400 with structured detail. No code needed.

### Layer 2: Business Logic Errors → 422

Domain-specific exceptions inheriting from `SynaptixError`:

```python
# packages/shared/errors/base.py
class SynaptixError(Exception):
    code: str = "SNX-UNKNOWN"
    http_status: int = 500
    
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

# services/attendance/errors.py
class AttendanceShortfallError(SynaptixError):
    code = "SNX-ATT-001"
    http_status = 422
    
class TheoryAttendanceShortfallError(AttendanceShortfallError):
    code = "SNX-ATT-002"

class PracticalAttendanceShortfallError(AttendanceShortfallError):
    code = "SNX-ATT-003"
```

Usage:

```python
if theory_pct < NMC_THEORY_THRESHOLD:
    raise TheoryAttendanceShortfallError(
        f"Theory attendance {theory_pct}% below required {NMC_THEORY_THRESHOLD}%",
        details={
            "current": theory_pct,
            "required": NMC_THEORY_THRESHOLD,
            "subject_code": subject_code,
            "phase": phase,
        }
    )
```

### Layer 3: System Errors → 500

Database errors, network timeouts, unexpected conditions. Let them bubble up. Global handler logs with full context and returns generic 500 (no internal details leaked to user).

## Global Exception Handler

```python
# packages/shared/errors/handler.py
from fastapi import Request
from fastapi.responses import JSONResponse

async def synaptix_exception_handler(request: Request, exc: SynaptixError):
    logger.error(
        f"Domain error: {exc.code}",
        extra={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "request_id": request.state.request_id,
        }
    )
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "success": False,
            "data": None,
            "meta": {
                "request_id": request.state.request_id,
                "timezone": "Asia/Kolkata",
                "api_version": "v1",
            },
            "errors": [{
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }]
        }
    )
```

## Error Code Registry

Every error code must be registered in `docs/ERROR_CODES.md` (maintained by Architect agent):

| Code | Service | Message | HTTP |
|------|---------|---------|------|
| SNX-ATT-001 | Attendance | Generic shortfall | 422 |
| SNX-ATT-002 | Attendance | Theory shortfall (<75%) | 422 |
| SNX-ATT-003 | Attendance | Practical shortfall (<80%) | 422 |
| SNX-NMC-001 | NMC | Logbook not submitted | 422 |
| SNX-NMC-002 | NMC | AETCOM not completed | 422 |
| SNX-NMC-003 | NMC | Elective logbook missing | 422 |
| SNX-RBAC-001 | Auth | Insufficient permissions | 403 |
| SNX-TNT-001 | Tenant | Cross-tenant access attempt | 403 |
| ... | | | |

## Never Do

```python
# NEVER — bare except
try:
    ...
except:
    pass

# NEVER — silent failure
try:
    ...
except Exception:
    return None

# NEVER — generic exception
raise Exception("error")

# NEVER — print
print(f"error: {e}")

# NEVER — leak internal details to user
return {"error": str(e)}  # exposes stack traces, secrets, internal paths
```

## Always Do

```python
# ALWAYS — specific exception
raise AttendanceShortfallError(...)

# ALWAYS — structured log
logger.error("Operation failed", extra={"operation": "mark_attendance", "error": str(e)})

# ALWAYS — re-raise or wrap
try:
    await external_api.call()
except HTTPError as e:
    raise ExternalServiceError("HIMS API unavailable") from e

# ALWAYS — clean response to user
# (handled by global exception handler — your code just raises)
```

## Retry Logic

```python
from packages.shared.retry import async_retry

@async_retry(max_attempts=3, backoff_factor=2.0)
async def call_external_service():
    ...
```

Retry only:
- Network errors (timeout, connection refused)
- 5xx responses from external APIs
- Database deadlocks

DO NOT retry:
- 4xx responses (client error)
- Domain exceptions (SynaptixError)
- Validation errors

## Circuit Breaker

For external dependencies (HIMS, SMS gateway, WhatsApp API), use circuit breaker pattern via `pybreaker` to prevent cascading failures.
