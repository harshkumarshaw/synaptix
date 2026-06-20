# Coding Standards — Synaptix

> Mandatory reading for all developer agents (Backend, Frontend, Mobile, Database).

## Python (Backend)

### Version & Toolchain
- Python 3.12 only
- Package manager: `uv` (preferred) or `pip` with `pyproject.toml`
- Formatter: `black` (line length 100)
- Linter: `ruff` (with rules: E, W, F, I, B, UP, S, A, COM, C4, PT, SIM, ARG, PL)
- Type checker: `mypy --strict`

### Imports

```python
# Standard library
import asyncio
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

# Third-party
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Local — packages/shared first, then current service
from packages.shared.auth import require_auth, require_tenant_context
from packages.shared.db import get_db
from packages.shared.errors import SynaptixError

from services.attendance.models import Attendance
from services.attendance.schemas import AttendanceCreate
```

Group order: stdlib → third-party → local. Blank line between groups. Sort within group alphabetically.

### Type Hints

EVERY function signature must have type hints. EVERY variable initialised from `None` or function output must have explicit type annotation if the type is non-obvious.

```python
# GOOD
async def get_attendance(
    student_id: UUID,
    subject_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttendanceResponse:
    ...

# BAD — no return type, no parameter types
async def get_attendance(student_id, subject_code, db):
    ...

# BAD — using Any
async def process(data: Any) -> Any:
    ...
```

### SQLAlchemy 2.0 Style

Use the new declarative `Mapped[]` syntax:

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

class Attendance(Base):
    __tablename__ = "attendance"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), nullable=False)
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id"), nullable=False)
    status: Mapped[AttendanceStatus]
    marked_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    student: Mapped["Student"] = relationship(back_populates="attendance_records")
```

Do NOT use the old `Column()` syntax.

### Async/Await

EVERYTHING I/O bound is async. No `requests`, use `httpx.AsyncClient`. No sync SQLAlchemy, use `AsyncSession`.

```python
# GOOD
async def fetch_student(student_id: UUID, db: AsyncSession) -> Student:
    result = await db.execute(select(Student).where(Student.id == student_id))
    return result.scalar_one_or_none()

# BAD — blocking
def fetch_student(student_id: UUID, db: Session) -> Student:
    return db.query(Student).filter(Student.id == student_id).first()
```

### N+1 Prevention

Always use `selectinload` or `joinedload` when accessing related entities:

```python
# GOOD
stmt = select(Student).options(selectinload(Student.attendance_records))

# BAD — lazy load triggers N+1
stmt = select(Student)
students = (await db.execute(stmt)).scalars().all()
for student in students:
    print(student.attendance_records)  # N+1!
```

### Docstrings (Google Style)

```python
async def calculate_attendance_pct(
    student_id: UUID,
    subject_code: str,
    category: AttendanceCategory,
    db: AsyncSession,
) -> float:
    """Calculate the attendance percentage for a student in a subject.

    Computes the percentage based on conducted sessions only (not planned).
    For MBBS, applies the two-threshold rule (75% theory, 80% practical).

    Args:
        student_id: UUID of the student.
        subject_code: Subject code (e.g., "AN" for Anatomy).
        category: Attendance category (theory, practical, clinical, etc.).
        db: Async database session.

    Returns:
        Attendance percentage as a float between 0.0 and 100.0.

    Raises:
        StudentNotFoundError: If the student does not exist.
        SubjectNotFoundError: If the subject code is invalid.
    """
    ...
```

### Logging (No print!)

```python
from packages.shared.logging import get_logger

logger = get_logger(__name__)

# GOOD
logger.info(
    "Attendance marked",
    extra={
        "student_id": str(student.id),
        "event_id": str(event.id),
        "tenant_id": str(tenant_id),
        "method": method,
    }
)

# BAD
print(f"Attendance marked for {student.id}")  # NEVER use print
```

### Error Handling

```python
# GOOD — domain-specific exception
class AttendanceShortfallError(SynaptixError):
    code = "SNX-ATT-001"
    
raise AttendanceShortfallError(
    f"Theory attendance {current_pct}% below required {required_pct}%",
    details={"current": current_pct, "required": required_pct}
)

# BAD — generic exception
raise Exception("attendance too low")  # NEVER use bare Exception
raise ValueError("attendance too low")  # NEVER use stdlib exceptions for domain errors

# BAD — silent failure
try:
    await calculate_pct(...)
except:  # NEVER bare except
    pass

# BAD — swallowing
try:
    await calculate_pct(...)
except Exception as e:
    print(e)  # NEVER use print, NEVER catch broadly without re-raise
```

## TypeScript (Frontend)

### Version & Toolchain
- TypeScript 5.x with strict mode
- Formatter: Prettier
- Linter: ESLint with `eslint-config-next` + `eslint-plugin-react-hooks`
- No `any` types — use `unknown` with type narrowing if type is genuinely unknown

### Component Structure

```tsx
// GOOD
import { useAttendance } from "@/hooks/useAttendance";
import type { Student } from "@/types/student";

interface AttendanceCardProps {
  student: Student;
  subjectCode: string;
}

export function AttendanceCard({ student, subjectCode }: AttendanceCardProps) {
  const { data, isLoading, error } = useAttendance(student.id, subjectCode);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!data) return null;

  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="font-semibold">{student.name}</h3>
      <p className="text-sm text-muted-foreground">
        Theory: {data.theory_pct}% | Practical: {data.practical_pct}%
      </p>
    </div>
  );
}
```

### Hooks

Custom hooks start with `use`, are in `frontend-web/src/hooks/`, return typed values:

```tsx
export function useAttendance(studentId: string, subjectCode: string) {
  return useQuery<AttendanceData, Error>({
    queryKey: ["attendance", studentId, subjectCode],
    queryFn: async () => {
      const res = await api.get(`/students/${studentId}/attendance/${subjectCode}`);
      return res.data;
    },
  });
}
```

### Tailwind

- Use utility classes only
- No inline `style={{...}}` except for dynamic values (e.g., `height: ${x}px`)
- No CSS modules unless approved by Architect
- Use `cn()` helper for conditional classes

```tsx
import { cn } from "@/lib/utils";

<button
  className={cn(
    "rounded-md px-4 py-2 text-sm font-medium",
    "bg-primary text-primary-foreground hover:bg-primary/90",
    disabled && "opacity-50 cursor-not-allowed"
  )}
  disabled={disabled}
>
  Submit
</button>
```

## Dart / Flutter (Mobile)

### Naming
- Files: `snake_case.dart`
- Classes: `PascalCase`
- Constants: `lowerCamelCase` (Dart convention, not SCREAMING_SNAKE)
- Private: prefix with `_`

### Widget Structure

```dart
class AttendanceScreen extends ConsumerWidget {
  const AttendanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final attendanceAsync = ref.watch(attendanceProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Attendance')),
      body: attendanceAsync.when(
        data: (attendance) => _AttendanceList(attendance: attendance),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}
```

### Riverpod

Use `riverpod_generator` for type safety:

```dart
@riverpod
Future<List<Attendance>> attendance(AttendanceRef ref) async {
  final api = ref.watch(apiClientProvider);
  return api.getMyAttendance();
}
```

### Offline-First

EVERY data operation must work offline:
- Read from local SQLite first
- Background sync to server
- UI never blocked on network

## SQL

### Naming
- snake_case for everything
- Tables: plural (`students`, `attendance_records`)
- Columns: descriptive (`marked_at`, not `m_at`)
- FKs: `{singular_referenced_table}_id` (`student_id`, `event_id`)
- Indexes: `idx_{table}_{columns}` (`idx_attendance_student_subject_category`)

### Every Table Must Have

```sql
CREATE TABLE example (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    -- ... business columns ...
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE example ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_example ON example
    USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);

-- Index tenant_id (every query filters on it)
CREATE INDEX idx_example_tenant ON example(tenant_id);

-- Auto-update updated_at
CREATE TRIGGER update_example_updated_at
    BEFORE UPDATE ON example
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Migrations

- One Alembic chain for the entire monorepo
- Migration files in `alembic/versions/`
- Format: `{revision}_{description}.py`
- Always include rollback (`downgrade()`)
- Test both directions before committing

## General

### File Headers (Optional but Recommended)

```python
"""
Attendance Engine — Two-threshold rule for MBBS.

Implements NMC CBME 2019/2023 requirements:
- 75% theory attendance minimum
- 80% practical/clinical attendance minimum
- Separate enforcement per subject per phase

NMC Reference: GMER 2019, §11.1
"""
```

### Constants

Define magic numbers as named constants:

```python
# GOOD
NMC_THEORY_THRESHOLD = 75.0
NMC_PRACTICAL_THRESHOLD = 80.0
NMC_ELECTIVE_THRESHOLD = 75.0

if pct < NMC_THEORY_THRESHOLD:
    raise AttendanceShortfallError(...)

# BAD
if pct < 75:  # Magic number!
    raise ...
```

### TODO Comments

```python
# TODO(2026-Q3): Implement face recognition fallback. SNX-MOB-042
# FIXME: This is a workaround for HIMS API quirk. Remove after HIMS upgrade. SNX-INT-013
# SECURITY: This endpoint requires manual audit before each release. SNX-SEC-008
```

Always include a date or ticket reference.

---

*This document is the source of truth for code style. Pre-commit hooks enforce it. PRs failing checks are rejected.*
