"""
Score Delta Calculator

Compares the current analysis period to the previous period of equal length,
computing deltas for overall score, event volume, article tone, and
dominant themes.  This enables the evaluator to explain WHY scores changed.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import date, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .theme_codes import describe_theme

logger = logging.getLogger(__name__)


class ScoreDeltas(BaseModel):
    """Period-over-period deltas used by the evaluator for causal attribution."""
    previous_overall: Optional[float] = None
    current_overall: float = 50.0
    overall_delta: Optional[float] = None
    dimension_deltas: Dict[str, float] = {}
    event_volume_change: Optional[float] = None
    tone_shift: Optional[float] = None
    new_themes: List[str] = []
    disappeared_themes: List[str] = []


async def calculate_deltas(
    city_id: str,
    current_date: str,
    window_days: int,
    session: AsyncSession,
) -> ScoreDeltas:
    """
    Compare current period to previous period (each window_days long).

    Example: current_date=2024-01-15, window_days=30
      - Current:  Dec 16 2023 - Jan 15 2024
      - Previous: Nov 16 2023 - Dec 15 2023

    Queries daily_city_stats and city_articles for both windows.
    """
    ref = date.fromisoformat(current_date) if isinstance(current_date, str) else current_date
    curr_start = ref - timedelta(days=window_days)
    curr_end = ref
    prev_start = curr_start - timedelta(days=window_days)
    prev_end = curr_start - timedelta(days=1)

    curr_stats = await _window_stats(session, city_id, curr_start, curr_end)
    prev_stats = await _window_stats(session, city_id, prev_start, prev_end)

    result = ScoreDeltas()

    if curr_stats:
        result.current_overall = curr_stats["avg_stability"]
    if prev_stats:
        result.previous_overall = prev_stats["avg_stability"]
    if result.previous_overall is not None:
        result.overall_delta = result.current_overall - result.previous_overall

    # Event volume change (percentage)
    if prev_stats and prev_stats["total_events"] > 0 and curr_stats:
        pct = ((curr_stats["total_events"] - prev_stats["total_events"])
               / prev_stats["total_events"]) * 100.0
        result.event_volume_change = round(pct, 1)

    # Tone shift from city_articles
    curr_tone = await _window_avg_tone(session, city_id, curr_start, curr_end)
    prev_tone = await _window_avg_tone(session, city_id, prev_start, prev_end)
    if curr_tone is not None and prev_tone is not None:
        result.tone_shift = round(curr_tone - prev_tone, 2)

    # Theme comparison from city_articles
    curr_themes = await _window_themes(session, city_id, curr_start, curr_end)
    prev_themes = await _window_themes(session, city_id, prev_start, prev_end)
    curr_set = set(curr_themes.keys())
    prev_set = set(prev_themes.keys())
    result.new_themes = [
        describe_theme(t) for t in sorted(curr_set - prev_set)
    ][:10]
    result.disappeared_themes = [
        describe_theme(t) for t in sorted(prev_set - curr_set)
    ][:10]

    return result


# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #

async def _window_stats(
    session: AsyncSession,
    city_id: str,
    start: date,
    end: date,
) -> Optional[dict]:
    """Aggregate daily_city_stats for a window."""
    result = await session.execute(
        text("""
            SELECT
                COALESCE(AVG(stability_score), 50.0) AS avg_stability,
                COALESCE(SUM(event_count), 0) AS total_events,
                COALESCE(AVG(avg_goldstein), 0.0) AS avg_goldstein,
                COUNT(*) AS day_count
            FROM daily_city_stats
            WHERE city_id = :cid
              AND day >= :s
              AND day <= :e
        """),
        {"cid": city_id, "s": start, "e": end},
    )
    row = result.fetchone()
    if row is None or row[3] == 0:
        return None
    return {
        "avg_stability": float(row[0]),
        "total_events": int(row[1]),
        "avg_goldstein": float(row[2]),
        "day_count": int(row[3]),
    }


async def _window_avg_tone(
    session: AsyncSession,
    city_id: str,
    start: date,
    end: date,
) -> Optional[float]:
    """Average overall tone from city_articles for a window."""
    try:
        result = await session.execute(
            text("""
                SELECT AVG(tone_overall)
                FROM city_articles
                WHERE city_id = :cid
                  AND article_date >= :s
                  AND article_date <= :e
            """),
            {"cid": city_id, "s": start, "e": end},
        )
        row = result.fetchone()
        if row and row[0] is not None:
            return float(row[0])
    except Exception:
        # city_articles table may not exist yet
        logger.debug("city_articles not available for tone query")
    return None


async def _window_themes(
    session: AsyncSession,
    city_id: str,
    start: date,
    end: date,
) -> Counter:
    """Count theme occurrences across city_articles for a window."""
    counts: Counter = Counter()
    try:
        result = await session.execute(
            text("""
                SELECT themes
                FROM city_articles
                WHERE city_id = :cid
                  AND article_date >= :s
                  AND article_date <= :e
                  AND themes IS NOT NULL
            """),
            {"cid": city_id, "s": start, "e": end},
        )
        for row in result.fetchall():
            themes_str = row[0]
            if themes_str:
                for theme in themes_str.split(";"):
                    theme = theme.strip()
                    if theme:
                        counts[theme] += 1
    except Exception:
        logger.debug("city_articles not available for theme query")
    return counts
