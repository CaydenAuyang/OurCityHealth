#!/usr/bin/env python3
"""
Snapshot the live API into static JSON files so the public GitHub Pages
deploy works without a backend.

Outputs are written to:
    v2_engine/frontend_v2/public/snapshot/

What gets snapshotted (auto-discovered from the database, not hardcoded):
    cities.json                            all 1,000 cities with coords
    data-coverage.json                     timeline data dots
    cities-scores-{date}.json              for every distinct day in
                                           daily_city_stats (globe colors)
    score-{cityId}-{date}.json             for every (city,date) pair in
                                           city_scores (LLM detail panels)
    sources-{cityId}-{date}.json           same pairs (GKG source breakdown)
    history-{cityId}.json                  full daily_city_stats series per
                                           city (powers 90-day sparkline)
    manifest.json                          inventory of what's bundled,
                                           grouped by city for nearest-date
                                           lookup on the client

The frontend client.ts checks for these files first and only calls the
live API as a fallback, so the demo works fully offline.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import date, timedelta
from pathlib import Path
from typing import Any

API_BASE = "http://localhost:8001"
OUT_DIR = Path(__file__).resolve().parent.parent / "frontend_v2" / "public" / "snapshot"

# --------------------------------------------------------------------- #
# HTTP helper
# --------------------------------------------------------------------- #

def get_json(path: str, retries: int = 3) -> Any:
    """GET a JSON endpoint with simple retry."""
    url = f"{API_BASE}{path}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (404, 422):
                return None  # don't retry on definite misses
            print(f"  HTTP {e.code} on {path}, retry {attempt + 1}/{retries}", flush=True)
            time.sleep(1)
        except Exception as e:
            print(f"  Error on {path}: {e}", flush=True)
            if attempt == retries - 1:
                return None
            time.sleep(1)
    return None


def write_json(filename: str, data: Any) -> int:
    """Write JSON file, return file size in bytes."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / filename
    path.write_text(json.dumps(data, separators=(",", ":")))
    return path.stat().st_size


# --------------------------------------------------------------------- #
# DB discovery (we go directly to Postgres for the inventory queries
# because we want every (city,date) tuple, which there's no public API for)
# --------------------------------------------------------------------- #

async def discover_inventory() -> tuple[list[str], list[tuple[str, str]], list[str]]:
    """
    Returns:
        (color_dates, score_pairs, history_city_ids)
        color_dates: ISO dates where daily_city_stats has any row
        score_pairs: (city_id, scored_date) tuples present in city_scores
        history_city_ids: distinct city_ids that have any daily_city_stats rows
                         (so we know which cities need a history snapshot)
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from backend_v2.db.session import async_session_factory
    from sqlalchemy import text

    async with async_session_factory() as session:
        rows = await session.execute(
            text("SELECT DISTINCT day FROM daily_city_stats ORDER BY day")
        )
        color_dates = [r.day.isoformat() for r in rows.fetchall()]

        rows = await session.execute(
            text(
                "SELECT city_id, scored_date FROM city_scores "
                "ORDER BY scored_date, city_id"
            )
        )
        score_pairs = [(r.city_id, r.scored_date.isoformat()) for r in rows.fetchall()]

        rows = await session.execute(
            text(
                "SELECT DISTINCT city_id::text AS cid FROM daily_city_stats"
            )
        )
        history_city_ids = [r.cid for r in rows.fetchall()]

    return color_dates, score_pairs, history_city_ids


# --------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------- #

def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUT_DIR}", flush=True)
    print(f"API base:         {API_BASE}\n", flush=True)

    # -- 1. Cities (1,000 entries, ~146 KB) --
    print("[1/5] cities.json", flush=True)
    cities = get_json("/api/v2/cities")
    if cities is None:
        print("ERROR: /api/v2/cities failed; backend probably not running", flush=True)
        return 1
    size = write_json("cities.json", cities)
    print(f"      {len(cities)} cities, {size / 1024:.1f} KB", flush=True)

    # -- 2. Data coverage (powers timeline data dots) --
    print("\n[2/5] data-coverage.json", flush=True)
    coverage = get_json("/api/v2/data-coverage")
    if coverage is not None:
        size = write_json("data-coverage.json", coverage)
        print(f"      {len(coverage.get('coverage', []))} days, {size / 1024:.1f} KB", flush=True)

    # -- 3. Discover what to snapshot from the DB itself --
    print("\n[3/6] Discovering inventory from database…", flush=True)
    color_dates, score_pairs, history_city_ids = asyncio.run(discover_inventory())
    print(f"      {len(color_dates)} dates with raw GDELT data (globe colors)", flush=True)
    print(f"      {len(score_pairs)} (city,date) pairs with LLM scores (detail panels)", flush=True)
    print(f"      {len(history_city_ids)} cities with history (sparklines)", flush=True)

    # -- 4. Snapshot cities-scores for every data date (globe colors) --
    print(f"\n[4/6] cities-scores-{{date}}.json × {len(color_dates)}", flush=True)
    total_color_bytes = 0
    color_dates_written: list[str] = []
    for i, d in enumerate(color_dates, 1):
        scores = get_json(f"/api/v2/cities/scores?date={d}&window_days=30")
        if scores is None:
            continue
        size = write_json(f"cities-scores-{d}.json", scores)
        total_color_bytes += size
        color_dates_written.append(d)
        if i % 20 == 0:
            print(f"      ... {i}/{len(color_dates)}", flush=True)
    print(f"      {len(color_dates_written)} files, {total_color_bytes / 1024:.1f} KB total", flush=True)

    # -- 5. Snapshot score+sources for every (city,date) LLM pair --
    print(f"\n[5/6] score+sources files × {len(score_pairs)}", flush=True)
    total_detail_bytes = 0
    pairs_written: list[tuple[str, str]] = []
    for i, (cid, d) in enumerate(score_pairs, 1):
        score = get_json(f"/api/v2/score/{cid}?date={d}")
        if score is not None:
            total_detail_bytes += write_json(f"score-{cid}-{d}.json", score)

        end = date.fromisoformat(d)
        start = end - timedelta(days=90)
        sources = get_json(
            f"/api/v2/sources/{cid}?start={start.isoformat()}&end={end.isoformat()}"
        )
        if sources is not None:
            total_detail_bytes += write_json(f"sources-{cid}-{d}.json", sources)

        if score is not None:
            pairs_written.append((cid, d))
        if i % 20 == 0:
            print(f"      ... {i}/{len(score_pairs)}", flush=True)
    print(f"      {len(pairs_written)} pairs, {total_detail_bytes / 1024:.1f} KB total", flush=True)

    # -- 6. Snapshot full history per city (powers the 90-day sparkline) --
    # We grab a wide window (5 years) so the client can slice locally.
    print(f"\n[6/6] history-{{cityId}}.json × {len(history_city_ids)}", flush=True)
    total_history_bytes = 0
    history_cities_written: list[str] = []
    for cid in history_city_ids:
        # Wide range; 1825 = 5 years
        history = get_json(
            f"/api/v2/score/{cid}/history?start=2014-01-01&end=2026-12-31&limit=1825"
        )
        if history is None:
            continue
        total_history_bytes += write_json(f"history-{cid}.json", history)
        history_cities_written.append(cid)
    print(f"      {len(history_cities_written)} cities, {total_history_bytes / 1024:.1f} KB total", flush=True)

    # -- Manifest --
    # Group scored pairs by city so the client can do nearest-date lookup
    # when an exact (city, date) snapshot is missing.
    by_city: dict[str, list[str]] = {}
    for c, d in pairs_written:
        by_city.setdefault(c, []).append(d)
    for c in by_city:
        by_city[c].sort()

    manifest = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "city_count": len(cities),
        "color_dates": color_dates_written,
        "scored_pairs": [{"city_id": c, "date": d} for c, d in pairs_written],
        "scored_dates_by_city": by_city,
        "history_city_ids": history_cities_written,
    }
    write_json("manifest.json", manifest)

    total_files = len(list(OUT_DIR.glob("*.json")))
    total_size_mb = sum(p.stat().st_size for p in OUT_DIR.glob("*.json")) / (1024 * 1024)
    print(f"\nDone. {total_files} files, {total_size_mb:.2f} MB total in {OUT_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
