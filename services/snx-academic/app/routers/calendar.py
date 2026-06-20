from __future__ import annotations

import uuid
import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException

from packages.shared.auth.dependencies import get_current_user
from packages.shared.auth.jwt import TokenPayload
from packages.shared.errors import ResourceNotFoundError
from app.schemas.calendar import EventCreate, EventResponse, EventUpdate
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a scheduled academic event",
)
async def create_event(
    event_in: EventCreate,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(CalendarService)],
) -> EventResponse:
    try:
        event = await service.create_event(
            tenant_id=current_user.tenant_uuid,
            event_in=event_in,
            actor_id=current_user.user_uuid
        )
        # Fetch event with populated relations
        full_event = await service.get_event(current_user.tenant_uuid, event.id)
        return full_event
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an event by ID",
)
async def get_event(
    event_id: uuid.UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(CalendarService)],
) -> EventResponse:
    event = await service.get_event(current_user.tenant_uuid, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found."
        )
    return event


@router.post(
    "/{event_id}/cancel",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel a scheduled event",
)
async def cancel_event(
    event_id: uuid.UUID,
    payload: dict,  # {"reason": "string"}
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(CalendarService)],
) -> EventResponse:
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(status_code=400, detail="reason is required to cancel an event.")
    
    event = await service.cancel_event(
        tenant_id=current_user.tenant_uuid,
        event_id=event_id,
        reason=reason,
        actor_id=current_user.user_uuid
    )
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    
    # Reload with relations
    return await service.get_event(current_user.tenant_uuid, event.id)


@router.post(
    "/{event_id}/reschedule",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Reschedule an event",
)
async def reschedule_event(
    event_id: uuid.UUID,
    payload: dict,  # {"date": "YYYY-MM-DD", "start_time": "HH:MM", "end_time": "HH:MM"}
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(CalendarService)],
) -> EventResponse:
    try:
        new_date = datetime.datetime.strptime(payload["date"], "%Y-%m-%d").date()
        new_start = datetime.datetime.strptime(payload["start_time"], "%H:%M:%S" if len(payload["start_time"]) > 5 else "%H:%M").time()
        new_end = datetime.datetime.strptime(payload["end_time"], "%H:%M:%S" if len(payload["end_time"]) > 5 else "%H:%M").time()
    except (KeyError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date or time formats. Required format: date: YYYY-MM-DD, start_time: HH:MM, end_time: HH:MM"
        )

    try:
        new_event = await service.reschedule_event(
            tenant_id=current_user.tenant_uuid,
            event_id=event_id,
            new_date=new_date,
            new_start=new_start,
            new_end=new_end,
            actor_id=current_user.user_uuid
        )
        return await service.get_event(current_user.tenant_uuid, new_event.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
