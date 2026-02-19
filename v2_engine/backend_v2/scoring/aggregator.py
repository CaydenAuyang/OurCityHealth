"""
Phase 3 — Score Aggregator

Fuses two signal streams into a single CityContext that the evaluator can score:

  1. EVENT signal  — structured GDELT data from daily_city_stats (TimescaleDB)
  2. SEMANTIC signal — free-text snippets (news, Reddit) from future scrapers

Recency weighting:
  Each day's contribution decays exponentially.  A day from last week
  counts far more than a day from six months ago, ensuring the score
  reflects current conditions rather than a flat historical average.

  weight(t) = exp(-λ · Δdays)   where λ = ln(2) / half_life_days

  Default half_life = 30 days → a day 30 days old has half the weight
  of today; a day 90 days old has ~12.5 % of today's weight.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from datetime import date, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend_v2.db.timescale_models import DailyCityStats, CityEvent, CityArticle
from .cameo_codes import describe_event_code
from .deduplicator import DedupedEvent, deduplicate_events
from .delta_calculator import ScoreDeltas, calculate_deltas
from .evaluator import CityContext
from .schemas import DailyStatsRow
from .source_ranker import get_source_tier, rank_articles
from .theme_codes import describe_theme

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Constants
# ------------------------------------------------------------------ #

DEFAULT_HALF_LIFE_DAYS: int = 30
"""Days after which an event's weight halves."""

DEFAULT_LOOKBACK_DAYS: int = 180
"""How far back to pull GDELT rows when no explicit window is given."""


# ------------------------------------------------------------------ #
# Recency helpers
# ------------------------------------------------------------------ #

def _decay_weight(event_date: date, reference_date: date, half_life: int) -> float:
    """
    Exponential decay weight relative to reference_date.

    Returns 1.0 for same-day events, approaching 0 for very old events.
    """
    delta = (reference_date - event_date).days
    if delta < 0:
        # Future-dated data gets weight 1.0 (should not normally occur)
        return 1.0
    lam = math.log(2) / half_life
    return math.exp(-lam * delta)


def _weighted_mean(
    values: list[float],
    weights: list[float],
) -> Optional[float]:
    """Weighted arithmetic mean; returns None if all weights are zero."""
    total_w = sum(weights)
    if total_w == 0.0:
        return None
    return sum(v * w for v, w in zip(values, weights)) / total_w


# ------------------------------------------------------------------ #
# ScoreAggregator
# ------------------------------------------------------------------ #

class ScoreAggregator:
    """
    Loads GDELT data from TimescaleDB and fuses it with optional text snippets
    to produce a CityContext ready for the ScoreEvaluator.

    Typical flow::

        aggregator = ScoreAggregator(db_session)
        ctx = await aggregator.build_context(city_id, city_name, ..., scored_date)
        score = evaluator.calculate_score(ctx)
    """

    def __init__(
        self,
        session: AsyncSession,
        half_life_days: int = DEFAULT_HALF_LIFE_DAYS,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> None:
        self._session = session
        self._half_life = half_life_days
        self._lookback = lookback_days

    # ---------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------- #

    async def build_context(
        self,
        city_id: UUID | str,
        city_name: str,
        country_code: str,
        scored_date: date,
        news_snippets: Optional[list[str]] = None,
    ) -> CityContext:
        """
        Fetch GDELT rows from TimescaleDB and compute recency-weighted stats.

        Args:
            city_id:      UUID of the city (cities.id).
            city_name:    Human-readable name for prompt injection.
            country_code: ISO 2-char code for prompt injection.
            scored_date:  The date we are assessing.
            news_snippets: Optional free-text snippets from scrapers.

        Returns:
            CityContext populated with weighted GDELT statistics.
        """
        city_id_str = str(city_id)
        rows = await self._fetch_rows(city_id_str, scored_date)

        if not rows:
            logger.warning(
                "No GDELT rows found for city %s (%s) within %d days of %s",
                city_name,
                city_id_str,
                self._lookback,
                scored_date,
            )
            return CityContext(
                city_name=city_name,
                city_id=city_id_str,
                scored_date=scored_date,
                country_code=country_code,
                news_snippets=news_snippets or [],
            )

        weights = [_decay_weight(r.day, scored_date, self._half_life) for r in rows]

        weighted_goldstein = _weighted_mean(
            [r.avg_goldstein for r in rows], weights
        ) or 0.0
        weighted_stability = _weighted_mean(
            [r.stability_score for r in rows], weights
        ) or 50.0

        total_mentions = sum(r.total_mentions for r in rows)
        total_events = sum(r.event_count for r in rows)
        verbal_coop = sum(r.verbal_cooperation_count for r in rows)
        material_coop = sum(r.material_cooperation_count for r in rows)
        verbal_conf = sum(r.verbal_conflict_count for r in rows)
        material_conf = sum(r.material_conflict_count for r in rows)

        logger.info(
            "Built context for %s: %d rows, weighted_stability=%.1f, weighted_goldstein=%.2f",
            city_name,
            len(rows),
            weighted_stability,
            weighted_goldstein,
        )

        return CityContext(
            city_name=city_name,
            city_id=city_id_str,
            scored_date=scored_date,
            country_code=country_code,
            gdelt_avg_goldstein=weighted_goldstein,
            gdelt_total_mentions=total_mentions,
            gdelt_event_count=total_events,
            gdelt_stability_score=weighted_stability,
            gdelt_verbal_cooperation=verbal_coop,
            gdelt_material_cooperation=material_coop,
            gdelt_verbal_conflict=verbal_conf,
            gdelt_material_conflict=material_conf,
            aggregated_stability=weighted_stability,
            news_snippets=news_snippets or [],
        )

    # ---------------------------------------------------------------- #
    # Internal DB fetch
    # ---------------------------------------------------------------- #

    async def _fetch_rows(
        self,
        city_id: str,
        reference_date: date,
    ) -> list[DailyStatsRow]:
        """
        Pull daily_city_stats rows for the lookback window.

        TimescaleDB will use its chunk-exclusion index to scan only the
        relevant time chunks — far faster than a full-table scan.
        """
        cutoff = reference_date - timedelta(days=self._lookback)

        result = await self._session.execute(
            select(DailyCityStats)
            .where(DailyCityStats.city_id == city_id)
            .where(DailyCityStats.day >= cutoff)
            .where(DailyCityStats.day <= reference_date)
            .order_by(DailyCityStats.day.asc())
        )
        raw_rows = result.scalars().all()

        return [
            DailyStatsRow(
                day=r.day,
                city_id=r.city_id,
                avg_goldstein=r.avg_goldstein,
                total_mentions=r.total_mentions,
                event_count=r.event_count,
                stability_score=r.stability_score,
                verbal_cooperation_count=r.verbal_cooperation_count,
                material_cooperation_count=r.material_cooperation_count,
                verbal_conflict_count=r.verbal_conflict_count,
                material_conflict_count=r.material_conflict_count,
                unique_sources=r.unique_sources,
            )
            for r in raw_rows
        ]

    # ---------------------------------------------------------------- #
    # Convenience: fetch history rows directly (used by history endpoint)
    # ---------------------------------------------------------------- #

    async def fetch_history(
        self,
        city_id: str,
        start_date: date,
        end_date: date,
        limit: int = 365,
    ) -> list[DailyStatsRow]:
        """
        Retrieve raw daily stats for the /history endpoint, no weighting applied.
        """
        result = await self._session.execute(
            select(DailyCityStats)
            .where(DailyCityStats.city_id == city_id)
            .where(DailyCityStats.day >= start_date)
            .where(DailyCityStats.day <= end_date)
            .order_by(DailyCityStats.day.asc())
            .limit(limit)
        )
        raw_rows = result.scalars().all()
        return [
            DailyStatsRow(
                day=r.day,
                city_id=r.city_id,
                avg_goldstein=r.avg_goldstein,
                total_mentions=r.total_mentions,
                event_count=r.event_count,
                stability_score=r.stability_score,
                verbal_cooperation_count=r.verbal_cooperation_count,
                material_cooperation_count=r.material_cooperation_count,
                verbal_conflict_count=r.verbal_conflict_count,
                material_conflict_count=r.material_conflict_count,
                unique_sources=r.unique_sources,
            )
            for r in raw_rows
        ]

    # ---------------------------------------------------------------- #
    # V2.1 — Enriched context with individual event details
    # ---------------------------------------------------------------- #

    async def get_enriched_context(
        self,
        city_id: str,
        city_name: str,
        country_code: str,
        scored_date: date,
        window_days: int = 90,
        top_n_events: int = 25,
    ) -> "EnrichedCityContext":
        """
        Build a rich context for the LLM by combining aggregate GDELT stats
        with the most significant individual events, GKG articles, named
        entities, themes, source rankings, and period-over-period deltas.

        V2.2 additions over V2.1:
          - GKG article ingestion (city_articles)
          - Event deduplication
          - Source credibility ranking
          - Named entity & theme extraction
          - Score delta calculation
        """
        # 1. Aggregate stats via existing build_context (reuses all weighting)
        old_ctx = await self.build_context(
            city_id=city_id,
            city_name=city_name,
            country_code=country_code,
            scored_date=scored_date,
        )

        # 2. Pull top individual events from city_events
        cutoff = scored_date - timedelta(days=window_days)
        result = await self._session.execute(
            select(CityEvent)
            .where(CityEvent.city_id == city_id)
            .where(CityEvent.event_date >= cutoff)
            .where(CityEvent.event_date <= scored_date)
            .order_by(
                (func.abs(CityEvent.goldstein_scale) * func.coalesce(CityEvent.num_mentions, 1))
                .desc()
            )
            .limit(top_n_events)
        )
        raw_events = result.scalars().all()

        top_events: list[EventDetail] = []
        url_mentions: Counter = Counter()
        cooperation_count = 0
        conflict_count = 0

        cluster_events: dict = {}
        cluster_goldstein: dict = {}

        # Build raw event dicts for the deduplicator
        raw_event_dicts: list[dict] = []

        for ev in raw_events:
            desc = describe_event_code(ev.event_code or "")
            ed = EventDetail(
                date=ev.event_date.isoformat(),
                actor1=ev.actor1 or "Unknown",
                actor2=ev.actor2 or "Unknown",
                event_description=desc,
                goldstein_scale=ev.goldstein_scale or 0.0,
                num_mentions=ev.num_mentions or 0,
                source_url=ev.source_url,
            )
            top_events.append(ed)
            raw_event_dicts.append({
                "event_date": ev.event_date,
                "event_code": ev.event_code,
                "actor1": ev.actor1,
                "actor2": ev.actor2,
                "goldstein_scale": ev.goldstein_scale or 0.0,
                "num_mentions": ev.num_mentions or 0,
                "source_url": ev.source_url,
                "event_description": desc,
            })
            if ev.source_url:
                url_mentions[ev.source_url] += ev.num_mentions or 1
            gs = ev.goldstein_scale or 0.0
            if gs > 0:
                cooperation_count += 1
            elif gs < 0:
                conflict_count += 1

            code = (ev.event_code or "00").zfill(3)
            root = code[:2]
            if root not in cluster_events:
                cluster_events[root] = []
                cluster_goldstein[root] = []
            cluster_events[root].append(ed)
            cluster_goldstein[root].append(gs)

        # 3. Build cluster summary text
        cluster_lines = []
        for root in sorted(cluster_events.keys()):
            evs = cluster_events[root]
            gs_list = cluster_goldstein[root]
            avg_gs = sum(gs_list) / len(gs_list) if gs_list else 0.0
            root_desc = describe_event_code(root + "0")
            top3 = sorted(
                evs,
                key=lambda e: abs(e.goldstein_scale) * max(e.num_mentions, 1),
                reverse=True,
            )[:3]
            notable = "; ".join(
                f"{e.date} [{e.actor1}\u2192{e.actor2}] gs={e.goldstein_scale:+.1f}"
                for e in top3
            )
            cluster_lines.append(
                f"  - {root_desc} (code {root}x): "
                f"{len(evs)} events, avg Goldstein {avg_gs:+.2f} | "
                f"Notable: {notable}"
            )
        cluster_summary = "\n".join(cluster_lines) if cluster_lines else "  (none)"

        # 4. Deduplicate events
        deduped = deduplicate_events(raw_event_dicts)

        # 5. Top sources by mention volume (legacy)
        top_source_urls = [url for url, _ in url_mentions.most_common(5)]

        # -------------------------------------------------------------- #
        # V2.2: GKG article-based enrichment
        # -------------------------------------------------------------- #
        total_articles = 0
        unique_sources = 0
        top_sources_list: List[SourceSummary] = []
        top_persons: List[str] = []
        top_organizations: List[str] = []
        top_themes: List[str] = []
        source_tone_summary = ""

        try:
            article_result = await self._session.execute(
                select(CityArticle)
                .where(CityArticle.city_id == str(city_id))
                .where(CityArticle.article_date >= cutoff)
                .where(CityArticle.article_date <= scored_date)
                .order_by(CityArticle.article_date.desc())
                .limit(100)
            )
            articles_orm = article_result.scalars().all()
            logger.info(
                "GKG articles found for %s (%s window ending %s): %d",
                city_name, window_days, scored_date, len(articles_orm),
            )

            if articles_orm:
                total_articles = len(articles_orm)

                # Build article dicts for the ranker
                article_dicts = [
                    {
                        "source_name": a.source_name or "",
                        "url": a.url,
                        "word_count": a.word_count or 0,
                        "tone_overall": a.tone_overall,
                        "themes": a.themes or "",
                        "persons": a.persons or "",
                        "organizations": a.organizations or "",
                    }
                    for a in articles_orm
                ]

                ranked = rank_articles(article_dicts)

                # Unique sources
                source_names = set(a["source_name"].lower() for a in article_dicts if a["source_name"])
                unique_sources = len(source_names)

                # Person frequency
                person_counter: Counter = Counter()
                for a in article_dicts:
                    for p in a["persons"].split(";"):
                        p = p.split(",")[0].strip()
                        if p:
                            person_counter[p] += 1
                top_persons = [name for name, _ in person_counter.most_common(10)]

                # Organization frequency
                org_counter: Counter = Counter()
                for a in article_dicts:
                    for o in a["organizations"].split(";"):
                        o = o.split(",")[0].strip()
                        if o:
                            org_counter[o] += 1
                top_organizations = [name for name, _ in org_counter.most_common(10)]

                # Theme frequency — count raw codes then translate to English.
                # Deduplicate translated descriptions (multiple codes → same label).
                theme_counter: Counter = Counter()
                for a in article_dicts:
                    for t in a["themes"].split(";"):
                        t = t.split(",")[0].strip()
                        if t:
                            theme_counter[t] += 1
                seen_descriptions: dict = {}  # description → total count
                for code, cnt in theme_counter.most_common(50):
                    desc = describe_theme(code)
                    seen_descriptions[desc] = seen_descriptions.get(desc, 0) + cnt
                top_themes = [
                    desc for desc, _
                    in sorted(seen_descriptions.items(), key=lambda x: -x[1])
                ][:10]

                # Group by source: avg tone per source, grouped by tier
                source_tone: Dict[str, list] = {}
                for a in article_dicts:
                    sn = a["source_name"].lower().strip() or "unknown"
                    if sn not in source_tone:
                        source_tone[sn] = []
                    if a["tone_overall"] is not None:
                        source_tone[sn].append(a["tone_overall"])

                src_summaries: List[SourceSummary] = []
                for sn, tones in source_tone.items():
                    avg_t = sum(tones) / len(tones) if tones else 0.0
                    tier = get_source_tier(sn)
                    sample = next(
                        (a["url"] for a in article_dicts
                         if (a["source_name"] or "").lower().strip() == sn),
                        "",
                    )
                    src_summaries.append(SourceSummary(
                        source_name=sn,
                        tier=tier,
                        article_count=len(tones),
                        avg_tone=round(avg_t, 2),
                        sample_url=sample,
                    ))
                src_summaries.sort(key=lambda s: (s.tier, -s.article_count))
                top_sources_list = src_summaries[:15]

                # Source tone summary text for LLM
                tier_tones: Dict[int, list] = {}
                for s in src_summaries:
                    if s.tier not in tier_tones:
                        tier_tones[s.tier] = []
                    tier_tones[s.tier].append(s.avg_tone)
                tone_lines = []
                tier_labels = {1: "Tier 1 (major intl)", 2: "Tier 2 (national)",
                               3: "Tier 3 (aggregators)", 4: "Tier 4 (other)"}
                for t in sorted(tier_tones.keys()):
                    vals = tier_tones[t]
                    avg = sum(vals) / len(vals) if vals else 0.0
                    tone_lines.append(
                        f"  {tier_labels.get(t, 'Unknown')}: "
                        f"{len(vals)} sources, avg tone {avg:+.2f}"
                    )
                source_tone_summary = "\n".join(tone_lines)

        except Exception:
            logger.warning(
                "city_articles query failed for %s (city_id=%s) — "
                "V2.2 article enrichment will be skipped",
                city_name, city_id, exc_info=True,
            )

        # -------------------------------------------------------------- #
        # V2.2: Score deltas
        # -------------------------------------------------------------- #
        prev_score: Optional[float] = None
        score_delta_val: Optional[float] = None
        dim_deltas: Dict[str, float] = {}

        try:
            deltas = await calculate_deltas(
                city_id=city_id,
                current_date=scored_date.isoformat(),
                window_days=window_days,
                session=self._session,
            )
            prev_score = deltas.previous_overall
            score_delta_val = deltas.overall_delta
        except Exception:
            logger.warning(
                "Delta calculation failed for %s (city_id=%s) — non-fatal",
                city_name, city_id, exc_info=True,
            )

        ctx = EnrichedCityContext(
            city_name=city_name,
            city_country=country_code,
            analysis_date=scored_date.isoformat(),
            window_days=window_days,
            total_events=old_ctx.gdelt_event_count,
            avg_goldstein=old_ctx.gdelt_avg_goldstein,
            cooperation_events=cooperation_count,
            conflict_events=conflict_count,
            stability_score=old_ctx.gdelt_stability_score,
            total_mentions=old_ctx.gdelt_total_mentions,
            top_events=top_events,
            top_sources=top_source_urls,
            event_clusters=cluster_summary,
            city_id=str(city_id),
            # V2.2 additions
            total_articles=total_articles,
            unique_sources=unique_sources,
            top_sources_ranked=top_sources_list,
            top_persons=top_persons,
            top_organizations=top_organizations,
            top_themes=top_themes,
            deduped_events=deduped,
            source_tone_summary=source_tone_summary,
            previous_period_score=prev_score,
            score_delta=score_delta_val,
            dimension_deltas=dim_deltas,
        )

        logger.info(
            "Enriched context for %s: "
            "%d articles, %d unique sources, "
            "%d persons, %d orgs, %d themes, "
            "%d deduped events, prev_score=%s, delta=%s",
            city_name,
            ctx.total_articles,
            ctx.unique_sources,
            len(ctx.top_persons),
            len(ctx.top_organizations),
            len(ctx.top_themes),
            len(ctx.deduped_events),
            ctx.previous_period_score,
            ctx.score_delta,
        )

        return ctx


# ------------------------------------------------------------------ #
# V2.1 + V2.2 — Enriched context schemas
# ------------------------------------------------------------------ #

class EventDetail(BaseModel):
    """A single significant event pulled from city_events."""
    date: str
    actor1: str
    actor2: str
    event_description: str
    goldstein_scale: float
    num_mentions: int
    source_url: Optional[str] = None


class SourceSummary(BaseModel):
    """Aggregated info about a single news source."""
    source_name: str
    tier: int
    article_count: int
    avg_tone: float
    sample_url: str = ""


class EnrichedCityContext(BaseModel):
    """
    Everything the LLM needs to produce a citable, specific assessment.

    V2.2 additions: articles, deduped events, named entities, themes,
    source tone analysis, and period-over-period deltas.
    """
    city_name: str
    city_country: str
    city_id: str
    analysis_date: str
    window_days: int

    # Aggregate stats
    total_events: int
    avg_goldstein: float
    cooperation_events: int
    conflict_events: int
    stability_score: float = 50.0
    total_mentions: int = 0

    # Specific events
    top_events: List[EventDetail] = []
    top_sources: List[str] = []

    # CAMEO cluster summary (pre-formatted text for the LLM prompt)
    event_clusters: str = ""

    # V2.2: Article-level data
    total_articles: int = 0
    unique_sources: int = 0
    top_sources_ranked: List[SourceSummary] = []
    top_persons: List[str] = []
    top_organizations: List[str] = []
    top_themes: List[str] = []
    deduped_events: List[DedupedEvent] = []
    source_tone_summary: str = ""
    previous_period_score: Optional[float] = None
    score_delta: Optional[float] = None
    dimension_deltas: Dict[str, float] = {}
