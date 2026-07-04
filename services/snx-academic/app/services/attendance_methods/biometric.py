from .base import AttendanceMethodHandler, MarkingContext, MarkingResult


class BiometricHandler(AttendanceMethodHandler):
    method_name = "biometric"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if not ctx.biometric_hash:
            return MarkingResult(
                success=False,
                method="biometric",
                error_code="ATT-BIO-001",
                error_message="Biometric data missing",
            )
        return MarkingResult(success=True, method="biometric")
