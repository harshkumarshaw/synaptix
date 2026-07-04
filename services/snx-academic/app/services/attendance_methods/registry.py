from .base import AttendanceMethodHandler
from .biometric import BiometricHandler
from .gps import GPSHandler
from .manual import ManualHandler
from .qr import QRHandler
from .rfid import RFIDHandler

HANDLERS: dict[str, AttendanceMethodHandler] = {
    "manual": ManualHandler(),
    "qr": QRHandler(),
    "rfid": RFIDHandler(),
    "gps": GPSHandler(),
    "biometric": BiometricHandler(),
    "face": BiometricHandler(),
}


def get_handler(method: str) -> AttendanceMethodHandler:
    handler = HANDLERS.get(method)
    if not handler:
        raise ValueError(f"Unknown attendance method: {method}")
    return handler
