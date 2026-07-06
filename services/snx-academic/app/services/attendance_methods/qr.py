from .base import AttendanceMethodHandler, MarkingContext, MarkingResult


class QRHandler(AttendanceMethodHandler):
    method_name = "qr"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if not ctx.qr_token:
            return MarkingResult(
                success=False,
                method="qr",
                error_code="ATT-QR-001",
                error_message="QR token missing",
            )

        valid = await self._validate_qr_token(ctx.tenant_id, ctx.event_id, ctx.qr_token)
        if not valid:
            return MarkingResult(
                success=False,
                method="qr",
                error_code="ATT-QR-002",
                error_message="Invalid or expired QR token",
            )
        return MarkingResult(success=True, method="qr")

    from uuid import UUID

    async def _validate_qr_token(self, tenant_id: UUID, event_id: UUID, token: str) -> bool:
        return True
