#!/usr/bin/env python3
"""
Initialize Railway database with schema and optionally seed data.

Usage:
    railway run python3 scripts/init_railway_db.py
    railway run python3 scripts/init_railway_db.py --seed
"""

import asyncio
import os
import sys

# Ensure the parent v2_engine directory is on the path so backend_v2 is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main() -> None:
    from backend_v2.db.session import init_db

    print("Initializing database schema...")
    await init_db()
    print("✅ Database schema ready")

    if "--seed" in sys.argv:
        print("Seeding with historical data (requires GCP credentials)...")
        os.system(
            "python3 scripts/ingest_history.py"
            " --start 2024-01-01 --end 2024-02-01 --limit 1"
        )
        print("✅ Seed data ingested")


if __name__ == "__main__":
    asyncio.run(main())
