"""
V2.2 — Sources API Endpoint

GET /api/v2/sources/{city_id}?start=YYYY-MM-DD&end=YYYY-MM-DD

Returns article-level intelligence: source breakdown by tier, theme
distribution, top persons, and top organizations.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend_v2.api.deps import get_session
from backend_v2.scoring.source_ranker import get_source_tier
from backend_v2.scoring.theme_codes import describe_theme

router = APIRouter(prefix="/api/v2", tags=["sources"])


# ------------------------------------------------------------------ #
# Response models
# ------------------------------------------------------------------ #

class SourceInfo(BaseModel):
    name: str
    tier: int
    article_count: int
    avg_tone: float
    themes: List[str] = []
    sample_urls: List[str] = []


class ThemeCount(BaseModel):
    theme: str
    count: int


class SourcesResponse(BaseModel):
    city_id: str
    city_name: str
    date_range: dict
    total_articles: int
    sources: List[SourceInfo]
    theme_distribution: List[ThemeCount]
    top_persons: List[str]
    top_organizations: List[str]


# ------------------------------------------------------------------ #
# Route
# ------------------------------------------------------------------ #

@router.get("/sources/{city_id}")
async def get_city_sources(
    city_id: str,
    start: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session),
) -> SourcesResponse:
    # Resolve city name
    name_result = await session.execute(
        text("SELECT name FROM cities WHERE id = :cid"),
        {"cid": city_id},
    )
    name_row = name_result.fetchone()
    city_name = name_row[0] if name_row else "Unknown"

    # Date range defaults
    start_date = date.fromisoformat(start) if start else date(2020, 1, 1)
    end_date = date.fromisoformat(end) if end else date(2030, 1, 1)

    # Fetch articles
    result = await session.execute(
        text("""
            SELECT url, source_name, tone_overall, themes, persons,
                   organizations, word_count, article_date
            FROM city_articles
            WHERE city_id = :cid
              AND article_date >= :s
              AND article_date <= :e
            ORDER BY article_date DESC
        """),
        {"cid": city_id, "s": start_date, "e": end_date},
    )
    rows = result.fetchall()
    total = len(rows)

    # Aggregate by source
    source_data: dict = {}
    theme_counter: Counter = Counter()
    person_counter: Counter = Counter()
    org_counter: Counter = Counter()

    for row in rows:
        url = row[0]
        src = (row[1] or "unknown").lower().strip()
        tone = row[2]
        themes_str = row[3] or ""
        persons_str = row[4] or ""
        orgs_str = row[5] or ""

        if src not in source_data:
            source_data[src] = {
                "tones": [],
                "urls": [],
                "themes": Counter(),
            }
        if tone is not None:
            source_data[src]["tones"].append(tone)
        if url and len(source_data[src]["urls"]) < 3:
            source_data[src]["urls"].append(url)

        for t in themes_str.split(";"):
            t = t.split(",")[0].strip()
            if t:
                theme_counter[t] += 1
                source_data[src]["themes"][t] += 1

        for p in persons_str.split(";"):
            p = p.split(",")[0].strip()
            if p:
                person_counter[p] += 1

        for o in orgs_str.split(";"):
            o = o.split(",")[0].strip()
            if o:
                org_counter[o] += 1

    sources: List[SourceInfo] = []
    for src, data in source_data.items():
        tones = data["tones"]
        avg_tone = sum(tones) / len(tones) if tones else 0.0
        top_src_themes = [
            describe_theme(code)
            for code, _ in data["themes"].most_common(3)
        ]
        sources.append(SourceInfo(
            name=src,
            tier=get_source_tier(src),
            article_count=len(tones),
            avg_tone=round(avg_tone, 2),
            themes=top_src_themes,
            sample_urls=data["urls"],
        ))
    sources.sort(key=lambda s: (s.tier, -s.article_count))

    theme_dist = [
        ThemeCount(theme=describe_theme(code), count=cnt)
        for code, cnt in theme_counter.most_common(20)
    ]

    top_persons = [name for name, _ in person_counter.most_common(15)]
    top_orgs = [name for name, _ in org_counter.most_common(15)]

    return SourcesResponse(
        city_id=city_id,
        city_name=city_name,
        date_range={"start": start_date.isoformat(), "end": end_date.isoformat()},
        total_articles=total,
        sources=sources,
        theme_distribution=theme_dist,
        top_persons=top_persons,
        top_organizations=top_orgs,
    )
