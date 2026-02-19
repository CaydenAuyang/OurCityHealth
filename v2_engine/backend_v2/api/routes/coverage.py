"""
Data-coverage endpoint — returns which dates have GDELT data
and how many cities are represented per date.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend_v2.api.deps import get_session

router = APIRouter(prefix="/api/v2", tags=["coverage"])


class CoverageDay(BaseModel):
    date: str
    city_count: int


class CoverageResponse(BaseModel):
    coverage: List[CoverageDay]
    min_date: str
    max_date: str


@router.get("/data-coverage", response_model=CoverageResponse)
async def get_data_coverage(
    session: AsyncSession = Depends(get_session),
) -> CoverageResponse:
    result = await session.execute(
        text(
            "SELECT day::date AS date, COUNT(DISTINCT city_id) AS city_count "
            "FROM daily_city_stats "
            "GROUP BY day::date "
            "ORDER BY date"
        )
    )
    rows = result.fetchall()

    if not rows:
        return CoverageResponse(coverage=[], min_date="", max_date="")

    coverage = [
        CoverageDay(date=str(r[0]), city_count=int(r[1]))
        for r in rows
    ]
    return CoverageResponse(
        coverage=coverage,
        min_date=coverage[0].date,
        max_date=coverage[-1].date,
    )
