from __future__ import annotations

from app.schemas.doap import (
    DoapProgressionResponse,
    DoapSessionCreate,
    DoapSessionResponse,
    DoapStateResponse,
)
from app.schemas.electives import (
    AllocationResponse,
    AllocationRunRequest,
    AllocationRunResponse,
    ElectiveCreate,
    ElectiveResponse,
    PreferenceResponse,
    PreferencesSubmitRequest,
)
from app.schemas.logbook import (
    AetcomRecordResponse,
    AetcomReflectionSubmit,
    AetcomSignoffPayload,
    FoundationCourseHoursLog,
    FoundationCourseRecordResponse,
    FoundationCourseSignoffPayload,
)
from app.schemas.logbook_phase2 import (
    LogbookEntryCreate,
    LogbookEntryResponse,
    LogbookSignoffRequest,
    LogbookEntrySubmitRequest,
    LogbookAssessmentResponse,
    IAMarksCalculation,
)

__all__ = [
    # Logbook / Foundation / AETCOM
    "FoundationCourseRecordResponse",
    "FoundationCourseHoursLog",
    "FoundationCourseSignoffPayload",
    "AetcomReflectionSubmit",
    "AetcomSignoffPayload",
    "AetcomRecordResponse",
    # Phase 2
    "LogbookEntryCreate",
    "LogbookEntryResponse",
    "LogbookSignoffRequest",
    "LogbookEntrySubmitRequest",
    "LogbookAssessmentResponse",
    "IAMarksCalculation",
    # Electives
    "ElectiveCreate",
    "ElectiveResponse",
    "PreferencesSubmitRequest",
    "PreferenceResponse",
    "AllocationRunRequest",
    "AllocationRunResponse",
    "AllocationResponse",
    # DOAP
    "DoapSessionCreate",
    "DoapSessionResponse",
    "DoapStateResponse",
    "DoapProgressionResponse",
]

