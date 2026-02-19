"""
Parquet Archival Writer for V2 Engine

Saves raw GDELT DataFrames into date-partitioned Parquet files:

    data/historical/YYYY/MM/<city_id>.parquet

These files form our "cold storage" source of truth.  They are written with
Snappy compression and can be read back cheaply with pyarrow.

Usage:
    from data_pipeline.etl.parquet_writer import save_city_parquet

    save_city_parquet(df, city_id="abc-123", year=2023, month=6)
"""

import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Root directory for historical data
_DEFAULT_DATA_DIR = os.getenv(
    "HISTORICAL_DATA_DIR",
    str(Path(__file__).parent.parent.parent / "data" / "historical"),
)


def _partition_path(
    city_id: str,
    year: int,
    month: int,
    base_dir: Optional[str] = None,
) -> Path:
    """Build the deterministic file path for a given city / year / month."""
    base = Path(base_dir or _DEFAULT_DATA_DIR)
    return base / f"{year:04d}" / f"{month:02d}" / f"{city_id}.parquet"


# --------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------- #

def save_city_parquet(
    df: pd.DataFrame,
    city_id: str,
    year: int,
    month: int,
    base_dir: Optional[str] = None,
    append: bool = True,
) -> Path:
    """
    Write a DataFrame of raw GDELT rows to a Parquet file.

    Args:
        df:        DataFrame (columns should match GDELT_COLUMNS).
        city_id:   UUID string identifying the city.
        year:      Partition year.
        month:     Partition month.
        base_dir:  Override for the data root directory.
        append:    If True and the file already exists, append rows.

    Returns:
        Path to the written Parquet file.
    """
    if df.empty:
        logger.debug("Empty DataFrame for %s/%d/%02d — skipping write", city_id, year, month)
        return _partition_path(city_id, year, month, base_dir)

    dest = _partition_path(city_id, year, month, base_dir)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Convert to pyarrow Table
    table = pa.Table.from_pandas(df, preserve_index=False)

    if append and dest.exists():
        existing = pq.read_table(dest)
        table = pa.concat_tables([existing, table], promote_options="default")
        logger.debug("Appended %d rows to %s (total: %d)", len(df), dest, table.num_rows)
    else:
        logger.debug("Writing %d rows to %s", len(df), dest)

    pq.write_table(table, dest, compression="snappy")
    return dest


def read_city_parquet(
    city_id: str,
    year: int,
    month: int,
    base_dir: Optional[str] = None,
) -> pd.DataFrame:
    """
    Read a single Parquet partition back into a DataFrame.
    Returns an empty DataFrame if the file does not exist.
    """
    src = _partition_path(city_id, year, month, base_dir)
    if not src.exists():
        return pd.DataFrame()
    return pq.read_table(src).to_pandas()


def list_partitions(
    city_id: Optional[str] = None,
    base_dir: Optional[str] = None,
) -> list[Path]:
    """
    List all Parquet files, optionally filtered to a single city.
    """
    base = Path(base_dir or _DEFAULT_DATA_DIR)
    if not base.exists():
        return []

    pattern = f"**/{city_id}.parquet" if city_id else "**/*.parquet"
    return sorted(base.glob(pattern))
