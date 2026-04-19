#!/usr/bin/env python3
"""
Snapshot live API responses into static JSON files that the frontend
serves directly (no backend needed for the public demo).

Outputs are written to:
    v2_engine/frontend_v2/public/snapshot/

Files generated:
    cities.json
    data-coverage.json
    cities-scores-{date}.json          for each "feature date"
    score-{cityId}-{date}.json         for each scored city × feature date
    sources-{cityId}-{date}.json       for each scored city × feature date
    manifest.json                      lists what dates/cities are snapshotted

The frontend client.ts checks for these files first and only calls the
live API if the snapshot is missing.
"""
from __future__ import annotations

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

# Dates the frontend is most likely to land on. Each one becomes a complete
# snapshot (globe colors + per-city scores + per-city sources).
FEATURE_DATES = [
    "2024-01-14",
    "2024-01-15",  # default date in App.tsx
    "2024-01-21",
    "2024-01-28",
    "2024-01-07",
]


def get_json(path: str, retries: int = 3) -> Any:
    """GET a JSON endpoint with simple retry."""
    url = f"{API_BASE}{path}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (404, 422) and attempt == retries - 1:
                return None
            print(f"  HTTP {e.code} on {path}, retry {attempt + 1}/{retries}")
            time.sleep(1)
        except Exception as e:
            print(f"  Error on {path}: {e}")
            if attempt == retries - 1:
                return None
            time.sleep(1)
    return None


def write_json(filename: str, data: Any) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / filename
    path.write_text(json.dumps(data, separators=(",", ":")))
    size_kb = path.stat().st_size / 1024
    print(f"  wrote {filename} ({size_kb:.1f} KB)")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {OUT_DIR}")
    print(f"Hitting API at: {API_BASE}\n")

    # -- 1. Cities (the big one — 1,000 entries) --
    print("== cities ==")
    cities = get_json("/api/v2/cities")
    if cities is None:
        print("ERROR: /api/v2/cities failed; backend probably not running")
        return 1
    write_json("cities.json", cities)

    # -- 2. Data coverage (powers timeline data dots) --
    print("\n== data-coverage ==")
    coverage = get_json("/api/v2/data-coverage")
    if coverage is not None:
        write_json("data-coverage.json", coverage)

    # -- 3. Build a list of distinct (city_id, date) pairs to snapshot --
    # Only snapshot scores+sources for cities that actually have data on a
    # feature date, to keep the bundle small.
    snapshotted_pairs: list[tuple[str, str]] = []
    snapshotted_dates: list[str] = []

    for d in FEATURE_DATES:
        print(f"\n== cities/scores for {d} ==")
        scores = get_json(f"/api/v2/cities/scores?date={d}&window_days=30")
        if scores is None:
            print(f"  no scores for {d}")
            continue
        write_json(f"cities-scores-{d}.json", scores)
        snapshotted_dates.append(d)

        # Snapshot full LLM score + sources for each city that has a row.
        for row in scores:
            cid = row["city_id"]
            print(f"  -- city {cid[:8]}... ({d})")

            score = get_json(f"/api/v2/score/{cid}?date={d}")
            if score is not None:
                write_json(f"score-{cid}-{d}.json", score)
                snapshotted_pairs.append((cid, d))

            # Sources query needs a date range; use 90 days back.
            end = date.fromisoformat(d)
            start = end - timedelta(days=90)
            sources = get_json(
                f"/api/v2/sources/{cid}?start={start.isoformat()}&end={end.isoformat()}"
            )
            if sources is not None:
                write_json(f"sources-{cid}-{d}.json", sources)

    # -- 4. Manifest so the frontend knows what's pre-baked --
    manifest = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "feature_dates": snapshotted_dates,
        "scored_pairs": [
            {"city_id": c, "date": d} for c, d in snapshotted_pairs
        ],
        "city_count": len(cities),
    }
    print("\n== manifest ==")
    write_json("manifest.json", manifest)

    print(f"\nDone. {len(snapshotted_dates)} dates × {len(set(p[0] for p in snapshotted_pairs))} cities snapshotted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
