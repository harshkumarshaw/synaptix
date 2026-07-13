from app.schemas.academic import (
    BatchResponse,
    CourseResponse,
    ProgramResponse,
    TimetableEntryResponse,
    TimetableSlotResponse,
)
from app.schemas.admissions import (
    AdmissionApplicationCreate,
    AdmissionApplicationResponse,
)
from app.schemas.calendar import (
    EventCreate,
    EventResponse,
    EventUpdate,
)
from app.schemas.curriculum_migration import (
    CurriculumMigrationAuditCreate,
    CurriculumMigrationAuditResponse,
)
from app.schemas.exam import (
    EligibilityOverrideRequest,
    ExamEligibilityResponse,
    ExaminationCreate,
    ExaminationResponse,
    ExamScheduleCreate,
    ExamScheduleResponse,
    IAAggregationRequest,
    IAAggregationResponse,
)
from app.schemas.lesson_plan import (
    LessonPlanCreate,
    LessonPlanResponse,
    LessonPlanUpdate,
)
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
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
    "AdmissionApplicationCreate",
    "AdmissionApplicationResponse",
    "ExaminationCreate",
    "ExaminationResponse",
    "ExamScheduleCreate",
    "ExamScheduleResponse",
    "IAAggregationRequest",
    "IAAggregationResponse",
    "ExamEligibilityResponse",
    "EligibilityOverrideRequest",
]
