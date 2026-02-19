"""
GDELT GKG (Global Knowledge Graph) BigQuery Client

Queries the public `gdelt-bq.gdeltv2.gkg_partitioned` table for article-level
data near our city database.  Each row is a news article with URL, themes,
entities, tone, and mentioned locations.

The GKG location filter uses a coarse LIKE on V2Locations (lat/lng rounded to
1 decimal place) inside BigQuery, followed by precise distance filtering in
Python after retrieval.

Usage:
    client = GKGClient()
    df = client.query_city_articles(
        lat=31.23, lng=121.47,
        start_date="2024-01-01", end_date="2024-02-01",
    )
"""

from __future__ import annotations

import logging
import math
import os
from typing import Optional

import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GKG_TABLE = "gdelt-bq.gdeltv2.gkg_partitioned"

GKG_COLUMNS = [
    "DocumentIdentifier",
    "DATE",
    "SourceCommonName",
    "V2Themes",
    "V2Persons",
    "V2Organizations",
    "V2Tone",
    "V2Locations",
]


# ------------------------------------------------------------------ #
# V2-field parsers
# ------------------------------------------------------------------ #

def parse_v2_tone(tone_str: str) -> dict:
    """
    Split the comma-separated V2Tone field into named components.

    Format: overall,positive,negative,polarity,activity,self_group,word_count
    """
    defaults = {
        "overall": 0.0, "positive": 0.0, "negative": 0.0,
        "polarity": 0.0, "activity": 0.0, "self_group": 0.0,
        "word_count": 0,
    }
    if not tone_str or not isinstance(tone_str, str):
        return defaults
    parts = tone_str.split(",")
    keys = ["overall", "positive", "negative", "polarity", "activity",
            "self_group", "word_count"]
    result = dict(defaults)
    for i, key in enumerate(keys):
        if i < len(parts):
            try:
                result[key] = int(float(parts[i])) if key == "word_count" else float(parts[i])
            except (ValueError, TypeError):
                pass
    return result


def parse_v2_themes(themes_str: str) -> list:
    """Split semicolon-separated theme codes, stripping offsets."""
    if not themes_str or not isinstance(themes_str, str):
        return []
    result = []
    for entry in themes_str.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        # Each entry may have a comma-delimited offset suffix (e.g. "THEME,123")
        code = entry.split(",")[0].strip()
        if code:
            result.append(code)
    return result


def parse_v2_persons(persons_str: str) -> list:
    """Split semicolon-separated person names, stripping offsets."""
    if not persons_str or not isinstance(persons_str, str):
        return []
    result = []
    for entry in persons_str.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        name = entry.split(",")[0].strip()
        if name:
            result.append(name)
    return result


def parse_v2_organizations(orgs_str: str) -> list:
    """Split semicolon-separated organization names, stripping offsets."""
    if not orgs_str or not isinstance(orgs_str, str):
        return []
    result = []
    for entry in orgs_str.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        name = entry.split(",")[0].strip()
        if name:
            result.append(name)
    return result


def parse_v2_locations(locations_str: str) -> list:
    """
    Parse V2Locations into a list of dicts.

    GKG V2Locations format (semicolon-separated entries, each #-delimited):
        type#fullname#countrycode#adm1code#featureid#lat#lng#secondaryid#charoffset

    Field indices (0-based):
        0 = location type
        1 = full name
        2 = country code
        3 = adm1 code
        4 = feature ID  ← NOT lat
        5 = latitude
        6 = longitude
        7 = secondary ID
        8 = character offset

    Example:
        4#Shanghai, Shanghai, China#CH#CH23#13243#31.2222#121.458#-1924465#2122
    """
    if not locations_str or not isinstance(locations_str, str):
        return []
    result = []
    for entry in locations_str.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("#")
        # Need at least 7 fields: type, name, country, adm1, featureid, lat, lng
        if len(parts) < 7:
            continue
        try:
            lat_str = parts[5].strip()
            lng_str = parts[6].strip()
            if not lat_str or not lng_str:
                continue
            result.append({
                "name": parts[1].strip(),
                "country_code": parts[2].strip(),
                "lat": float(lat_str),
                "lng": float(lng_str),
            })
        except (ValueError, IndexError):
            continue
    return result


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ------------------------------------------------------------------ #
# GKGClient
# ------------------------------------------------------------------ #

class GKGClient:
    """Thin wrapper around google-cloud-bigquery for GKG article queries."""

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
        logger.info("GKG BigQuery client initialised (project=%s)", project_id)

    def query_city_articles(
        self,
        lat: float,
        lng: float,
        start_date: str,
        end_date: str,
        radius_km: float = 50.0,
        limit: int = 2000,
    ) -> pd.DataFrame:
        """
        Fetch GKG articles mentioning locations near a city.

        Uses two coarse OR-ed LIKE patterns on V2Locations in BigQuery
        (lat/lng rounded to 1dp, searching for the #lat# pattern used in
        V2Locations entries), then does precise haversine distance filtering
        in Python after retrieval.

        V2Locations entries look like:
            1#Shanghai, Shanghai, China#CH#CH23#31.2222#121.4581#-1234567
        so we match '#31.2#' (1dp lat) OR '#121.4#' (1dp lng) as a coarse gate.
        """
        # Round to 1 decimal place for the coarse BigQuery pre-filter.
        # Use the #lat# pattern that matches actual V2Locations structure.
        lat_1dp = f"{lat:.1f}"
        lng_1dp = f"{lng:.1f}"

        # Also try with one extra decimal for cases where rounding differs
        lat_floor = f"{math.floor(lat * 10) / 10:.1f}"
        lng_floor = f"{math.floor(lng * 10) / 10:.1f}"

        sd = start_date.replace("-", "") + "000000"
        ed = end_date.replace("-", "") + "000000"

        cols = ", ".join(GKG_COLUMNS)
        # Use OR patterns: match either the lat or the lng in the #-delimited field.
        # This is a broad pre-filter — the precise distance check happens in Python.
        query = f"""
            SELECT {cols}
            FROM `{GKG_TABLE}`
            WHERE DATE >= {sd}
              AND DATE < {ed}
              AND (
                V2Locations LIKE '%#{lat_1dp}#%'
                OR V2Locations LIKE '%#{lat_floor}#%'
                OR V2Locations LIKE '%#{lng_1dp}#%'
                OR V2Locations LIKE '%#{lng_floor}#%'
              )
            ORDER BY DATE DESC
            LIMIT {limit}
        """

        logger.debug(
            "GKG query for (%.4f, %.4f) %s->%s (lat_1dp=%s, lng_1dp=%s)",
            lat, lng, start_date, end_date, lat_1dp, lng_1dp,
        )

        job_config = bigquery.QueryJobConfig(
            use_legacy_sql=False,
            use_query_cache=True,
        )

        try:
            df = self.client.query(query, job_config=job_config).to_dataframe()
            logger.info(
                "GKG returned %d raw rows for (%.2f, %.2f) [%s - %s]",
                len(df), lat, lng, start_date, end_date,
            )
        except Exception:
            logger.exception("GKG BigQuery query failed for (%.2f, %.2f)", lat, lng)
            return pd.DataFrame(columns=GKG_COLUMNS)

        if df.empty:
            return df

        # Debug: log first few parsed location results to verify parsing
        if len(df) > 0:
            for i, row in df.head(3).iterrows():
                raw_loc = row.get("V2Locations", "")
                parsed = parse_v2_locations(str(raw_loc)) if raw_loc else []
                logger.debug(
                    "GKG DEBUG row %d: raw_loc (first 200) = %s",
                    i, str(raw_loc)[:200],
                )
                logger.debug("GKG DEBUG row %d: parsed = %s", i, parsed)

        # Precise distance filtering: keep only articles where ANY mentioned
        # location is within radius_km of the city center.
        keep_mask = []
        for _, row in df.iterrows():
            raw_loc = row.get("V2Locations", "")
            locs = parse_v2_locations(str(raw_loc)) if raw_loc else []
            within = any(
                _haversine_km(lat, lng, loc["lat"], loc["lng"]) <= radius_km
                for loc in locs
            )
            keep_mask.append(within)

        df = df[keep_mask].reset_index(drop=True)
        logger.info(
            "GKG after distance filter: %d / %d articles within %d km",
            len(df), len(keep_mask), radius_km,
        )
        return df
