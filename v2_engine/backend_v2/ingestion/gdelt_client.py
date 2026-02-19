"""
GDELT BigQuery Client for V2 Engine

Queries the public `gdelt-bq.gdeltv2.events` table for events geolocated near
our city database.  Designed to be cost-efficient:

1. DATEADDED range filter (integer YYYYMMDDHHMMSS) — earliest possible pruning.
2. Bounding-box filter on ActionGeo_Lat / ActionGeo_Long — limits rows early.
3. Selects only the columns we need.

Usage:
    client = GDELTClient()
    df = client.query_city_events(
        lat=22.28, lng=114.17, radius_km=50,
        start_date="2020-01-01", end_date="2024-01-01",
    )
"""

import logging
import math
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Columns we pull from GDELT — keeps BQ scan costs low
GDELT_COLUMNS = [
    "SQLDATE",          # INT64 YYYYMMDD
    "SOURCEURL",
    "Actor1Name",
    "Actor2Name",
    "EventCode",        # CAMEO code
    "EventRootCode",    # First two digits of EventCode
    "GoldsteinScale",   # -10 to +10
    "NumMentions",
    "NumSources",
    "NumArticles",
    "AvgTone",          # -100 to +100
    "ActionGeo_Lat",
    "ActionGeo_Long",
    "ActionGeo_FullName",
]


def _bounding_box(lat: float, lng: float, radius_km: float) -> dict:
    """
    Return a lat/lng bounding box around a point.

    Uses a simple equirectangular approximation — accurate enough for ~50 km
    city-level filtering and much cheaper than ST_DISTANCE in BigQuery.
    """
    # 1 degree latitude ≈ 111.32 km
    lat_delta = radius_km / 111.32
    # 1 degree longitude shrinks by cos(latitude)
    lng_delta = radius_km / (111.32 * math.cos(math.radians(lat)))

    return {
        "lat_min": lat - lat_delta,
        "lat_max": lat + lat_delta,
        "lng_min": lng - lng_delta,
        "lng_max": lng + lng_delta,
    }


@dataclass
class CityCoord:
    """Lightweight struct passed to the GDELT client."""
    city_id: str
    name: str
    lat: float
    lng: float


class GDELTClient:
    """Thin wrapper around google-cloud-bigquery for GDELT event queries."""

    # The public GDELT v2 events table
    TABLE = "gdelt-bq.gdeltv2.events"

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ):
        project_id = project_id or os.getenv("GCP_PROJECT_ID", "ourcityhealth")
        cred_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if cred_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

        self.client = bigquery.Client(project=project_id)
        logger.info("BigQuery client initialised (project=%s)", project_id)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def query_city_events(
        self,
        lat: float,
        lng: float,
        start_date: str,
        end_date: str,
        radius_km: float = 50.0,
    ) -> pd.DataFrame:
        """
        Fetch GDELT events near a city for a date range.

        Args:
            lat:        City centre latitude.
            lng:        City centre longitude.
            start_date: Inclusive start date "YYYY-MM-DD".
            end_date:   Exclusive end date   "YYYY-MM-DD".
            radius_km:  Approximate bounding-box radius.

        Returns:
            DataFrame with GDELT_COLUMNS, empty if nothing found.
        """
        bbox = _bounding_box(lat, lng, radius_km)

        # DATEADDED is an INT64 column with format YYYYMMDDHHMMSS.
        # Filtering on it early is the cheapest way to limit BQ scan volume.
        # We convert YYYY-MM-DD → YYYYMMDD000000 (start of day) for the range.
        sd = start_date.replace("-", "") + "000000"
        ed = end_date.replace("-", "") + "000000"

        cols = ", ".join(GDELT_COLUMNS)

        query = f"""
            SELECT {cols}
            FROM `{self.TABLE}`
            WHERE DATEADDED >= {sd}
              AND DATEADDED <  {ed}
              AND ActionGeo_Lat  BETWEEN {bbox['lat_min']:.6f} AND {bbox['lat_max']:.6f}
              AND ActionGeo_Long BETWEEN {bbox['lng_min']:.6f} AND {bbox['lng_max']:.6f}
        """

        logger.debug("BigQuery for (%.4f, %.4f) %s→%s", lat, lng, start_date, end_date)

        job_config = bigquery.QueryJobConfig(
            use_legacy_sql=False,
            # Enable cache to avoid re-scanning identical ranges
            use_query_cache=True,
        )

        try:
            df = self.client.query(query, job_config=job_config).to_dataframe()
            logger.info(
                "BQ returned %d rows for (%.2f, %.2f) [%s – %s]",
                len(df), lat, lng, start_date, end_date,
            )
            return df
        except Exception:
            logger.exception("BigQuery query failed for (%.2f, %.2f)", lat, lng)
            return pd.DataFrame(columns=GDELT_COLUMNS)

    def query_city_events_chunked(
        self,
        lat: float,
        lng: float,
        start_date: str,
        end_date: str,
        chunk_months: int = 3,
        radius_km: float = 50.0,
    ) -> pd.DataFrame:
        """
        Same as `query_city_events` but breaks the range into smaller chunks
        to keep per-query costs predictable and avoid BQ timeouts.
        """
        chunks: list[pd.DataFrame] = []
        current = datetime.strptime(start_date, "%Y-%m-%d").date()
        final = datetime.strptime(end_date, "%Y-%m-%d").date()

        while current < final:
            next_month = current.month + chunk_months
            next_year = current.year + (next_month - 1) // 12
            next_month = ((next_month - 1) % 12) + 1
            chunk_end = date(next_year, next_month, 1)
            if chunk_end > final:
                chunk_end = final

            df = self.query_city_events(
                lat=lat, lng=lng,
                start_date=current.isoformat(),
                end_date=chunk_end.isoformat(),
                radius_km=radius_km,
            )
            if not df.empty:
                chunks.append(df)

            current = chunk_end

        if not chunks:
            return pd.DataFrame(columns=GDELT_COLUMNS)
        return pd.concat(chunks, ignore_index=True)

    # ------------------------------------------------------------------ #
    # Cost estimator (dry-run)
    # ------------------------------------------------------------------ #

    def estimate_bytes(
        self,
        lat: float,
        lng: float,
        start_date: str,
        end_date: str,
        radius_km: float = 50.0,
    ) -> int:
        """
        Dry-run the query and return estimated bytes processed.
        Useful to sanity-check costs before a large ingestion run.
        First 1 TB / month is free on BQ.
        """
        bbox = _bounding_box(lat, lng, radius_km)
        sd = start_date.replace("-", "") + "000000"
        ed = end_date.replace("-", "") + "000000"
        cols = ", ".join(GDELT_COLUMNS)

        query = f"""
            SELECT {cols}
            FROM `{self.TABLE}`
            WHERE DATEADDED >= {sd}
              AND DATEADDED <  {ed}
              AND ActionGeo_Lat  BETWEEN {bbox['lat_min']:.6f} AND {bbox['lat_max']:.6f}
              AND ActionGeo_Long BETWEEN {bbox['lng_min']:.6f} AND {bbox['lng_max']:.6f}
        """

        job_config = bigquery.QueryJobConfig(dry_run=True, use_legacy_sql=False)
        job = self.client.query(query, job_config=job_config)
        return job.total_bytes_processed
