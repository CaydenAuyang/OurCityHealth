#!/usr/bin/env python3
"""
GDELT Historical Data Ingestion Script

Iterates through the cities table, queries BigQuery for GDELT events within
a bounding box of each city, saves raw results as partitioned Parquet files,
and inserts daily aggregates into the TimescaleDB `daily_city_stats` hypertable.

Usage:
    # Full 5-year ingest for all cities (very large — use with care)
    python scripts/ingest_history.py --start 2020-01-01 --end 2025-01-01

    # Quick smoke-test: 2 cities, 1 month
    python scripts/ingest_history.py --start 2024-01-01 --end 2024-02-01 --limit 2

    # Dry-run: estimate BigQuery bytes only
    python scripts/ingest_history.py --start 2024-01-01 --end 2024-02-01 --limit 1 --dry-run

Requirements:
    - Docker containers running  (docker compose up -d)
    - pip install -r requirements_v2.txt
    - GCP credentials configured in .env
"""

import argparse
import asyncio
import logging
import math
import os
import sys
import time
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import text
from tqdm import tqdm
from dotenv import load_dotenv

# Add parent directory so imports work when invoked as a standalone script
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from backend_v2.db.session import async_session_factory, engine
from backend_v2.db.timescale_models import DailyCityStats, TIMESCALE_INIT_SQL
from backend_v2.ingestion.gdelt_client import GDELTClient, CityCoord, GDELT_COLUMNS
from backend_v2.ingestion.gkg_client import (
    GKGClient,
    parse_v2_tone,
    parse_v2_themes,
    parse_v2_persons,
    parse_v2_organizations,
)
from data_pipeline.etl.parquet_writer import save_city_parquet

# ------------------------------------------------------------------ #
# Logging
# ------------------------------------------------------------------ #
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "ingest_history.log"),
    ],
)
logger = logging.getLogger("ingest_history")


# ------------------------------------------------------------------ #
# Database bootstrap: create table + hypertable if needed
# ------------------------------------------------------------------ #

async def ensure_timescale_schema() -> None:
    """
    Create the daily_city_stats table and convert it to a TimescaleDB
    hypertable.  Safe to call repeatedly.
    """
    async with engine.connect() as conn:
        # PostGIS was already enabled by Phase 1 init_db; just need TimescaleDB
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        await conn.commit()

        # Create the raw table first (if not exists)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS daily_city_stats (
                day              DATE         NOT NULL,
                city_id          UUID         NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
                avg_goldstein    DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                total_mentions   INTEGER      NOT NULL DEFAULT 0,
                event_count      INTEGER      NOT NULL DEFAULT 0,
                stability_score  DOUBLE PRECISION NOT NULL DEFAULT 50.0,
                verbal_cooperation_count  INTEGER NOT NULL DEFAULT 0,
                material_cooperation_count INTEGER NOT NULL DEFAULT 0,
                verbal_conflict_count     INTEGER NOT NULL DEFAULT 0,
                material_conflict_count   INTEGER NOT NULL DEFAULT 0,
                unique_sources   INTEGER      NOT NULL DEFAULT 0,
                ingested_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (day, city_id)
            );
        """))
        await conn.commit()

        # Enable TimescaleDB + hypertable conversion
        for stmt in TIMESCALE_INIT_SQL:
            try:
                await conn.execute(text(stmt))
                await conn.commit()
            except Exception as e:
                # Tolerate "already a hypertable" or extension-not-available
                await conn.rollback()
                if "already a hypertable" in str(e).lower():
                    logger.debug("Hypertable already exists — skipping")
                elif "timescaledb" in str(e).lower():
                    logger.warning(
                        "TimescaleDB extension not available — table will "
                        "work as a regular PostgreSQL table.  Install "
                        "TimescaleDB in Docker for hypertable features."
                    )
                    break
                else:
                    logger.warning("Skipping TimescaleDB statement: %s", e)

    # V2.2: city_articles table
    async with engine.connect() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS city_articles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
                article_date DATE NOT NULL,
                url TEXT NOT NULL,
                source_name VARCHAR(255),
                tone_overall DOUBLE PRECISION,
                tone_positive DOUBLE PRECISION,
                tone_negative DOUBLE PRECISION,
                themes TEXT,
                persons TEXT,
                organizations TEXT,
                word_count INTEGER,
                CONSTRAINT uq_city_articles_city_date_url
                    UNIQUE (city_id, article_date, url)
            );
        """))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_city_articles_city_date "
            "ON city_articles (city_id, article_date);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_city_articles_city_source "
            "ON city_articles (city_id, source_name);"
        ))
        await conn.commit()

    logger.info("\u2705 daily_city_stats + city_articles tables ready")


# ------------------------------------------------------------------ #
# Load cities from PostGIS
# ------------------------------------------------------------------ #

async def load_cities(limit: Optional[int] = None) -> list[CityCoord]:
    """Read city coordinates from the cities table."""
    q = """
        SELECT id::text, name, ST_Y(location) AS lat, ST_X(location) AS lng
        FROM cities
        ORDER BY population DESC
    """
    if limit:
        q += f" LIMIT {int(limit)}"

    async with async_session_factory() as session:
        result = await session.execute(text(q))
        rows = result.fetchall()

    cities = [CityCoord(city_id=r[0], name=r[1], lat=r[2], lng=r[3]) for r in rows]
    logger.info("Loaded %d cities from database", len(cities))
    return cities


# ------------------------------------------------------------------ #
# Aggregation: raw GDELT rows → DailyCityStats
# ------------------------------------------------------------------ #

def _cameo_root(code) -> str:
    """Extract the first two characters of a CAMEO EventCode."""
    try:
        return str(code)[:2]
    except Exception:
        return ""


def _goldstein_to_stability(avg_goldstein: float, event_count: int) -> float:
    """
    Map average Goldstein score to a 0-100 stability index.

    Goldstein ranges roughly -10 to +10.
    We linearly map: -10 → 0, 0 → 50, +10 → 100
    Then clamp and apply a mild confidence dampening when event_count is low.
    """
    raw = (avg_goldstein + 10.0) * 5.0  # -10→0, +10→100
    raw = max(0.0, min(100.0, raw))

    # Shrink toward 50 when evidence is sparse
    confidence = min(1.0, event_count / 20.0)
    return 50.0 + (raw - 50.0) * confidence


def aggregate_daily(df: pd.DataFrame, city_id: str) -> list[dict]:
    """
    Aggregate a raw GDELT DataFrame into one row per day.

    Returns a list of dicts ready for bulk-insert into daily_city_stats.
    """
    if df.empty:
        return []

    # Parse SQLDATE (INT64 YYYYMMDD) into a proper date
    df = df.copy()
    df["day"] = pd.to_datetime(df["SQLDATE"].astype(str), format="%Y%m%d", errors="coerce").dt.date
    df = df.dropna(subset=["day"])

    records: list[dict] = []
    for day, grp in df.groupby("day"):
        goldstein_vals = pd.to_numeric(grp["GoldsteinScale"], errors="coerce").dropna()
        avg_goldstein = float(goldstein_vals.mean()) if len(goldstein_vals) else 0.0

        mentions = pd.to_numeric(grp["NumMentions"], errors="coerce").fillna(0)
        total_mentions = int(mentions.sum())
        event_count = len(grp)

        roots = grp["EventRootCode"].apply(_cameo_root) if "EventRootCode" in grp.columns else pd.Series(dtype=str)
        verbal_coop = int((roots.isin(["01", "02", "03", "04", "05"])).sum())
        material_coop = int((roots.isin(["06", "07", "08"])).sum())
        verbal_conf = int((roots.isin(["09", "10", "11", "12", "13"])).sum())
        material_conf = int((roots.isin(["14", "15", "16", "17", "18", "19", "20"])).sum())

        unique_sources = int(pd.to_numeric(grp["NumSources"], errors="coerce").fillna(0).sum())

        stability = _goldstein_to_stability(avg_goldstein, event_count)

        records.append({
            "day": day,
            "city_id": city_id,
            "avg_goldstein": round(avg_goldstein, 4),
            "total_mentions": total_mentions,
            "event_count": event_count,
            "stability_score": round(stability, 2),
            "verbal_cooperation_count": verbal_coop,
            "material_cooperation_count": material_coop,
            "verbal_conflict_count": verbal_conf,
            "material_conflict_count": material_conf,
            "unique_sources": unique_sources,
        })

    return records


# ------------------------------------------------------------------ #
# Insert aggregates into TimescaleDB
# ------------------------------------------------------------------ #

async def upsert_daily_stats(records: list[dict]) -> int:
    """
    Bulk upsert daily aggregates.  Uses ON CONFLICT to update if the same
    (day, city_id) is re-ingested.
    """
    if not records:
        return 0

    async with async_session_factory() as session:
        for rec in records:
            await session.execute(
                text("""
                    INSERT INTO daily_city_stats (
                        day, city_id, avg_goldstein, total_mentions, event_count,
                        stability_score,
                        verbal_cooperation_count, material_cooperation_count,
                        verbal_conflict_count, material_conflict_count,
                        unique_sources
                    ) VALUES (
                        :day, :city_id, :avg_goldstein, :total_mentions, :event_count,
                        :stability_score,
                        :verbal_cooperation_count, :material_cooperation_count,
                        :verbal_conflict_count, :material_conflict_count,
                        :unique_sources
                    )
                    ON CONFLICT (day, city_id) DO UPDATE SET
                        avg_goldstein   = EXCLUDED.avg_goldstein,
                        total_mentions  = EXCLUDED.total_mentions,
                        event_count     = EXCLUDED.event_count,
                        stability_score = EXCLUDED.stability_score,
                        verbal_cooperation_count  = EXCLUDED.verbal_cooperation_count,
                        material_cooperation_count = EXCLUDED.material_cooperation_count,
                        verbal_conflict_count     = EXCLUDED.verbal_conflict_count,
                        material_conflict_count   = EXCLUDED.material_conflict_count,
                        unique_sources  = EXCLUDED.unique_sources,
                        ingested_at     = CURRENT_TIMESTAMP
                """),
                rec,
            )
        await session.commit()

    return len(records)


# ------------------------------------------------------------------ #
# Insert raw events into city_events (V2.1)
# ------------------------------------------------------------------ #

async def insert_raw_events(df: pd.DataFrame, city_id: str, batch_size: int = 1000) -> int:
    """
    Bulk-insert individual GDELT rows into the city_events table.

    Uses ON CONFLICT DO NOTHING on (city_id, event_date, source_url) so
    re-runs are safe and idempotent.

    Returns the number of rows sent (actual inserts may be fewer due to
    duplicate skipping).
    """
    if df.empty:
        return 0

    df = df.copy()
    df["_parsed_date"] = pd.to_datetime(
        df["SQLDATE"].astype(str), format="%Y%m%d", errors="coerce"
    ).dt.date
    df = df.dropna(subset=["_parsed_date"])

    rows_sent = 0

    async with async_session_factory() as session:
        batch: list[dict] = []
        for _, row in df.iterrows():
            batch.append({
                "city_id": city_id,
                "event_date": row["_parsed_date"],
                "actor1": _safe_str(row.get("Actor1Name")),
                "actor2": _safe_str(row.get("Actor2Name")),
                "event_code": _safe_str(row.get("EventCode")),
                "goldstein_scale": _safe_float(row.get("GoldsteinScale")),
                "num_mentions": _safe_int(row.get("NumMentions")),
                "source_url": _safe_str(row.get("SOURCEURL")),
                "action_geo_lat": _safe_float(row.get("ActionGeo_Lat")),
                "action_geo_long": _safe_float(row.get("ActionGeo_Long")),
            })
            if len(batch) >= batch_size:
                await _flush_event_batch(session, batch)
                rows_sent += len(batch)
                batch = []

        if batch:
            await _flush_event_batch(session, batch)
            rows_sent += len(batch)

        await session.commit()

    return rows_sent


async def _flush_event_batch(session, batch: list[dict]) -> None:
    """Execute a batch INSERT … ON CONFLICT DO NOTHING."""
    for rec in batch:
        await session.execute(
            text("""
                INSERT INTO city_events (
                    city_id, event_date, actor1, actor2, event_code,
                    goldstein_scale, num_mentions, source_url,
                    action_geo_lat, action_geo_long
                ) VALUES (
                    :city_id, :event_date, :actor1, :actor2, :event_code,
                    :goldstein_scale, :num_mentions, :source_url,
                    :action_geo_lat, :action_geo_long
                )
                ON CONFLICT (city_id, event_date, source_url) DO NOTHING
            """),
            rec,
        )


def _safe_str(val) -> str:
    """Coerce to str or None, handling NaN / NaT."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    return str(val).strip() or None


def _safe_float(val) -> float:
    """Coerce to float or None."""
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> int:
    """Coerce to int or None."""
    try:
        f = float(val)
        return None if math.isnan(f) else int(f)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ #
# Insert GKG articles into city_articles (V2.2)
# ------------------------------------------------------------------ #

async def insert_gkg_articles(
    df: pd.DataFrame, city_id: str, batch_size: int = 500
) -> int:
    """
    Parse GKG rows and batch-insert into city_articles.

    Uses ON CONFLICT DO NOTHING on (city_id, article_date, url).
    """
    if df.empty:
        return 0

    rows_sent = 0
    async with async_session_factory() as session:
        batch: list[dict] = []
        for _, row in df.iterrows():
            url = _safe_str(row.get("DocumentIdentifier"))
            if not url:
                continue

            # Parse DATE column (int64 YYYYMMDDHHMMSS) to date
            raw_date = row.get("DATE")
            try:
                date_str = str(int(raw_date))[:8]
                article_date = pd.to_datetime(date_str, format="%Y%m%d").date()
            except (ValueError, TypeError):
                continue

            tone_data = parse_v2_tone(str(row.get("V2Tone", "")))
            themes_raw = parse_v2_themes(str(row.get("V2Themes", "")))
            persons_raw = parse_v2_persons(str(row.get("V2Persons", "")))
            orgs_raw = parse_v2_organizations(str(row.get("V2Organizations", "")))

            batch.append({
                "city_id": city_id,
                "article_date": article_date,
                "url": url,
                "source_name": _safe_str(row.get("SourceCommonName")),
                "tone_overall": tone_data.get("overall"),
                "tone_positive": tone_data.get("positive"),
                "tone_negative": tone_data.get("negative"),
                "themes": ";".join(themes_raw)[:5000] if themes_raw else None,
                "persons": ";".join(persons_raw)[:5000] if persons_raw else None,
                "organizations": ";".join(orgs_raw)[:5000] if orgs_raw else None,
                "word_count": tone_data.get("word_count"),
            })

            if len(batch) >= batch_size:
                await _flush_article_batch(session, batch)
                rows_sent += len(batch)
                batch = []

        if batch:
            await _flush_article_batch(session, batch)
            rows_sent += len(batch)

        await session.commit()

    return rows_sent


async def _flush_article_batch(session, batch: list[dict]) -> None:
    """Execute a batch INSERT ... ON CONFLICT DO NOTHING for articles."""
    for rec in batch:
        await session.execute(
            text("""
                INSERT INTO city_articles (
                    city_id, article_date, url, source_name,
                    tone_overall, tone_positive, tone_negative,
                    themes, persons, organizations, word_count
                ) VALUES (
                    :city_id, :article_date, :url, :source_name,
                    :tone_overall, :tone_positive, :tone_negative,
                    :themes, :persons, :organizations, :word_count
                )
                ON CONFLICT (city_id, article_date, url) DO NOTHING
            """),
            rec,
        )


# ------------------------------------------------------------------ #
# Main pipeline
# ------------------------------------------------------------------ #

async def run_pipeline(
    start_date: str,
    end_date: str,
    limit: Optional[int] = None,
    radius_km: float = 50.0,
    chunk_months: int = 3,
    dry_run: bool = False,
    skip_gkg: bool = False,
) -> None:
    t0 = time.time()

    print("\n" + "=" * 64)
    print("  GDELT HISTORICAL INGESTION PIPELINE")
    print("=" * 64)
    print(f"  Date range : {start_date} \u2192 {end_date}")
    print(f"  Radius     : {radius_km} km")
    print(f"  Chunk size : {chunk_months} month(s)")
    if limit:
        print(f"  City limit : {limit}")
    if dry_run:
        print("  MODE       : DRY RUN (cost estimation only)")
    if skip_gkg:
        print("  GKG        : SKIPPED (--skip-gkg)")
    print("=" * 64 + "\n")

    # 1 — Bootstrap schema
    logger.info("Ensuring TimescaleDB schema…")
    await ensure_timescale_schema()

    # 2 — Load cities
    cities = await load_cities(limit=limit)
    if not cities:
        logger.error("No cities in database. Run v2_ingest_geo.py first.")
        return

    # 3 — Initialise GDELT client (and GKG client if not skipped)
    gdelt = GDELTClient()
    gkg: Optional[GKGClient] = None
    if not skip_gkg:
        try:
            gkg = GKGClient()
        except Exception:
            logger.warning("GKG client init failed \u2014 skipping GKG ingestion")

    # 4 \u2014 Dry-run cost check
    if dry_run:
        sample = cities[0]
        est = gdelt.estimate_bytes(
            lat=sample.lat, lng=sample.lng,
            start_date=start_date, end_date=end_date,
            radius_km=radius_km,
        )
        est_gb = est / (1024 ** 3)
        total_est_gb = est_gb * len(cities)
        print(f"\n  Sample city       : {sample.name}")
        print(f"  Bytes (1 city)    : {est_gb:.2f} GB")
        print(f"  Est total ({len(cities)} cities): {total_est_gb:.1f} GB")
        print(f"  BQ free tier      : 1,000 GB / month")
        print(f"  Est cost (>1 TB)  : ${max(0, total_est_gb - 1000) * 5:.2f}")
        return

    # 5 — Iterate cities
    total_events = 0
    total_days_inserted = 0
    total_raw_inserted = 0
    total_gkg_articles = 0
    total_gkg_inserted = 0
    gkg_unique_sources: set = set()
    failures: list[str] = []

    for city in tqdm(cities, desc="Cities", unit="city"):
        try:
            df = gdelt.query_city_events_chunked(
                lat=city.lat,
                lng=city.lng,
                start_date=start_date,
                end_date=end_date,
                chunk_months=chunk_months,
                radius_km=radius_km,
            )

            if df.empty:
                logger.info("%s: 0 events", city.name)
                continue

            total_events += len(df)

            # 5a — Save raw to Parquet (partitioned by month)
            df_copy = df.copy()
            df_copy["_parsed_date"] = pd.to_datetime(
                df_copy["SQLDATE"].astype(str), format="%Y%m%d", errors="coerce"
            )
            df_copy = df_copy.dropna(subset=["_parsed_date"])

            for (year, month), month_df in df_copy.groupby(
                [df_copy["_parsed_date"].dt.year, df_copy["_parsed_date"].dt.month]
            ):
                save_city_parquet(
                    month_df.drop(columns=["_parsed_date"]),
                    city_id=city.city_id,
                    year=int(year),
                    month=int(month),
                )

            # 5b — Aggregate and upsert into TimescaleDB
            records = aggregate_daily(df, city.city_id)
            inserted = await upsert_daily_stats(records)
            total_days_inserted += inserted

            # 5c — Insert raw events into city_events table (V2.1)
            raw_inserted = await insert_raw_events(df, city.city_id)
            total_raw_inserted += raw_inserted

            logger.info(
                "%s: %d events \u2192 %d daily rows, %d raw events",
                city.name, len(df), inserted, raw_inserted,
            )

            # 5d — GKG article ingestion (V2.2)
            gkg_inserted = 0
            if gkg is not None:
                try:
                    gkg_df = gkg.query_city_articles(
                        lat=city.lat, lng=city.lng,
                        start_date=start_date, end_date=end_date,
                        radius_km=radius_km,
                        limit=500,
                    )
                    if not gkg_df.empty:
                        total_gkg_articles += len(gkg_df)
                        # Track unique sources
                        if "SourceCommonName" in gkg_df.columns:
                            for sn in gkg_df["SourceCommonName"].dropna().unique():
                                gkg_unique_sources.add(str(sn).lower().strip())
                        gkg_inserted = await insert_gkg_articles(
                            gkg_df, city.city_id
                        )
                        total_gkg_inserted += gkg_inserted
                    logger.info(
                        "%s: GKG %d articles \u2192 %d inserted",
                        city.name, len(gkg_df), gkg_inserted,
                    )
                except Exception:
                    logger.exception(
                        "GKG ingestion failed for %s", city.name
                    )

        except Exception:
            logger.exception("Failed processing %s", city.name)
            failures.append(city.name)
            continue

    elapsed = time.time() - t0

    # 6 — Summary
    print("\n" + "=" * 64)
    print("  INGESTION COMPLETE")
    print("=" * 64)
    print(f"  Cities processed    : {len(cities)}")
    print(f"  Total GDELT events  : {total_events:,}")
    print(f"  Daily rows upserted : {total_days_inserted:,}")
    print(f"  Raw events inserted : {total_raw_inserted:,}")
    print(f"  GKG articles found  : {total_gkg_articles:,}")
    print(f"  GKG articles inserted: {total_gkg_inserted:,}")
    print(f"  Unique sources      : {len(gkg_unique_sources):,}")
    print(f"  Failures            : {len(failures)}")
    if failures:
        print(f"  Failed cities       : {', '.join(failures[:20])}")
    print(f"  Elapsed             : {elapsed:.0f}s ({elapsed / 60:.1f} min)")
    print("=" * 64 + "\n")


# ------------------------------------------------------------------ #
# CLI
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(
        description="Ingest historical GDELT data for V2 cities."
    )
    parser.add_argument(
        "--start", required=True,
        help="Start date inclusive (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end", required=True,
        help="End date exclusive (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max cities to process (default: all)",
    )
    parser.add_argument(
        "--radius", type=float, default=50.0,
        help="Bounding-box radius in km (default: 50)",
    )
    parser.add_argument(
        "--chunk-months", type=int, default=3,
        help="Split date range into N-month BigQuery chunks (default: 3)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Only estimate BigQuery cost — do not fetch data",
    )
    parser.add_argument(
        "--skip-gkg", action="store_true",
        help="Skip GKG article ingestion (saves BigQuery quota)",
    )
    args = parser.parse_args()

    asyncio.run(run_pipeline(
        start_date=args.start,
        end_date=args.end,
        limit=args.limit,
        radius_km=args.radius,
        chunk_months=args.chunk_months,
        dry_run=args.dry_run,
        skip_gkg=args.skip_gkg,
    ))


if __name__ == "__main__":
    main()
