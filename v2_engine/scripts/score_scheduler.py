#!/usr/bin/env python3
"""
Pre-compute city health scores for all cities with GDELT data.

Queries the existing scoring pipeline (aggregator + evaluator) for each
city/date combination and persists the result in the city_scores table so
the API can serve them instantly.

Usage:
    # Score all cities with GDELT data for today
    python3 scripts/score_scheduler.py

    # Score all cities for a specific date
    python3 scripts/score_scheduler.py --date 2024-01-15

    # Score one city only
    python3 scripts/score_scheduler.py --city shanghai --date 2024-01-15

    # Backfill weekly scores for a date range
    python3 scripts/score_scheduler.py --backfill --start 2024-01-01 --end 2024-01-31 --interval 7

    # Re-score everything (overwrite existing scores)
    python3 scripts/score_scheduler.py --backfill --start 2024-01-01 --end 2024-01-31 --force
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure v2_engine/ is on sys.path so "backend_v2" imports resolve
# regardless of where the script is invoked from.
_v2_root = str(Path(__file__).resolve().parent.parent)
if _v2_root not in sys.path:
    sys.path.insert(0, _v2_root)

from dotenv import load_dotenv

load_dotenv(os.path.join(_v2_root, ".env"))

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("score_scheduler")


async def main(args: argparse.Namespace) -> None:
    from sqlalchemy import text as sa_text, select

    from backend_v2.db.session import async_session_factory, init_db
    from backend_v2.db.timescale_models import CityScore
    from backend_v2.scoring.aggregator import ScoreAggregator
    from backend_v2.scoring.evaluator import ScoreEvaluator

    await init_db()

    model_name = os.environ.get("OPENAI_MODEL", "gpt-4o")
    evaluator = ScoreEvaluator(
        model=model_name,
        max_retries=int(os.environ.get("SCORING_MAX_RETRIES", "3")),
    )

    async with async_session_factory() as session:
        # --- Discover cities with GDELT data ---
        if args.city:
            city_rows = (
                await session.execute(
                    sa_text(
                        "SELECT DISTINCT c.id::text, c.name, c.country_code "
                        "FROM daily_city_stats dcs "
                        "JOIN cities c ON dcs.city_id = c.id "
                        "WHERE LOWER(c.name) = :cname "
                        "LIMIT 1"
                    ),
                    {"cname": args.city.strip().lower()},
                )
            ).fetchall()
        else:
            city_rows = (
                await session.execute(
                    sa_text(
                        "SELECT DISTINCT c.id::text, c.name, c.country_code "
                        "FROM daily_city_stats dcs "
                        "JOIN cities c ON dcs.city_id = c.id"
                    )
                )
            ).fetchall()

        if not city_rows:
            logger.error("No cities with GDELT data found.")
            return

        # --- Determine dates to score ---
        if args.backfill:
            if not args.start or not args.end:
                logger.error("--backfill requires --start and --end")
                return
            start = date.fromisoformat(args.start)
            end = date.fromisoformat(args.end)
            interval = args.interval
            dates: list[date] = []
            current = start
            while current <= end:
                dates.append(current)
                current += timedelta(days=interval)
        else:
            target = date.fromisoformat(args.date) if args.date else date.today()
            dates = [target]

        total = len(city_rows) * len(dates)
        completed = 0
        failed = 0
        skipped = 0

        logger.info(
            "Scoring %d cities x %d dates = %d scores  |  dates: %s → %s  |  force=%s",
            len(city_rows), len(dates), total,
            dates[0], dates[-1], args.force,
        )
        print("=" * 64)

        for city_id, city_name, country_code in city_rows:
            for scored_date in dates:
                label = f"{city_name} / {scored_date}"

                # --- Skip check (unless --force) ---
                if not args.force:
                    existing = await session.execute(
                        select(CityScore).where(
                            CityScore.city_id == city_id,
                            CityScore.scored_date == scored_date,
                        )
                    )
                    if existing.scalar_one_or_none() is not None:
                        skipped += 1
                        print(f"  SKIP  {label}  (already scored)")
                        continue

                # --- Run the scoring pipeline ---
                try:
                    aggregator = ScoreAggregator(session)
                    enriched_ctx = await aggregator.get_enriched_context(
                        city_id=city_id,
                        city_name=city_name,
                        country_code=country_code,
                        scored_date=scored_date,
                    )

                    score = evaluator.calculate_score(enriched_ctx)

                    score_json = json.dumps(score.model_dump(), default=str)

                    # Upsert into city_scores
                    await session.execute(
                        sa_text("""
                            INSERT INTO city_scores
                                (city_id, city_name, scored_date, overall_score,
                                 overall_confidence, score_json, model_used)
                            VALUES (:cid, :cname, :sd, :os, :oc, :sj, :mu)
                            ON CONFLICT (city_id, scored_date) DO UPDATE SET
                                city_name        = EXCLUDED.city_name,
                                overall_score    = EXCLUDED.overall_score,
                                overall_confidence = EXCLUDED.overall_confidence,
                                score_json       = EXCLUDED.score_json,
                                model_used       = EXCLUDED.model_used,
                                computed_at      = CURRENT_TIMESTAMP
                        """),
                        {
                            "cid": city_id,
                            "cname": city_name,
                            "sd": scored_date,
                            "os": float(score.overall_score),
                            "oc": float(score.overall_confidence),
                            "sj": score_json,
                            "mu": model_name,
                        },
                    )
                    await session.commit()

                    completed += 1
                    print(f"  OK    {label}  →  score={score.overall_score}")

                    # Rate-limit safety
                    await asyncio.sleep(2)

                except Exception as exc:
                    failed += 1
                    logger.error("FAIL  %s  →  %s", label, exc, exc_info=True)
                    await session.rollback()

        print("=" * 64)
        print(f"Done:  {completed} scored  |  {skipped} skipped  |  {failed} failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pre-compute city health scores and store in city_scores.",
    )
    parser.add_argument(
        "--date",
        help="Target date YYYY-MM-DD (defaults to today).",
    )
    parser.add_argument(
        "--city",
        help="Score only this city (match by name, case-insensitive).",
    )
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Backfill a date range instead of a single date.",
    )
    parser.add_argument(
        "--start",
        help="Backfill start date YYYY-MM-DD (requires --backfill).",
    )
    parser.add_argument(
        "--end",
        help="Backfill end date YYYY-MM-DD (requires --backfill).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=7,
        help="Days between backfill scores (default: 7).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scores (upsert instead of skip).",
    )
    asyncio.run(main(parser.parse_args()))
