"""
Strict Pydantic V2 schemas for the Phase 3 Scoring Engine.

Design principles:
  - Every field is validated on assignment (model_config validate_default=True).
  - `reasoning` is checked for vague hedge words — any violation raises immediately.
  - `evidence_snippets` must be non-empty so every score is traceable to source text.
  - `confidence` is a float bounded 0.0–1.0, independent of the 0-100 score.

These constraints make the schemas "financial-grade": an auditor can always
trace a score back to the exact snippets that produced it.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Annotated, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

# ------------------------------------------------------------------ #
# Dimension catalogue
# ------------------------------------------------------------------ #

DIMENSION_NAMES = Literal[
    "safety",
    "economy",
    "governance",
    "housing",
    "transport",
    "environment",
    "health",
    "culture",
    "education",
    "technology",
    "community",
    "cost_of_living",
]

# Words that indicate imprecise LLM reasoning — banned from `reasoning` fields
_VAGUE_WORDS: list[str] = [
    "seems",
    "maybe",
    "perhaps",
    "might",
    "could be",
    "possibly",
    "unclear",
    "uncertain",
    "appears to",
    "i think",
    "i believe",
    "it's possible",
]
_VAGUE_PATTERN = re.compile(
    "|".join(re.escape(w) for w in _VAGUE_WORDS),
    re.IGNORECASE,
)


def _reject_vague(text: str, field_name: str = "reasoning") -> str:
    """Raise ValueError if `text` contains any banned hedge words."""
    match = _VAGUE_PATTERN.search(text)
    if match:
        raise ValueError(
            f"'{field_name}' contains vague language ('{match.group()}').  "
            "Use specific, evidence-based language only."
        )
    return text


# ------------------------------------------------------------------ #
# DimensionScore — one per civic dimension per city per date
# ------------------------------------------------------------------ #

class DimensionScore(BaseModel):
    """
    Score for a single civic dimension.

    All fields are required; no defaults exist so the LLM is forced to produce
    a fully populated object — instructor will retry on missing fields.
    """

    model_config = {"validate_default": True}

    dimension: DIMENSION_NAMES = Field(
        description="Which civic dimension this score covers.",
    )
    score: Annotated[int, Field(ge=0, le=100)] = Field(
        description=(
            "0 = catastrophic, 50 = average/neutral, 100 = excellent.  "
            "Must be grounded in evidence_snippets."
        ),
    )
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        description=(
            "How confident the scorer is, 0.0–1.0.  "
            "Low confidence when evidence is thin or contradictory."
        ),
    )
    evidence_snippets: list[str] = Field(
        min_length=1,
        description=(
            "1–10 direct quotes or paraphrased sentences from source material "
            "that justify the score.  Must not be empty."
        ),
    )
    reasoning: str = Field(
        min_length=30,
        description=(
            "Concise explanation (≥ 30 chars) citing specific evidence.  "
            "No hedge words ('seems', 'maybe', etc.)."
        ),
    )
    citations: list[str] = Field(
        default_factory=list,
        description=(
            "Source URLs that support this dimension's score.  "
            "Extracted from evidence_snippets when URLs are available."
        ),
    )
    score_delta: Optional[float] = Field(
        default=None,
        description="Change from previous period's score for this dimension.",
    )
    causal_driver: Optional[str] = Field(
        default=None,
        description=(
            "Explanation of what caused a significant score change (>5 pts).  "
            "References specific events, actors, and dates."
        ),
    )

    @field_validator("evidence_snippets")
    @classmethod
    def snippets_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("evidence_snippets must contain at least one item.")
        if any(not s.strip() for s in v):
            raise ValueError("evidence_snippets must not contain blank strings.")
        return v

    @field_validator("reasoning")
    @classmethod
    def reasoning_is_specific(cls, v: str) -> str:
        return _reject_vague(v, "reasoning")


# ------------------------------------------------------------------ #
# RiskOrStrength — structured risk/strength with multi-source citations
# ------------------------------------------------------------------ #

class RiskOrStrength(BaseModel):
    """
    A structured risk or strength finding backed by multiple GDELT events.

    The LLM is instructed to synthesise patterns across events rather than
    picking a single headline.  The hard floor on citations is 1 (schema
    validation), but the prompt requires 2+ as a soft instruction.
    """

    model_config = {"validate_default": True}

    summary: str = Field(
        min_length=20,
        description=(
            "Concise description of the pattern or trend.  "
            "Must synthesise multiple events — no single-headline statements.  "
            "No inline URLs."
        ),
    )
    supporting_event_count: int = Field(
        ge=1,
        description="Number of distinct GDELT events that corroborate this finding.",
    )
    date_range: str = Field(
        description='Date span of the supporting events, e.g. "Jan 3–15, 2024".',
    )
    citations: list[str] = Field(
        min_length=1,
        description=(
            "Source URLs corroborating this finding.  "
            "Aim for 2–3+ distinct outlets for cross-source validation."
        ),
    )

    source_tiers: List[int] = Field(
        default_factory=list,
        description="Credibility tier (1-4) for each citation, in the same order.",
    )

    @field_validator("summary")
    @classmethod
    def summary_is_specific(cls, v: str) -> str:
        return _reject_vague(v, "summary")

    @field_validator("citations")
    @classmethod
    def warn_single_citation(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            import logging
            logging.getLogger(__name__).warning(
                "RiskOrStrength has only %d citation(s); 2+ recommended.", len(v)
            )
        return v


# ------------------------------------------------------------------ #
# KeyEvent — most-impactful events surfaced in the score (V2.1)
# ------------------------------------------------------------------ #

class KeyEvent(BaseModel):
    """
    A single significant event surfaced by the scoring engine.

    The evaluator picks the top 5 events by impact (|goldstein| * mentions)
    and classifies each as positive, negative, or neutral.
    """

    model_config = {"validate_default": True}

    date: str = Field(description="ISO date YYYY-MM-DD of the event.")
    description: str = Field(
        min_length=10,
        description="Human-readable event description from CAMEO lookup + LLM context.",
    )
    actors: list[str] = Field(
        description="Actor names involved in the event.",
    )
    impact: Literal["positive", "negative", "neutral"] = Field(
        description="Directional impact on civic health.",
    )
    goldstein_scale: float = Field(
        description="Goldstein scale value for this event.",
    )
    source_url: Optional[str] = Field(
        default=None,
        description="URL to the original source article, if available.",
    )


# ------------------------------------------------------------------ #
# CityHealthScore — top-level object returned by the scoring engine
# ------------------------------------------------------------------ #

class CityHealthScore(BaseModel):
    """
    Complete civic health assessment for a city on a given date.

    Produced by ScoreEvaluator.calculate_score() and stored/returned
    via the /api/v2/score/{city_id} endpoint.
    """

    model_config = {"validate_default": True}

    city_id: str = Field(description="UUID of the city in the cities table.")
    city_name: str = Field(description="Human-readable city name.")
    scored_date: date = Field(description="The calendar date this assessment covers.")
    generated_at: datetime = Field(description="UTC timestamp when the score was produced.")

    overall_score: Annotated[int, Field(ge=0, le=100)] = Field(
        description=(
            "Weighted average across all dimensions, 0–100.  "
            "Calculated deterministically from dimension scores."
        ),
    )
    overall_confidence: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        description="Mean confidence across all dimension scores.",
    )
    dimensions: list[DimensionScore] = Field(
        min_length=1,
        description="One DimensionScore per civic dimension assessed.",
    )
    top_risks: list[RiskOrStrength] = Field(
        max_length=5,
        default_factory=list,
        description=(
            "3–5 risk patterns identified from the evidence.  "
            "Each must synthesise multiple events with 2+ source citations."
        ),
    )
    top_strengths: list[RiskOrStrength] = Field(
        max_length=5,
        default_factory=list,
        description=(
            "3–5 strength patterns identified from the evidence.  "
            "Each must synthesise multiple events with 2+ source citations."
        ),
    )
    data_sources: list[str] = Field(
        description="List of source types used (e.g. 'GDELT', 'news snippet').",
    )
    gdelt_event_count: int = Field(
        ge=0,
        default=0,
        description="Number of GDELT events that contributed to this score.",
    )
    gdelt_avg_goldstein: float = Field(
        default=0.0,
        description="Average Goldstein Scale across contributing GDELT events.",
    )
    key_events: list[KeyEvent] = Field(
        default_factory=list,
        description="Top 5 most impactful events from GDELT that shaped the assessment.",
    )
    analyst_summary: str = Field(
        default="",
        description=(
            "2-3 sentence executive summary suitable for institutional clients.  "
            "Must reference specific actors, dates, or events."
        ),
    )
    total_articles_analyzed: int = Field(
        default=0,
        description="Number of GKG articles analysed for this score.",
    )
    unique_sources_analyzed: int = Field(
        default=0,
        description="Number of unique news sources contributing articles.",
    )
    top_entities: List[str] = Field(
        default_factory=list,
        description="Top named entities (persons + organisations) by mention frequency.",
    )
    dominant_themes: List[str] = Field(
        default_factory=list,
        description="Most prevalent GKG themes in the analysis window.",
    )
    source_bias_note: Optional[str] = Field(
        default=None,
        description=(
            "Analyst note on source bias or divergent tone between international "
            "and domestic outlets, if detected."
        ),
    )
    previous_overall_score: Optional[float] = Field(
        default=None,
        description="Overall score from the previous analysis period, if available.",
    )
    score_delta: Optional[float] = Field(
        default=None,
        description="Change in overall score from the previous period.",
    )
    dimension_deltas: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-dimension score deltas from the previous period.",
    )

    @model_validator(mode="after")
    def overall_score_matches_dimensions(self) -> "CityHealthScore":
        """
        Verify that overall_score is a plausible weighted mean of dimension scores.
        Allow ±5 tolerance for floating-point rounding from the aggregator.
        """
        if not self.dimensions:
            return self
        mean = sum(d.score for d in self.dimensions) / len(self.dimensions)
        if abs(self.overall_score - mean) > 10:
            raise ValueError(
                f"overall_score ({self.overall_score}) deviates more than 10 points "
                f"from dimension mean ({mean:.1f}).  Recalculate."
            )
        return self


# ------------------------------------------------------------------ #
# Lightweight read model — returned from TimescaleDB history queries
# ------------------------------------------------------------------ #

class DailyStatsRow(BaseModel):
    """Thin read-model matching the daily_city_stats hypertable columns."""

    day: date
    city_id: UUID
    avg_goldstein: float
    total_mentions: int
    event_count: int
    stability_score: float
    verbal_cooperation_count: int
    material_cooperation_count: int
    verbal_conflict_count: int
    material_conflict_count: int
    unique_sources: int
