from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import text

from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload
from packages.shared.db.session import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
)
async def get_dashboard_stats(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    db=Depends(get_db),
) -> dict:
    """Fetch aggregated dashboard analytics for the current tenant."""
    # 1. Total students
    res = await db.execute(text("SELECT COUNT(*) FROM students"))
    total_students = res.scalar() or 0

    # 2. Today's attendance rate
    res = await db.execute(
        text(
            "SELECT AVG(CASE WHEN status='present' THEN 100.0 ELSE 0.0 END) FROM attendance WHERE marked_at::date = CURRENT_DATE"
        )
    )
    todays_rate = res.scalar()
    if todays_rate is None:
        # Fallback to overall rate if no attendance marked today
        res = await db.execute(
            text("SELECT AVG(CASE WHEN status='present' THEN 100.0 ELSE 0.0 END) FROM attendance")
        )
        todays_rate = res.scalar() or 0.0

    # 3. Pending logbook reviews
    try:
        res = await db.execute(
            text("SELECT COUNT(*) FROM logbook_entries WHERE status = 'submitted'")
        )
        pending_reviews = res.scalar() or 0
    except Exception:
        pending_reviews = 0

    # 4. At risk students
    try:
        res = await db.execute(
            text(
                "SELECT COUNT(DISTINCT student_id) FROM attendance_summary WHERE attendance_pct < 75.00"
            )
        )
        at_risk = res.scalar() or 0
    except Exception:
        at_risk = 0

    return {
        "total_students": total_students,
        "todays_attendance_rate": round(float(todays_rate), 2),
        "pending_logbook_reviews": pending_reviews,
        "at_risk_students": at_risk,
    }
