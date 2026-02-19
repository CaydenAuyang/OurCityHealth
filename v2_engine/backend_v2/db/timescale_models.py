"""
TimescaleDB Hypertable Models for V2 Engine

Stores daily aggregated city event metrics from GDELT for fast time-series queries.
The `daily_city_stats` table is converted into a TimescaleDB hypertable chunked by
1-week intervals.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend_v2.db.models import Base


class DailyCityStats(Base):
    """
    Daily aggregated event metrics for a city.

    One row per city per day.  Populated by the GDELT ingestion pipeline which
    rolls raw events up into daily summaries.

    Key metrics:
    - avg_goldstein:  Average Goldstein Scale across all events for the day.
                      Range roughly -10 (very hostile) to +10 (very cooperative).
    - total_mentions: Sum of NumMentions across all events.
    - event_count:    Number of distinct GDELT event rows matched to this city.
    - stability_score: Normalised 0-100 score derived from Goldstein + mention volume.
    """
    __tablename__ = "daily_city_stats"

    # Composite primary key: (day, city_id)
    day: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
        nullable=False,
    )
    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    # Aggregated metrics
    avg_goldstein: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_mentions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stability_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)

    # Breakdowns by CAMEO root code (top-level event categories)
    verbal_cooperation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    material_cooperation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verbal_conflict_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    material_conflict_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Source diversity
    unique_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Audit
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        UniqueConstraint("day", "city_id", name="uq_daily_city_stats_day_city"),
    )

    def __repr__(self) -> str:
        return (
            f"<DailyCityStats(day={self.day}, city_id={self.city_id}, "
            f"stability={self.stability_score:.1f})>"
        )


# ---------------------------------------------------------------
# CityEvent — individual raw GDELT events (V2.1)
# ---------------------------------------------------------------

class CityEvent(Base):
    """
    One row per GDELT event matched to a city.

    Populated by the ingestion script alongside the daily aggregates.
    The evaluator queries the top-N most-significant events to build
    an enriched, citable context for the LLM.
    """
    __tablename__ = "city_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    actor1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actor2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    goldstein_scale: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    num_mentions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_geo_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    action_geo_long: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "city_id", "event_date", "source_url",
            name="uq_city_events_city_date_url",
        ),
        Index("idx_city_events_city_date", "city_id", "event_date"),
        Index("idx_city_events_city_goldstein", "city_id", "goldstein_scale"),
    )

    def __repr__(self) -> str:
        return (
            f"<CityEvent(city_id={self.city_id}, date={self.event_date}, "
            f"code={self.event_code}, goldstein={self.goldstein_scale})>"
        )


# ---------------------------------------------------------------
# CityArticle — GKG article-level data (V2.2)
# ---------------------------------------------------------------

class CityArticle(Base):
    """
    One row per GKG article matched to a city.

    Populated by the ingestion script when querying gdelt-bq.gdeltv2.gkg_partitioned.
    Stores parsed tone, themes, persons, and organizations for the aggregator
    to mine named entities, dominant themes, and source tone analysis.
    """
    __tablename__ = "city_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
    )
    article_date: Mapped[date] = mapped_column(Date, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tone_overall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tone_positive: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tone_negative: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    themes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    persons: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organizations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "city_id", "article_date", "url",
            name="uq_city_articles_city_date_url",
        ),
        Index("idx_city_articles_city_date", "city_id", "article_date"),
        Index("idx_city_articles_city_source", "city_id", "source_name"),
    )

    def __repr__(self) -> str:
        return (
            f"<CityArticle(city_id={self.city_id}, date={self.article_date}, "
            f"source={self.source_name})>"
        )


# ---------------------------------------------------------------
# Helper: raw SQL to create the hypertable and continuous agg
# ---------------------------------------------------------------

TIMESCALE_INIT_SQL = [
    # Enable extension (idempotent)
    "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;",

    # Convert to hypertable chunked by 1-week intervals
    # `if_not_exists => true` makes it safe to re-run
    """
    SELECT create_hypertable(
        'daily_city_stats',
        by_range('day', INTERVAL '7 days'),
        if_not_exists => true
    );
    """,

    # Indexes tuned for typical access patterns
    "CREATE INDEX IF NOT EXISTS idx_dcs_city_day ON daily_city_stats (city_id, day DESC);",
    "CREATE INDEX IF NOT EXISTS idx_dcs_stability ON daily_city_stats (day DESC, stability_score);",
]
