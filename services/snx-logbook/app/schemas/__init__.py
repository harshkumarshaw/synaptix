from __future__ import annotations

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

from app.schemas.doap import (
    DoapSessionCreate,
    DoapSessionResponse,
    DoapStateResponse,
    DoapProgressionResponse,
)

__all__ = [
    # Logbook / Foundation / AETCOM
    "FoundationCourseRecordResponse",
    "FoundationCourseHoursLog",
    "FoundationCourseSignoffPayload",
    "AetcomReflectionSubmit",
    "AetcomSignoffPayload",
    "AetcomRecordResponse",
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

