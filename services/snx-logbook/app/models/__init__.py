from __future__ import annotations

from app.models.electives import Elective, ElectiveAllocation, StudentElectivePreference
from app.models.logbook import AetcomRecord, FoundationCourseRecord
from app.models.logbook_phase2 import DoapSessionRecord, LogbookAssessment, LogbookEntry
from app.models.stubs import Faculty, Student, Tenant, WorkflowInstance, WorkflowDefinition
from app.models.user import User

__all__ = [
    "User",
    "FoundationCourseRecord",
    "AetcomRecord",
    "Student",
    "Faculty",
    "Tenant",
    "WorkflowInstance",
    "WorkflowDefinition",
    # Phase 2
    "Elective",
    "ElectiveAllocation",
    "StudentElectivePreference",
    "LogbookEntry",
    "LogbookAssessment",
    "DoapSessionRecord",
]


