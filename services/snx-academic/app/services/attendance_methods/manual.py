from .base import AttendanceMethodHandler, MarkingContext, MarkingResult


class ManualHandler(AttendanceMethodHandler):
    method_name = "manual"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        return MarkingResult(success=True, method="manual")
