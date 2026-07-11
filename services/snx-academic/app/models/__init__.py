from app.models.academic_year import AcademicYear
from app.models.admissions import AdmissionApplication
from app.models.attendance import (
    Attendance,
    AttendanceAccommodation,
    AttendanceExemption,
    AttendanceSummary,
)
from app.models.batch import Batch
from app.models.calendar import Event, EventCourse, EventFaculty
from app.models.course import Course
from app.models.curriculum import Curriculum
from app.models.curriculum_migration import CurriculumMigrationAudit
from app.models.department import Department
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
    QuestionPaper,
    VivaScore,
)
from app.models.faculty import Faculty
from app.models.leave_request import InternshipRotation, LeaveRequest
from app.models.lesson_plan import LessonPlan
from app.models.program import Program
from app.models.section import Section
from app.models.session import Session, SessionFaculty
from app.models.stubs import LogbookAssessment, MdmConfig, Student, WorkflowInstance
from app.models.tenant import Tenant
from app.models.timetable_entry import TimetableEntry
from app.models.timetable_slot import TimetableSlot
from app.models.user import User

__all__ = [
    "AcademicYear",
    "Program",
    "Curriculum",
    "Course",
    "Batch",
    "Section",
    "TimetableSlot",
    "TimetableEntry",
    "Department",
    "Faculty",
    "User",
    "Tenant",
    "Event",
    "EventFaculty",
    "EventCourse",
    "LessonPlan",
    "Session",
    "SessionFaculty",
    "CurriculumMigrationAudit",
    "Student",
    "WorkflowInstance",
    # Phase 2
    "Attendance",
    "AttendanceSummary",
    "AttendanceExemption",
    "AttendanceAccommodation",
    "LeaveRequest",
    "InternshipRotation",
    "AdmissionApplication",
    # Phase 3
    "Examination",
    "ExamSchedule",
    "VivaScore",
    "PracticalAssessment",
    "ClinicalEvaluation",
    "IAAggregation",
    "ExamEligibility",
    "ExamResult",
    "ExamModeration",
    "MarkSheet",
    "QuestionPaper",
    "MdmConfig",
    "LogbookAssessment",
]
