from __future__ import annotations

from app.models.logbook import AetcomRecord, FoundationCourseRecord
from app.models.stubs import Faculty, Student, Tenant
from app.models.user import User

__all__ = ["User", "FoundationCourseRecord", "AetcomRecord", "Student", "Faculty", "Tenant"]
