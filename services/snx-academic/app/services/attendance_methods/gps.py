from .base import AttendanceMethodHandler, MarkingContext, MarkingResult


class GPSHandler(AttendanceMethodHandler):
    method_name = "gps"

    async def validate(self, ctx: MarkingContext) -> MarkingResult:
        if ctx.geo_lat is None or ctx.geo_lng is None:
            return MarkingResult(
                success=False,
                method="gps",
                error_code="ATT-GPS-001",
                error_message="GPS coordinates missing",
            )

        in_fence = await self._check_geofence(ctx.tenant_id, ctx.geo_lat, ctx.geo_lng)
        return MarkingResult(success=True, method="gps", needs_review=not in_fence)

    from decimal import Decimal
    from uuid import UUID

    async def _check_geofence(self, tenant_id: UUID, lat: Decimal, lng: Decimal) -> bool:
        return True
