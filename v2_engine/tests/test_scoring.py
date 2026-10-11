"""
Tests for the pure scoring helpers: source tiers, citation ranking,
recency weighting, the schema rules that constrain the LLM's output,
and event deduplication. No database, network or API key needed.
"""

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from backend_v2.scoring.aggregator import _decay_weight, _weighted_mean
from backend_v2.scoring.deduplicator import deduplicate_events
from backend_v2.scoring.schemas import CityHealthScore, DimensionScore
from backend_v2.scoring.source_ranker import get_source_tier, rank_articles


def _dimension(**overrides) -> dict:
    """A valid DimensionScore payload; tests override one field at a time."""
    data = {
        "dimension": "safety",
        "score": 45,
        "confidence": 0.8,
        "evidence_snippets": ["Police reported 11 incidents over 4 days."],
        "reasoning": "Eleven police incidents in four days, reported by three outlets.",
    }
    data.update(overrides)
    return data


# ------------------------------------------------------------------ #
# Source tiers
# ------------------------------------------------------------------ #

def test_source_tier_by_outlet():
    assert get_source_tier("reuters.com") == 1
    assert get_source_tier("cnn.com") == 2
    assert get_source_tier("prnewswire.com") == 3
    assert get_source_tier("someblog.net") == 4


def test_source_tier_subdomains_lookalikes_and_empty():
    assert get_source_tier(" UK.Reuters.com ") == 1
    assert get_source_tier("notreuters.com") == 4
    assert get_source_tier("") == 4


def test_rank_articles_orders_by_tier_then_length_and_caps_each_outlet():
    articles = [
        {"source_name": "reuters.com", "word_count": 100},
        {"source_name": "someblog.net", "word_count": 1000},
        {"source_name": "reuters.com", "word_count": 300},
        {"source_name": "cnn.com", "word_count": 900},
        {"source_name": "reuters.com", "word_count": 200},
    ]
    ranked = rank_articles(articles)
    assert [(a["source_name"], a["word_count"]) for a in ranked] == [
        ("reuters.com", 300),
        ("reuters.com", 200),
        ("cnn.com", 900),
        ("someblog.net", 1000),
    ]


# ------------------------------------------------------------------ #
# Recency weighting
# ------------------------------------------------------------------ #

def test_decay_weight_halves_every_half_life():
    today = date(2024, 1, 31)
    assert _decay_weight(today, today, half_life=30) == 1.0
    assert _decay_weight(date(2024, 1, 1), today, half_life=30) == pytest.approx(0.5)
    assert _decay_weight(date(2023, 12, 2), today, half_life=30) == pytest.approx(0.25)
    assert _decay_weight(date(2024, 2, 5), today, half_life=30) == 1.0


def test_weighted_mean():
    assert _weighted_mean([80.0, 40.0], [1.0, 3.0]) == 50.0
    assert _weighted_mean([80.0, 40.0], [0.0, 0.0]) is None


# ------------------------------------------------------------------ #
# Rules the LLM's output must pass
# ------------------------------------------------------------------ #

def test_dimension_score_rejects_hedge_words():
    DimensionScore(**_dimension())
    with pytest.raises(ValidationError):
        DimensionScore(**_dimension(reasoning="Safety seems worse after several incidents this week."))


def test_dimension_score_rejects_out_of_range_score_and_missing_evidence():
    with pytest.raises(ValidationError):
        DimensionScore(**_dimension(score=101))
    with pytest.raises(ValidationError):
        DimensionScore(**_dimension(evidence_snippets=[]))


def test_overall_score_must_stay_near_dimension_mean():
    def city_score(overall: int) -> CityHealthScore:
        return CityHealthScore(
            city_id="test-city",
            city_name="Test City",
            scored_date=date(2024, 1, 15),
            generated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
            overall_score=overall,
            overall_confidence=0.8,
            dimensions=[
                _dimension(dimension="safety", score=40),
                _dimension(dimension="economy", score=60),
            ],
            data_sources=["GDELT"],
        )

    assert city_score(55).overall_score == 55  # mean is 50
    with pytest.raises(ValidationError):
        city_score(70)


def test_overall_score_tolerance_is_ten_points():
    dims = [
        _dimension(dimension="safety", score=40),
        _dimension(dimension="economy", score=60),
    ]
    base = {
        "city_id": "test-city",
        "city_name": "Test City",
        "scored_date": date(2024, 1, 15),
        "generated_at": datetime(2024, 1, 15, tzinfo=timezone.utc),
        "overall_confidence": 0.8,
        "dimensions": dims,
        "data_sources": ["GDELT"],
    }
    CityHealthScore(overall_score=60, **base)  # exactly 10 above the mean of 50
    with pytest.raises(ValidationError):
        CityHealthScore(overall_score=61, **base)


# ------------------------------------------------------------------ #
# Event deduplication
# ------------------------------------------------------------------ #

def test_deduplicate_merges_same_story_within_two_days():
    events = [
        {"event_date": "2024-01-01", "event_code": "141", "actor1": "POLICE",
         "actor2": "PROTESTER", "goldstein_scale": -6.5, "num_mentions": 10,
         "source_url": "https://a.example/1", "event_description": "Protest"},
        {"event_date": "2024-01-02", "event_code": "145", "actor1": "PROTESTER",
         "actor2": "", "goldstein_scale": -7.5, "num_mentions": 20,
         "source_url": "https://b.example/2", "event_description": "Protest turns violent"},
        {"event_date": "2024-01-10", "event_code": "141", "actor1": "POLICE",
         "actor2": "", "goldstein_scale": -6.5, "num_mentions": 5,
         "source_url": "https://c.example/3", "event_description": "Later protest"},
    ]
    stories = deduplicate_events(events)
    assert len(stories) == 2
    assert stories[0].total_mentions == 30
    assert stories[0].source_count == 2
    assert stories[0].primary_description == "Protest turns violent"
    assert stories[1].total_mentions == 5


def test_deduplicate_lists_most_credible_sources_first():
    events = [
        {"event_date": "2024-01-01", "event_code": "141", "actor1": "POLICE",
         "actor2": "", "goldstein_scale": -6.5, "num_mentions": 10,
         "source_url": "https://someblog.net/protest", "event_description": "Protest"},
        {"event_date": "2024-01-01", "event_code": "141", "actor1": "POLICE",
         "actor2": "", "goldstein_scale": -6.5, "num_mentions": 10,
         "source_url": "https://www.reuters.com/world/protest", "event_description": "Protest"},
    ]
    [story] = deduplicate_events(events)
    assert story.source_urls == [
        "https://www.reuters.com/world/protest",
        "https://someblog.net/protest",
    ]
