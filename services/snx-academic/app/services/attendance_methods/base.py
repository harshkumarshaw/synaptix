from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass
class MarkingContext:
    tenant_id: UUID
    student_id: UUID
    event_id: UUID
    session_id: UUID | None
    device_id: str | None
    geo_lat: Decimal | None
    geo_lng: Decimal | None
    qr_token: str | None
    rfid_card_id: str | None
    biometric_hash: str | None


@dataclass
class MarkingResult:
    success: bool
    method: str
    error_code: str | None = None
    error_message: str | None = None
    needs_review: bool = False


class AttendanceMethodHandler(ABC):
    @property
    @abstractmethod
    def method_name(self) -> str: ...

    @abstractmethod
    async def validate(self, ctx: MarkingContext) -> MarkingResult: ...
