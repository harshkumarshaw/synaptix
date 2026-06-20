from app.models.academic_year import AcademicYear
from app.models.program import Program
from app.models.curriculum import Curriculum
from app.models.course import Course
from app.models.batch import Batch
from app.models.section import Section
from app.models.timetable_slot import TimetableSlot
from app.models.timetable_entry import TimetableEntry
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.user import User
from app.models.tenant import Tenant

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
]
