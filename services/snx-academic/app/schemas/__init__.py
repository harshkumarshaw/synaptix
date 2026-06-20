from app.schemas.academic import (
    ProgramResponse,
    CourseResponse,
    BatchResponse,
    TimetableSlotResponse,
    TimetableEntryResponse,
)
from app.schemas.calendar import (
    EventCreate,
    EventUpdate,
    EventResponse,
)
from app.schemas.lesson_plan import (
    LessonPlanCreate,
    LessonPlanUpdate,
    LessonPlanResponse,
)
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
)
from app.schemas.curriculum_migration import (
    CurriculumMigrationAuditCreate,
    CurriculumMigrationAuditResponse,
)

__all__ = [
    "ProgramResponse",
    "CourseResponse",
    "BatchResponse",
    "TimetableSlotResponse",
    "TimetableEntryResponse",
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "LessonPlanCreate",
    "LessonPlanUpdate",
    "LessonPlanResponse",
    "SessionCreate",
    "SessionResponse",
    "CurriculumMigrationAuditCreate",
    "CurriculumMigrationAuditResponse",
]
