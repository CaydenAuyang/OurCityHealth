"""
Phase 3 — Scoring API Routes

Endpoints:
  GET /api/v2/score/{city_id}?date=YYYY-MM-DD
      → Checks city_scores table first (sub-second).  Falls back to live
        GPT-4o pipeline if no pre-computed score exists, then persists the
        result for future requests.
      → Redis sits on top as a hot cache; Postgres is the durable store.

  GET /api/v2/score/{city_id}/history?start=YYYY-MM-DD&end=YYYY-MM-DD&limit=365
      → Returns raw daily_city_stats rows from TimescaleDB — no LLM call.

  GET /api/v2/score/{city_id}/dimensions?start=YYYY-MM-DD&end=YYYY-MM-DD
      → Returns pre-computed dimension snapshots over time from city_scores.

Both endpoints require a valid city UUID that exists in the cities table.
A 404 is returned for unknown city IDs to prevent information leakage.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend_v2.db.models import City
from backend_v2.db.session import async_session_factory
from backend_v2.db.timescale_models import CityScore
from backend_v2.scoring.aggregator import ScoreAggregator
from backend_v2.scoring.evaluator import ScoreEvaluator
from backend_v2.scoring.schemas import CityHealthScore, DailyStatsRow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/score", tags=["scoring"])


async def get_session() -> AsyncSession:
    """
    Plain async generator dependency — compatible with Python 3.9 + FastAPI.

    Using @asynccontextmanager on get_db() in session.py produces an
    _AsyncGeneratorContextManager, which FastAPI's dependency injector cannot
    iterate with __anext__ on Python 3.9.  A bare async generator (this
    function) is what FastAPI expects: it calls __anext__ once to get the
    yielded value and once more to run cleanup.
    """
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# ------------------------------------------------------------------ #
# Module-level evaluator (re-used across requests, shares HTTP pool)
# ------------------------------------------------------------------ #

_evaluator: Optional[ScoreEvaluator] = None


def _get_evaluator() -> ScoreEvaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = ScoreEvaluator(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            max_retries=int(os.environ.get("SCORING_MAX_RETRIES", "3")),
        )
    return _evaluator


# ------------------------------------------------------------------ #
# Optional Redis cache helper
# ------------------------------------------------------------------ #

def _get_redis():
    """Return a redis.Redis client or None if Redis is unavailable."""
    try:
        import redis as redis_lib
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6380/0")
        client = redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=2)
        client.ping()
        return client
    except Exception:
        logger.warning("Redis unavailable — scores will not be cached.")
        return None


def _cache_key(city_id: str, scored_date: date) -> str:
    return f"v2:score:{city_id}:{scored_date.isoformat()}"


# ------------------------------------------------------------------ #
# Postgres persistent score helpers
# ------------------------------------------------------------------ #

async def _load_pg_score(
    session: AsyncSession, city_id: str, scored_date: date,
) -> Optional[CityHealthScore]:
    """Return a pre-computed score from city_scores, or None."""
    result = await session.execute(
        select(CityScore).where(
            CityScore.city_id == city_id,
            CityScore.scored_date == scored_date,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    try:
        return CityHealthScore.model_validate_json(row.score_json)
    except Exception:
        logger.warning("Corrupt score_json for %s / %s — ignoring", city_id, scored_date)
        return None


async def _persist_pg_score(
    session: AsyncSession,
    city_id: str,
    city_name: str,
    scored_date: date,
    score: CityHealthScore,
    model: str = "gpt-4o",
) -> None:
    """Store a score in city_scores.  Silently skips on conflict."""
    try:
        await session.execute(
            text("""
                INSERT INTO city_scores
                    (city_id, city_name, scored_date, overall_score,
                     overall_confidence, score_json, model_used)
                VALUES (:cid, :cname, :sd, :os, :oc, :sj, :mu)
                ON CONFLICT (city_id, scored_date) DO NOTHING
            """),
            {
                "cid": city_id,
                "cname": city_name,
                "sd": scored_date,
                "os": float(score.overall_score),
                "oc": float(score.overall_confidence),
                "sj": score.model_dump_json(),
                "mu": model,
            },
        )
        await session.commit()
    except Exception as exc:
        logger.warning("Failed to persist score to city_scores: %s", exc)
        await session.rollback()


# ------------------------------------------------------------------ #
# Lookup helper
# ------------------------------------------------------------------ #

async def _get_city_or_404(city_id: str, session: AsyncSession) -> City:
    try:
        uid = UUID(city_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="city_id must be a valid UUID.")

    result = await session.execute(select(City).where(City.id == uid))
    city = result.scalar_one_or_none()
    if city is None:
        raise HTTPException(status_code=404, detail=f"City '{city_id}' not found.")
    return city


# ------------------------------------------------------------------ #
# GET /api/v2/score/{city_id}
# ------------------------------------------------------------------ #

@router.get(
    "/{city_id}",
    response_model=CityHealthScore,
    summary="Score a city for a given date",
    description=(
        "Runs the deterministic scoring pipeline: pulls GDELT data from TimescaleDB, "
        "applies recency weighting, then forces the LLM (temp=0) to emit a validated "
        "CityHealthScore.  Responses are cached in Redis for 6 hours."
    ),
)
async def get_city_score(
    city_id: str,
    date_param: Optional[str] = Query(
        default=None,
        alias="date",
        description="ISO date string YYYY-MM-DD.  Defaults to today (UTC).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    lookback_days: int = Query(
        default=180,
        ge=7,
        le=1825,
        description="How many days of GDELT history to consider when scoring.",
    ),
    half_life_days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Recency decay half-life in days.",
    ),
    session: AsyncSession = Depends(get_session),
) -> CityHealthScore:
    scored_date = (
        date.fromisoformat(date_param)
        if date_param
        else datetime.now(timezone.utc).date()
    )

    city = await _get_city_or_404(city_id, session)

    # --- 1. Persistent Postgres lookup (sub-millisecond) ---
    pg_score = await _load_pg_score(session, city_id, scored_date)
    if pg_score is not None:
        logger.info("PG score hit for %s / %s", city.name, scored_date)
        return pg_score

    # --- 2. Redis hot-cache check ---
    redis = _get_redis()
    cache_key = _cache_key(city_id, scored_date)
    if redis:
        cached = redis.get(cache_key)
        if cached:
            logger.info("Redis cache hit for %s / %s", city.name, scored_date)
            score = CityHealthScore.model_validate_json(cached)
            await _persist_pg_score(
                session, city_id, city.name, scored_date, score,
            )
            return score

    # --- 3. Live scoring pipeline (GPT-4o) ---
    aggregator = ScoreAggregator(
        session,
        half_life_days=half_life_days,
        lookback_days=lookback_days,
    )

    try:
        ctx = await aggregator.get_enriched_context(
            city_id=str(city.id),
            city_name=city.name,
            country_code=city.country_code,
            scored_date=scored_date,
            window_days=lookback_days,
        )
    except Exception:
        logger.warning(
            "Enriched context failed for %s — falling back to aggregate context",
            city.name,
            exc_info=True,
        )
        try:
            ctx = await aggregator.build_context(
                city_id=city.id,
                city_name=city.name,
                country_code=city.country_code,
                scored_date=scored_date,
            )
        except Exception as exc:
            logger.error("Aggregator failed for %s: %s", city.name, exc)
            raise HTTPException(status_code=500, detail=f"Aggregation error: {exc}")

    evaluator = _get_evaluator()
    try:
        score = evaluator.calculate_score(ctx)
    except Exception as exc:
        logger.error(
            "Scoring failed for %s/%s after retries: %s",
            city.name,
            scored_date,
            exc,
        )
        raise HTTPException(
            status_code=502,
            detail=(
                f"LLM scoring failed after retries: {exc}.  "
                "Validation errors are logged server-side."
            ),
        )

    # --- 4. Persist to Postgres + Redis ---
    await _persist_pg_score(
        session, city_id, city.name, scored_date, score,
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
    )
    if redis:
        try:
            redis.set(cache_key, score.model_dump_json(), ex=6 * 3600)
        except Exception as cache_exc:
            logger.warning("Failed to write Redis cache: %s", cache_exc)

    return score


# ------------------------------------------------------------------ #
# GET /api/v2/score/{city_id}/history
# ------------------------------------------------------------------ #

@router.get(
    "/{city_id}/history",
    response_model=list[DailyStatsRow],
    summary="Raw daily GDELT statistics history",
    description=(
        "Returns raw daily_city_stats rows from the TimescaleDB hypertable.  "
        "No LLM call is made — this is a fast time-series read."
    ),
)
async def get_city_history(
    city_id: str,
    start: Optional[str] = Query(
        default=None,
        description="Start date YYYY-MM-DD (defaults to 365 days ago).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    end: Optional[str] = Query(
        default=None,
        description="End date YYYY-MM-DD (defaults to today UTC).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    limit: int = Query(
        default=365,
        ge=1,
        le=1825,
        description="Maximum number of rows to return.",
    ),
    session: AsyncSession = Depends(get_session),
) -> list[DailyStatsRow]:
    city = await _get_city_or_404(city_id, session)

    today = datetime.now(timezone.utc).date()
    end_date = date.fromisoformat(end) if end else today
    start_date = date.fromisoformat(start) if start else end_date - timedelta(days=365)

    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start must be before end.")

    aggregator = ScoreAggregator(session)
    rows = await aggregator.fetch_history(
        city_id=str(city.id),
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No GDELT history found for '{city.name}' "
                f"between {start_date} and {end_date}."
            ),
        )

    return rows


# ------------------------------------------------------------------ #
# GET /api/v2/score/{city_id}/dimensions
# ------------------------------------------------------------------ #

@router.get(
    "/{city_id}/dimensions",
    summary="Pre-computed dimension snapshots over time",
    description=(
        "Returns LLM-scored dimension snapshots from the city_scores table.  "
        "Only dates that have been pre-computed (via the scheduler or on-demand) "
        "are included.  Fast — no LLM call."
    ),
)
async def get_city_dimensions(
    city_id: str,
    start: Optional[str] = Query(
        default=None,
        description="Start date YYYY-MM-DD (defaults to 365 days ago).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    end: Optional[str] = Query(
        default=None,
        description="End date YYYY-MM-DD (defaults to today UTC).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    city = await _get_city_or_404(city_id, session)

    today = datetime.now(timezone.utc).date()
    end_date = date.fromisoformat(end) if end else today
    start_date = date.fromisoformat(start) if start else end_date - timedelta(days=365)

    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start must be before end.")

    result = await session.execute(
        select(CityScore)
        .where(
            CityScore.city_id == city_id,
            CityScore.scored_date >= start_date,
            CityScore.scored_date <= end_date,
        )
        .order_by(CityScore.scored_date)
    )
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No pre-computed scores found for '{city.name}' "
                f"between {start_date} and {end_date}.  "
                "Run the scheduler to pre-compute scores."
            ),
        )

    snapshots: List[Dict[str, Any]] = []
    for row in rows:
        try:
            full = json.loads(row.score_json)
        except (json.JSONDecodeError, TypeError):
            continue

        dims = {}
        for d in full.get("dimensions", []):
            name = d.get("name", "").lower().replace(" ", "_")
            if name:
                dims[name] = d.get("score")

        snapshots.append({
            "date": row.scored_date.isoformat(),
            "overall_score": row.overall_score,
            "overall_confidence": row.overall_confidence,
            "dimensions": dims,
        })

    return {
        "city_id": city_id,
        "city_name": city.name,
        "snapshots": snapshots,
    }
