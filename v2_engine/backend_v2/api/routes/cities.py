"""
Phase 4 — Cities API Routes

Endpoints:
  GET /api/v2/cities
      → Returns all cities with id, name, country_code, population,
        latitude (ST_Y), longitude (ST_X).  Powers the globe city points.

  GET /api/v2/cities/scores?date=YYYY-MM-DD
      → Returns the most-recent stability_score per city within 7 days of
        the requested date.  No LLM call — pure TimescaleDB read.
        Used by the globe to colour-code city points reactively.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_v2.api.deps import get_session
from backend_v2.db.timescale_models import DailyCityStats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/cities", tags=["cities"])


# ------------------------------------------------------------------ #
# Response schemas
# ------------------------------------------------------------------ #

class CityRow(BaseModel):
    id: str
    name: str
    country_code: str
    population: int
    latitude: float
    longitude: float


class CityScoreRow(BaseModel):
    city_id: str
    stability_score: float
    day: date


# ------------------------------------------------------------------ #
# GET /api/v2/cities
# ------------------------------------------------------------------ #

@router.get(
    "",
    response_model=list[CityRow],
    summary="List all cities with coordinates",
    description=(
        "Returns up to 2,000 cities ordered by population descending.  "
        "Coordinates are extracted from the PostGIS point geometry via ST_Y/ST_X."
    ),
)
async def list_cities(
    limit: int = Query(default=1000, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
) -> list[CityRow]:
    result = await session.execute(
        text("""
            SELECT
                id::text,
                name,
                country_code,
                population,
                ST_Y(location)::double precision AS latitude,
                ST_X(location)::double precision AS longitude
            FROM cities
            ORDER BY population DESC
            LIMIT :limit
        """),
        {"limit": limit},
    )
    rows = result.fetchall()
    return [
        CityRow(
            id=row.id,
            name=row.name,
            country_code=row.country_code,
            population=row.population,
            latitude=row.latitude,
            longitude=row.longitude,
        )
        for row in rows
    ]


# ------------------------------------------------------------------ #
# GET /api/v2/cities/scores
# ------------------------------------------------------------------ #

@router.get(
    "/scores",
    response_model=list[CityScoreRow],
    summary="Stability scores for all cities near a date",
    description=(
        "Queries daily_city_stats (TimescaleDB) for the most-recent row per "
        "city within 7 days of the requested date.  Returns only cities that "
        "have GDELT data — others should be rendered as neutral (grey) on the globe."
    ),
)
async def get_city_scores(
    date_param: str = Query(
        alias="date",
        description="ISO date YYYY-MM-DD to anchor the 7-day lookback window.",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    window_days: int = Query(
        default=7,
        ge=1,
        le=90,
        description="How many days before `date` to search for the most-recent score.",
    ),
    session: AsyncSession = Depends(get_session),
) -> list[CityScoreRow]:
    try:
        anchor = date.fromisoformat(date_param)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format; use YYYY-MM-DD.")

    cutoff = anchor - timedelta(days=window_days)

    # DISTINCT ON keeps the most-recent row per city within the window.
    # TimescaleDB's chunk exclusion makes this fast even over 5 years of data.
    result = await session.execute(
        text("""
            SELECT DISTINCT ON (city_id)
                city_id::text,
                stability_score,
                day
            FROM daily_city_stats
            WHERE day >= :cutoff
              AND day <= :anchor
            ORDER BY city_id, day DESC
        """),
        {"cutoff": cutoff, "anchor": anchor},
    )
    rows = result.fetchall()
    return [
        CityScoreRow(
            city_id=row.city_id,
            stability_score=row.stability_score,
            day=row.day,
        )
        for row in rows
    ]
