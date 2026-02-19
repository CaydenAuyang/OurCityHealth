"""
V2.1 — Events API Route

Endpoint:
  GET /api/v2/events/{city_id}?start=YYYY-MM-DD&end=YYYY-MM-DD&limit=50
      → Returns raw GDELT events from the city_events table with
        CAMEO human-readable descriptions included.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_v2.api.deps import get_session
from backend_v2.db.models import City
from backend_v2.db.timescale_models import CityEvent
from backend_v2.scoring.cameo_codes import describe_event_code

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/events", tags=["events"])


# ------------------------------------------------------------------ #
# Response schemas
# ------------------------------------------------------------------ #

class EventWithDescription(BaseModel):
    date: str
    actor1: Optional[str] = None
    actor2: Optional[str] = None
    event_code: Optional[str] = None
    event_description: str
    goldstein_scale: Optional[float] = None
    num_mentions: Optional[int] = None
    source_url: Optional[str] = None


class EventResponse(BaseModel):
    city_id: str
    city_name: str
    events: list[EventWithDescription]


# ------------------------------------------------------------------ #
# GET /api/v2/events/{city_id}
# ------------------------------------------------------------------ #

@router.get(
    "/{city_id}",
    response_model=EventResponse,
    summary="Raw GDELT events with CAMEO descriptions",
    description=(
        "Returns individual GDELT events from the city_events table, "
        "enriched with human-readable CAMEO event descriptions.  "
        "Ordered by event_date descending (most recent first)."
    ),
)
async def get_city_events(
    city_id: str,
    start: Optional[str] = Query(
        default=None,
        description="Start date YYYY-MM-DD (defaults to 90 days ago).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    end: Optional[str] = Query(
        default=None,
        description="End date YYYY-MM-DD (defaults to today UTC).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of events to return.",
    ),
    session: AsyncSession = Depends(get_session),
) -> EventResponse:
    # Validate city exists
    from uuid import UUID as UUIDType
    try:
        uid = UUIDType(city_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="city_id must be a valid UUID.")

    result = await session.execute(
        select(City).where(City.id == uid)
    )
    city = result.scalar_one_or_none()
    if city is None:
        raise HTTPException(status_code=404, detail=f"City '{city_id}' not found.")

    # Date defaults
    from datetime import datetime, timezone as tz
    today = datetime.now(tz.utc).date()
    end_date = date.fromisoformat(end) if end else today
    start_date = date.fromisoformat(start) if start else end_date - timedelta(days=90)

    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start must be before end.")

    # Query events
    result = await session.execute(
        select(CityEvent)
        .where(CityEvent.city_id == city_id)
        .where(CityEvent.event_date >= start_date)
        .where(CityEvent.event_date <= end_date)
        .order_by(CityEvent.event_date.desc())
        .limit(limit)
    )
    raw = result.scalars().all()

    events = [
        EventWithDescription(
            date=ev.event_date.isoformat(),
            actor1=ev.actor1,
            actor2=ev.actor2,
            event_code=ev.event_code,
            event_description=describe_event_code(ev.event_code or ""),
            goldstein_scale=ev.goldstein_scale,
            num_mentions=ev.num_mentions,
            source_url=ev.source_url,
        )
        for ev in raw
    ]

    return EventResponse(
        city_id=str(city.id),
        city_name=city.name,
        events=events,
    )
