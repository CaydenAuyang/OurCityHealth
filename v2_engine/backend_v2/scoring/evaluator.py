"""
V2.1 — Deterministic Scoring Evaluator

Uses `instructor` (patched on top of `openai`) to force the LLM to emit
valid JSON conforming to our CityHealthScore schema.

V2.1 changes:
  - New rigorous intelligence-analyst system prompt.
  - calculate_score now accepts an EnrichedCityContext (from aggregator)
    that includes individual GDELT events, actors, CAMEO descriptions,
    and source URLs — producing specific, citable output.
  - The old CityContext dataclass is preserved for backward compatibility
    (used by build_context / the aggregator's internal weighted stats).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, Union

import instructor  # 0.4.x — uses instructor.patch(); Python 3.9-compatible
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .schemas import CityHealthScore, DIMENSION_NAMES

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Legacy context bundle (kept for backward compat with build_context)
# ------------------------------------------------------------------ #

@dataclass
class CityContext:
    """Aggregate-only factual inputs (Phase 3 original)."""

    city_name: str
    city_id: str
    scored_date: date
    country_code: str

    gdelt_avg_goldstein: float = 0.0
    gdelt_total_mentions: int = 0
    gdelt_event_count: int = 0
    gdelt_stability_score: float = 50.0
    gdelt_verbal_cooperation: int = 0
    gdelt_material_cooperation: int = 0
    gdelt_verbal_conflict: int = 0
    gdelt_material_conflict: int = 0

    news_snippets: list[str] = field(default_factory=list)
    aggregated_stability: Optional[float] = None


# ------------------------------------------------------------------ #
# V2.1 System prompt — intelligence analyst grade
# ------------------------------------------------------------------ #

_SYSTEM_PROMPT_V22 = """\
You are a senior geopolitical intelligence analyst producing a city risk \
assessment for institutional investors, real estate developers, and corporate \
security teams. Your assessments must meet financial-grade standards suitable \
for Investment Committee review.

CONTEXT YOU ARE RECEIVING:
You are provided with intelligence derived from news articles across multiple \
outlets, covering the target city over the past 90 days. Sources range from \
Tier 1 international wire services (Reuters, Bloomberg, BBC) to regional \
outlets. You also have structured event data covering distinct real-world \
happenings.

RULES:
1. SPECIFICITY: Every claim MUST reference a specific event, actor, date, \
or data point. Generic statements are unacceptable. Name the people, \
organizations, and dates involved.
2. ENTITY-AWARE ANALYSIS: Reference specific named individuals and \
organizations from the provided entity lists. When key political figures, \
CEOs, or institutional leaders appear, mention them by name and explain \
their relevance to the dimension being scored.
3. MULTI-SOURCE CORROBORATION: Prioritize findings reported by Tier 1 and \
Tier 2 sources. Note when only low-tier or single-source reporting exists \
— assign lower confidence. When international and domestic media disagree \
in tone, note the divergence as a signal.
4. CAUSAL ATTRIBUTION: For each dimension, explain what CAUSED the score. \
Not "Safety is 45" but "Safety scored 45, driven by 11 fight incidents \
involving police between Jan 1-20, representing a significant increase from \
the prior period." Connect specific events to scores. The user needs to \
understand the WHY.
5. SCORE DELTAS: You are provided with the previous period's scores. When \
a dimension changed significantly (>5 points), you MUST explain the causal \
driver in the causal_driver field. What specific events or trends caused \
the change?
6. CITATION REQUIREMENTS: Every claim must cite at least one source URL, \
preferring Tier 1-2 outlets. For risks and strengths, provide 3-5 citations \
from different outlets. Order citations by source credibility.
7. THEMATIC GROUNDING: Use the theme distribution to identify dominant \
narratives. Lead your analysis with the most prevalent themes.
8. SOURCE TONE ANALYSIS: When international and domestic outlets show \
divergent tone, flag this. It may indicate information asymmetry or \
propaganda influence.
9. Never use vague language: 'seems', 'maybe', 'perhaps', 'might', \
'could be', 'possibly', 'unclear', 'uncertain', 'appears to', 'I think', \
'I believe'.
10. overall_score must equal the arithmetic mean of dimension scores ± 5 pts.
11. Scores 0-100 (int); confidence 0.0-1.0 (float).

SCORING GUIDE:
  0-20 : Crisis conditions — active conflict, state failure, severe \
instability.
  20-40: High risk — significant unrest, deteriorating governance, \
economic crisis.
  40-55: Elevated concern — notable tensions or challenges but functional \
systems.
  55-70: Stable — normal conditions with typical urban challenges.
  70-85: Strong — well-functioning systems with positive trends.
  85-100: Exceptional — outstanding conditions across all indicators.

CONFIDENCE CALIBRATION:
- 0.9-1.0: Multiple Tier 1 corroborating sources, direct evidence, high \
relevance.
- 0.7-0.89: Good evidence but some inference required, or tangential sources.
- 0.5-0.69: Limited direct evidence, relying on regional/national patterns.
- 0.3-0.49: Very limited evidence, mostly inference.
- 0.0-0.29: Essentially no relevant data — score should be near 50.

RULES FOR TOP RISKS AND TOP STRENGTHS:
- Each MUST synthesise MULTIPLE events, not a single headline.
- Each must cite at least 2-3 different source URLs.
- Include source_tiers for each citation (array of integers like [1, 2, 3]).
- Minimum 3 risks and 3 strengths, maximum 5 each.
- summary: describe the PATTERN or TREND with specific actors and dates. \
Do NOT embed URLs in summary text.
- supporting_event_count: integer count of distinct events.
- date_range: span of supporting events, e.g. "Jan 3-15, 2024".
- citations: list of 2+ distinct source URL strings.

RULES FOR EVIDENCE SNIPPETS:
- Synthesise information from multiple events when available.
- Mention event counts and date ranges.
- 2-3 evidence snippets per dimension when data is available.
- Include source URLs in square brackets at end of each snippet.

ANALYST SUMMARY:
Write a 3-4 sentence executive summary as if briefing an Investment \
Committee. Lead with the most material risk or opportunity. Reference \
specific actors and dates. End with a forward-looking statement about \
trajectory.

GOLDSTEIN SCALE (for reference):
  -10 to -5 : Major conflict / material violence
   -5 to  0 : Verbal conflict / political tension
    0 to +5 : Neutral or cooperative interactions
   +5 to +10: Strong cooperation / positive diplomacy
"""


def _build_enriched_user_prompt(ctx) -> str:
    """
    Format an EnrichedCityContext into a structured user prompt.

    V2.2: includes deduped events, named entities, themes, source tone,
    and period-over-period score deltas alongside existing event data.
    """
    total_articles = getattr(ctx, "total_articles", 0)
    unique_sources = getattr(ctx, "unique_sources", 0)

    lines = [
        f"City: {ctx.city_name} ({ctx.city_country})",
        f"Assessment date: {ctx.analysis_date}",
        f"Analysis window: {ctx.window_days} days",
        f"Intelligence base: {total_articles} articles from {unique_sources} sources, "
        f"{ctx.total_events} structured events",
        "",
        "=== AGGREGATE STATISTICS ===",
        f"  Total GDELT events    : {ctx.total_events}",
        f"  Total mentions        : {ctx.total_mentions}",
        f"  Avg Goldstein         : {ctx.avg_goldstein:+.2f}",
        f"  Stability score (0-100): {ctx.stability_score:.1f}",
        f"  Cooperation events    : {ctx.cooperation_events}",
        f"  Conflict events       : {ctx.conflict_events}",
    ]

    # Score deltas
    prev_score = getattr(ctx, "previous_period_score", None)
    delta = getattr(ctx, "score_delta", None)
    if prev_score is not None and delta is not None:
        lines += [
            "",
            "=== SCORE CHANGES FROM PREVIOUS PERIOD ===",
            f"  Overall: {ctx.stability_score:.1f} (prev: {prev_score:.1f}, "
            f"delta: {delta:+.1f})",
        ]
        dim_deltas = getattr(ctx, "dimension_deltas", {})
        for dim_name, dv in dim_deltas.items():
            lines.append(f"  {dim_name}: delta {dv:+.1f}")

    # Named entities
    top_persons = getattr(ctx, "top_persons", [])
    if top_persons:
        lines += [
            "",
            "=== TOP PERSONS (by mention frequency) ===",
            "  " + ", ".join(top_persons[:10]),
        ]

    top_orgs = getattr(ctx, "top_organizations", [])
    if top_orgs:
        lines += [
            "",
            "=== TOP ORGANIZATIONS (by mention frequency) ===",
            "  " + ", ".join(top_orgs[:10]),
        ]

    # Themes
    top_themes = getattr(ctx, "top_themes", [])
    if top_themes:
        lines += [
            "",
            "=== DOMINANT THEMES ===",
            "  " + ", ".join(top_themes[:10]),
        ]

    # Source tone
    tone_summary = getattr(ctx, "source_tone_summary", "")
    if tone_summary:
        lines += [
            "",
            "=== SOURCE TONE ANALYSIS (by credibility tier) ===",
            tone_summary,
        ]

    # Deduplicated events (preferred over raw duplicates)
    deduped = getattr(ctx, "deduped_events", [])
    if deduped:
        lines += [
            "",
            "=== DEDUPLICATED EVENTS (consolidated real-world happenings) ===",
        ]
        for i, de in enumerate(deduped[:15], 1):
            actors_str = ", ".join(de.actors[:4]) if de.actors else "Unknown"
            urls_str = " ".join(f"[{u}]" for u in de.source_urls[:3])
            lines.append(
                f"  [{i}] {de.date_range} | {de.event_description} | "
                f"Actors: {actors_str} | "
                f"Goldstein: {de.avg_goldstein:+.1f} | "
                f"Sources: {de.source_count} | "
                f"Mentions: {de.total_mentions} | {urls_str}"
            )
    elif ctx.top_events:
        lines += ["", "=== TOP EVENTS (ranked by impact) ==="]
        for i, ev in enumerate(ctx.top_events, 1):
            url_tag = ""
            if ev.source_url:
                url_tag = f" [{ev.source_url}]"
            lines.append(
                f"  [{i}] {ev.date} | {ev.event_description} | "
                f"Actor1: {ev.actor1} \u2192 Actor2: {ev.actor2} | "
                f"Goldstein: {ev.goldstein_scale:+.1f} | "
                f"Mentions: {ev.num_mentions}{url_tag}"
            )
    else:
        lines += [
            "",
            "=== TOP EVENTS ===",
            "  (no individual events available \u2014 score from aggregates only; "
            "reduce confidence)",
        ]

    # Event clusters
    clusters = getattr(ctx, "event_clusters", "")
    if clusters:
        lines += [
            "",
            "=== EVENT CLUSTERS (grouped by CAMEO type) ===",
            "(Use these clusters to identify patterns for top_risks / top_strengths)",
            clusters,
        ]

    if ctx.top_sources:
        lines += ["", "=== TOP SOURCE URLS ==="]
        for i, url in enumerate(ctx.top_sources, 1):
            lines.append(f"  [{i}] {url}")

    lines += [
        "",
        "=== OUTPUT REQUIREMENTS ===",
        "Task: Produce a CityHealthScore JSON covering ALL 12 dimensions:",
        "  " + ", ".join(DIMENSION_NAMES.__args__),  # type: ignore[attr-defined]
        "",
        "Each dimension needs:",
        "  score (0-100 int), confidence (0.0-1.0 float),",
        "  evidence_snippets (2-3 items with [URL] citations inline),",
        "  reasoning (specific, no hedging), citations (list of source URL strings),",
        "  score_delta (float or null \u2014 change from previous period),",
        "  causal_driver (string or null \u2014 explain WHY if delta > 5 pts).",
        "",
        "top_risks and top_strengths \u2014 each item is a RiskOrStrength object with:",
        "  summary: pattern description (no inline URLs), NO vague language,",
        "  supporting_event_count: int,",
        "  date_range: string e.g. 'Jan 3-15, 2023',",
        "  citations: list of 2+ source URL strings,",
        "  source_tiers: list of ints (credibility tier 1-4 for each citation).",
        "Produce 3-5 risks and 3-5 strengths. Each MUST synthesise multiple events.",
        "",
        "Also provide:",
        "  key_events (top 5), analyst_summary (3-4 sentences naming specific",
        "  actors and dates; end with trajectory statement),",
        "  total_articles_analyzed, unique_sources_analyzed, top_entities,",
        "  dominant_themes, source_bias_note (or null), previous_overall_score,",
        "  score_delta, dimension_deltas.",
        "Do NOT omit any field.  Do NOT hedge.  Be precise and cite specifics.",
    ]
    return "\n".join(lines)


def _build_legacy_user_prompt(ctx: CityContext) -> str:
    """Format the old CityContext (aggregate-only, no individual events)."""
    lines = [
        f"City: {ctx.city_name} ({ctx.country_code})",
        f"Assessment date: {ctx.scored_date.isoformat()}",
        "",
        "=== GDELT EVENT SUMMARY ===",
        f"  Event count   : {ctx.gdelt_event_count}",
        f"  Total mentions: {ctx.gdelt_total_mentions}",
        f"  Avg Goldstein : {ctx.gdelt_avg_goldstein:+.2f}",
        f"  Stability     : {ctx.gdelt_stability_score:.1f}",
        f"  Verbal cooperation : {ctx.gdelt_verbal_cooperation}",
        f"  Material cooperation: {ctx.gdelt_material_cooperation}",
        f"  Verbal conflict    : {ctx.gdelt_verbal_conflict}",
        f"  Material conflict  : {ctx.gdelt_material_conflict}",
    ]
    if ctx.aggregated_stability is not None:
        lines.append(f"  Recency-weighted stability: {ctx.aggregated_stability:.1f}")

    if ctx.news_snippets:
        lines += ["", "=== NEWS / WEB SNIPPETS ==="]
        for i, s in enumerate(ctx.news_snippets[:20], 1):
            lines.append(f"  [{i}] {s}")
    else:
        lines += [
            "", "=== NEWS / WEB SNIPPETS ===",
            "  (none available — score based on GDELT only; reduce confidence)",
        ]

    lines += [
        "",
        "Task: Produce a CityHealthScore JSON covering ALL 12 dimensions:",
        "  " + ", ".join(DIMENSION_NAMES.__args__),  # type: ignore[attr-defined]
        "Each dimension needs: score, confidence, evidence_snippets, reasoning.",
        "Do NOT omit any field.  Do NOT hedge.  Be precise.",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------ #
# ScoreEvaluator
# ------------------------------------------------------------------ #

class ScoreEvaluator:
    """
    Wraps the instructor-patched OpenAI client.

    Usage (V2.1 with enriched context)::

        evaluator = ScoreEvaluator()
        score = evaluator.calculate_score(enriched_context)

    Usage (legacy with aggregate-only context)::

        score = evaluator.calculate_score(city_context)
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        max_retries: int = 3,
    ) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set.  Add it to v2_engine/.env"
            )

        raw_client = OpenAI(api_key=api_key)
        self._client = instructor.patch(raw_client)
        self._model = model
        self._max_retries = max_retries

    # ---------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------- #

    def calculate_score(
        self,
        city_context: Union[CityContext, "EnrichedCityContext_duck"],
        *,
        extra_system: str = "",
    ) -> CityHealthScore:
        """
        Call the LLM to produce a validated CityHealthScore.

        Accepts either an old-style CityContext (aggregate only) or the
        new EnrichedCityContext (with individual events and URLs).
        The prompt and system instruction are chosen accordingly.
        """
        is_enriched = hasattr(city_context, "top_events")

        system_content = _SYSTEM_PROMPT_V22
        if extra_system:
            system_content += "\n\n" + extra_system

        if is_enriched:
            user_content = _build_enriched_user_prompt(city_context)
        else:
            user_content = _build_legacy_user_prompt(city_context)

        city_name = (
            city_context.city_name
            if hasattr(city_context, "city_name")
            else "unknown"
        )
        scored_date = (
            city_context.analysis_date
            if is_enriched
            else city_context.scored_date.isoformat()
        )

        logger.info(
            "Scoring %s for %s (model=%s, enriched=%s)",
            city_name, scored_date, self._model, is_enriched,
        )

        score = self._call_with_retry(system_content, user_content, city_context)

        # Stamp audit fields
        score.city_id = str(city_context.city_id)
        score.city_name = city_name
        if is_enriched:
            score.scored_date = date.fromisoformat(city_context.analysis_date)
        else:
            score.scored_date = city_context.scored_date
        score.generated_at = datetime.now(timezone.utc)
        if is_enriched:
            score.gdelt_event_count = city_context.total_events
            score.gdelt_avg_goldstein = city_context.avg_goldstein
        else:
            score.gdelt_event_count = city_context.gdelt_event_count
            score.gdelt_avg_goldstein = city_context.gdelt_avg_goldstein

        # V2.2: Stamp article/entity/delta metadata from the enriched context.
        # These fields are authoritative from structured data (GKG, delta
        # calculator) and must ALWAYS override whatever the LLM produced.
        if is_enriched:
            # Article counts — always from aggregator, never LLM
            score.total_articles_analyzed = city_context.total_articles
            score.unique_sources_analyzed = city_context.unique_sources

            # Named entities: top persons + top orgs from GKG, deduped
            top_p = city_context.top_persons
            top_o = city_context.top_organizations
            combined = top_p[:5] + top_o[:5]
            score.top_entities = list(dict.fromkeys(combined))[:10]

            # Dominant themes: GKG-derived translated strings (not LLM text)
            score.dominant_themes = city_context.top_themes[:10]

            # Score deltas — always from delta calculator
            score.previous_overall_score = city_context.previous_period_score
            score.score_delta = city_context.score_delta
            score.dimension_deltas = dict(city_context.dimension_deltas)

            # Source bias note from tone summary (may be empty string — that's fine)
            if city_context.source_tone_summary:
                score.source_bias_note = city_context.source_tone_summary

            logger.info(
                "V2.2 metadata stamped — articles=%d, sources=%d, "
                "persons=%d, orgs=%d, themes=%d, prev_score=%s, delta=%s, "
                "dim_deltas=%d",
                score.total_articles_analyzed,
                score.unique_sources_analyzed,
                len(top_p),
                len(top_o),
                len(score.dominant_themes),
                score.previous_overall_score,
                score.score_delta,
                len(score.dimension_deltas),
            )

        logger.info(
            "Score complete — %s overall=%d confidence=%.2f",
            city_name, score.overall_score, score.overall_confidence,
        )
        return score

    # ---------------------------------------------------------------- #
    # Internal helpers
    # ---------------------------------------------------------------- #

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _call_with_retry(
        self,
        system_content: str,
        user_content: str,
        ctx,
    ) -> CityHealthScore:
        """Inner call with tenacity retry for transient API failures."""
        try:
            result = self._client.chat.completions.create(
                model=self._model,
                response_model=CityHealthScore,
                max_retries=self._max_retries,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as exc:
            city_name = getattr(ctx, "city_name", "unknown")
            logger.error("LLM call failed for %s: %s", city_name, exc)
            raise

        return result
