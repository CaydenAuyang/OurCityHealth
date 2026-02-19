"""
District GeoJSON endpoint — returns district boundaries for a city
as a standard GeoJSON FeatureCollection.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend_v2.api.deps import get_session

router = APIRouter(prefix="/api/v2", tags=["districts"])


@router.get("/cities/{city_id}/districts")
async def get_city_districts(
    city_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        text(
            "SELECT d.id::text, d.name, ST_AsGeoJSON(d.boundary) AS geojson "
            "FROM districts d WHERE d.city_id = :cid"
        ),
        {"cid": city_id},
    )
    rows = result.fetchall()

    features = []
    for row in rows:
        features.append(
            {
                "type": "Feature",
                "properties": {"name": row[1], "district_id": row[0]},
                "geometry": json.loads(row[2]),
            }
        )

    return {"type": "FeatureCollection", "features": features}
