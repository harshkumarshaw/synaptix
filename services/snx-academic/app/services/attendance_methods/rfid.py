from .base import AttendanceMethodHandler, MarkingContext, MarkingResult


class RFIDHandler(AttendanceMethodHandler):
    method_name = "rfid"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if not ctx.rfid_card_id:
            return MarkingResult(
                success=False,
                method="rfid",
                error_code="ATT-RFID-001",
                error_message="RFID card ID missing",
            )
        return MarkingResult(success=True, method="rfid", needs_review=False)
