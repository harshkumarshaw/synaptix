import os

base_dir = r'f:\Synaptix\services\snx-academic\app\services\attendance_methods'
files = {
    '__init__.py': '\"\"\"Attendance method handlers — one per marking method.\"\"\"',
    'base.py': '''from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

@dataclass
class MarkingContext:
    tenant_id: UUID
    student_id: UUID
    event_id: UUID
    session_id: UUID | None
    device_id: str | None
    geo_lat: float | None
    geo_lng: float | None
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
    def method_name(self) -> str:
        ...

    @abstractmethod
    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        ...
''',
    'manual.py': '''from .base import AttendanceMethodHandler, MarkingContext, MarkingResult

class ManualHandler(AttendanceMethodHandler):
    method_name = \"manual\"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        return MarkingResult(success=True, method=\"manual\")
''',
    'qr.py': '''from .base import AttendanceMethodHandler, MarkingContext, MarkingResult

class QRHandler(AttendanceMethodHandler):
    method_name = \"qr\"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if not ctx.qr_token:
            return MarkingResult(success=False, method=\"qr\", error_code=\"ATT-QR-001\", error_message=\"QR token missing\")
        
        valid = await self._validate_qr_token(ctx.tenant_id, ctx.event_id, ctx.qr_token)
        if not valid:
            return MarkingResult(success=False, method=\"qr\", error_code=\"ATT-QR-002\", error_message=\"Invalid or expired QR token\")
        return MarkingResult(success=True, method=\"qr\")

    async def _validate_qr_token(self, tenant_id, event_id, token) -> bool:
        return True
''',
    'rfid.py': '''from .base import AttendanceMethodHandler, MarkingContext, MarkingResult

class RFIDHandler(AttendanceMethodHandler):
    method_name = \"rfid\"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if not ctx.rfid_card_id:
            return MarkingResult(success=False, method=\"rfid\", error_code=\"ATT-RFID-001\", error_message=\"RFID card ID missing\")
        return MarkingResult(success=True, method=\"rfid\", needs_review=False)
''',
    'gps.py': '''from .base import AttendanceMethodHandler, MarkingContext, MarkingResult

class GPSHandler(AttendanceMethodHandler):
    method_name = \"gps\"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if ctx.geo_lat is None or ctx.geo_lng is None:
            return MarkingResult(success=False, method=\"gps\", error_code=\"ATT-GPS-001\", error_message=\"GPS coordinates missing\")
        
        in_fence = await self._check_geofence(ctx.tenant_id, ctx.geo_lat, ctx.geo_lng)
        return MarkingResult(success=True, method=\"gps\", needs_review=not in_fence)

    async def _check_geofence(self, tenant_id, lat, lng) -> bool:
        return True
''',
    'biometric.py': '''from .base import AttendanceMethodHandler, MarkingContext, MarkingResult

class BiometricHandler(AttendanceMethodHandler):
    method_name = \"biometric\"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if not ctx.biometric_hash:
            return MarkingResult(success=False, method=\"biometric\", error_code=\"ATT-BIO-001\", error_message=\"Biometric data missing\")
        return MarkingResult(success=True, method=\"biometric\")
''',
    'registry.py': '''from .manual import ManualHandler
from .qr import QRHandler
from .rfid import RFIDHandler
from .gps import GPSHandler
from .biometric import BiometricHandler
from .base import AttendanceMethodHandler

HANDLERS: dict[str, AttendanceMethodHandler] = {
    \"manual\": ManualHandler(),
    \"qr\": QRHandler(),
    \"rfid\": RFIDHandler(),
    \"gps\": GPSHandler(),
    \"biometric\": BiometricHandler(),
    \"face\": BiometricHandler(),
}

def get_handler(method: str) -> AttendanceMethodHandler:
    handler = HANDLERS.get(method)
    if not handler:
        raise ValueError(f\"Unknown attendance method: {method}\")
    return handler
'''
}

for name, content in files.items():
    with open(os.path.join(base_dir, name), 'w', encoding='utf-8') as f:
        f.write(content)
