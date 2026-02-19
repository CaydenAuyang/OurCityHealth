#!/usr/bin/env python3
"""
V2 Geospatial Data Ingestion Script

Loads 1,000+ cities from GeoNames and district boundaries from OpenStreetMap
into the PostGIS database.

Usage:
    python scripts/v2_ingest_geo.py

Requirements:
    - Docker containers running (docker-compose up -d)
    - pip install -r requirements_v2.txt
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import geonamescache
from shapely.geometry import shape, MultiPolygon, Polygon
from shapely import wkt
from sqlalchemy import text
from tqdm import tqdm

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "ingest.log"),
    ],
)
logger = logging.getLogger(__name__)

# OSM failure log
osm_failure_log = LOG_DIR / "osm_failures.log"


# ============================================
# Configuration
# ============================================

# Number of top cities to load
NUM_CITIES = 1000

# Minimum population threshold
MIN_POPULATION = 100_000

# Number of top cities to fetch districts for
NUM_CITIES_WITH_DISTRICTS = 50

# OSM admin levels to try (fallback order)
ADMIN_LEVELS = [8, 9, 10, 7, 6]

# Rate limiting for OSM queries (seconds between requests)
OSM_RATE_LIMIT = 1.5

# Batch size for database inserts
BATCH_SIZE = 100


# ============================================
# Step A: Load Cities from GeoNames
# ============================================

def get_top_cities(limit: int = NUM_CITIES, min_population: int = MIN_POPULATION) -> list[dict]:
    """
    Get top cities from geonamescache sorted by population.
    
    Returns:
        List of city dictionaries with: geonameid, name, latitude, longitude,
        countrycode, population, timezone
    """
    gc = geonamescache.GeonamesCache()
    cities = gc.get_cities()
    countries = gc.get_countries()
    
    # Filter and sort by population
    city_list = []
    for geonames_id, city in cities.items():
        if city.get("population", 0) >= min_population:
            country_code = city.get("countrycode", "")
            country_info = countries.get(country_code, {})
            
            city_list.append({
                "geonames_id": int(geonames_id),
                "name": city.get("name", ""),
                "ascii_name": city.get("asciiname", city.get("name", "")),
                "latitude": city.get("latitude", 0.0),
                "longitude": city.get("longitude", 0.0),
                "country_code": country_code,
                "country_name": country_info.get("name", ""),
                "population": city.get("population", 0),
                "timezone": city.get("timezone", ""),
            })
    
    # Sort by population descending
    city_list.sort(key=lambda x: x["population"], reverse=True)
    
    return city_list[:limit]


# ============================================
# Step B: Fetch District Boundaries from OSM
# ============================================

def fetch_districts_for_city(
    city_name: str,
    country_code: str,
    admin_levels: list[int] = ADMIN_LEVELS,
) -> list[dict]:
    """
    Fetch district boundaries from OpenStreetMap using osmnx.
    
    Uses fallback logic: tries admin_level 8, then 9, then 10, etc.
    
    Args:
        city_name: Name of the city
        country_code: ISO country code
        admin_levels: List of admin levels to try in order
    
    Returns:
        List of district dictionaries with: osm_id, name, admin_level, geometry
    """
    try:
        import osmnx as ox
        ox.settings.log_console = False
        ox.settings.use_cache = True
    except ImportError:
        logger.error("osmnx not installed. Run: pip install osmnx")
        return []
    
    districts = []
    
    for admin_level in admin_levels:
        try:
            logger.debug(f"Trying admin_level {admin_level} for {city_name}")
            
            # Query OSM for administrative boundaries within the city
            tags = {
                "admin_level": str(admin_level),
                "boundary": "administrative",
            }
            
            # First, get the city boundary
            try:
                gdf = ox.features_from_place(
                    f"{city_name}, {country_code}",
                    tags=tags,
                )
            except Exception:
                # Try without country code
                gdf = ox.features_from_place(
                    city_name,
                    tags=tags,
                )
            
            if gdf is None or len(gdf) == 0:
                continue
            
            # Extract districts from GeoDataFrame
            for idx, row in gdf.iterrows():
                # Get OSM ID (can be in different formats)
                osm_id = None
                if isinstance(idx, tuple):
                    osm_id = idx[1] if len(idx) > 1 else None
                elif hasattr(idx, "__int__"):
                    osm_id = int(idx)
                
                # Get name
                name = row.get("name", "")
                if not name or name == city_name:
                    name = row.get("name:en", row.get("alt_name", f"District_{idx}"))
                
                # Get geometry
                geom = row.geometry
                if geom is None:
                    continue
                
                # Ensure it's a Polygon or MultiPolygon
                if geom.geom_type == "Polygon":
                    geom = MultiPolygon([geom])
                elif geom.geom_type == "MultiPolygon":
                    pass
                else:
                    # Skip non-polygon geometries (points, lines)
                    continue
                
                # Validate geometry
                if not geom.is_valid:
                    geom = geom.buffer(0)  # Fix invalid geometries
                
                districts.append({
                    "osm_id": osm_id,
                    "name": str(name)[:255],
                    "admin_level": admin_level,
                    "boundary_type": row.get("boundary", "administrative"),
                    "geometry_wkt": geom.wkt,
                })
            
            if len(districts) > 0:
                logger.info(
                    f"Found {len(districts)} districts for {city_name} "
                    f"at admin_level {admin_level}"
                )
                return districts
        
        except Exception as e:
            logger.debug(f"admin_level {admin_level} failed for {city_name}: {e}")
            continue
    
    return districts


# ============================================
# Step C: Insert Data into PostGIS
# ============================================

async def insert_cities(cities: list[dict]) -> dict[int, str]:
    """
    Insert cities into PostGIS database.
    
    Args:
        cities: List of city dictionaries from get_top_cities()
    
    Returns:
        Mapping of geonames_id to UUID for foreign key references
    """
    from backend_v2.db.session import async_session_factory, init_db, engine
    from backend_v2.db.models import City
    from sqlalchemy import text
    
    # Check if tables exist first
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'cities'
            )
        """))
        tables_exist = result.scalar()
    
    # Only initialize if tables don't exist
    if not tables_exist:
        try:
            await init_db()
        except Exception as e:
            # If init_db fails, check if tables were created anyway
            async with engine.connect() as conn:
                result = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'cities'
                    )
                """))
                if not result.scalar():
                    logger.error(f"Failed to create tables: {e}")
                    raise
                else:
                    logger.warning(f"init_db had errors but tables exist, continuing...")
    
    geonames_to_uuid = {}
    
    async with async_session_factory() as session:
        for i in range(0, len(cities), BATCH_SIZE):
            batch = cities[i:i + BATCH_SIZE]
            
            for city_data in batch:
                # Create WKT point
                lng = city_data["longitude"]
                lat = city_data["latitude"]
                point_wkt = f"SRID=4326;POINT({lng} {lat})"
                
                # Check if city already exists
                result = await session.execute(
                    text("SELECT id FROM cities WHERE geonames_id = :gid"),
                    {"gid": city_data["geonames_id"]},
                )
                existing = result.fetchone()
                
                if existing:
                    geonames_to_uuid[city_data["geonames_id"]] = str(existing[0])
                    continue
                
                # Insert new city
                result = await session.execute(
                    text("""
                        INSERT INTO cities (
                            id, geonames_id, name, ascii_name, country_code,
                            country_name, population, timezone, location, created_at, updated_at
                        ) VALUES (
                            gen_random_uuid(), :geonames_id, :name, :ascii_name, :country_code,
                            :country_name, :population, :timezone, ST_GeomFromEWKT(:location),
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        RETURNING id
                    """),
                    {
                        "geonames_id": city_data["geonames_id"],
                        "name": city_data["name"],
                        "ascii_name": city_data["ascii_name"],
                        "country_code": city_data["country_code"],
                        "country_name": city_data["country_name"],
                        "population": city_data["population"],
                        "timezone": city_data["timezone"],
                        "location": point_wkt,
                    },
                )
                row = result.fetchone()
                if row:
                    geonames_to_uuid[city_data["geonames_id"]] = str(row[0])
            
            await session.commit()
            logger.info(f"Inserted cities batch {i // BATCH_SIZE + 1}")
    
    return geonames_to_uuid


async def insert_districts(
    city_uuid: str,
    city_name: str,
    districts: list[dict],
) -> int:
    """
    Insert districts for a city into PostGIS database.
    
    Args:
        city_uuid: UUID of the parent city
        city_name: Name of the city (for logging)
        districts: List of district dictionaries from fetch_districts_for_city()
    
    Returns:
        Number of districts inserted
    """
    from backend_v2.db.session import async_session_factory
    
    if not districts:
        return 0
    
    inserted = 0
    
    async with async_session_factory() as session:
        for district in districts:
            try:
                # Convert WKT to PostGIS format
                geom_ewkt = f"SRID=4326;{district['geometry_wkt']}"
                
                # Check if district already exists
                result = await session.execute(
                    text("""
                        SELECT id FROM districts 
                        WHERE city_id = :city_id AND name = :name
                    """),
                    {"city_id": city_uuid, "name": district["name"]},
                )
                if result.fetchone():
                    continue
                
                # Insert district
                await session.execute(
                    text("""
                        INSERT INTO districts (
                            id, city_id, osm_id, name, admin_level,
                            boundary_type, boundary, created_at
                        ) VALUES (
                            gen_random_uuid(), :city_id, :osm_id, :name, :admin_level,
                            :boundary_type, ST_GeomFromEWKT(:boundary), CURRENT_TIMESTAMP
                        )
                    """),
                    {
                        "city_id": city_uuid,
                        "osm_id": district.get("osm_id"),
                        "name": district["name"],
                        "admin_level": district["admin_level"],
                        "boundary_type": district.get("boundary_type"),
                        "boundary": geom_ewkt,
                    },
                )
                inserted += 1
            
            except Exception as e:
                logger.warning(f"Failed to insert district {district['name']}: {e}")
                continue
        
        await session.commit()
    
    return inserted


# ============================================
# Main Ingestion Pipeline
# ============================================

async def run_ingestion():
    """
    Main ingestion pipeline:
    1. Load cities from GeoNames
    2. Insert cities into PostGIS
    3. Fetch and insert districts for top cities
    """
    start_time = time.time()
    
    print("\n" + "=" * 60)
    print("V2 GEOSPATIAL DATA INGESTION")
    print("=" * 60 + "\n")
    
    # ----------------------------------------
    # Step A: Load cities from GeoNames
    # ----------------------------------------
    logger.info(f"📍 Loading top {NUM_CITIES} cities from GeoNames...")
    cities = get_top_cities(limit=NUM_CITIES, min_population=MIN_POPULATION)
    logger.info(f"✅ Loaded {len(cities)} cities from GeoNames cache")
    
    # Show top 10 cities
    logger.info("Top 10 cities by population:")
    for i, city in enumerate(cities[:10], 1):
        logger.info(f"  {i}. {city['name']}, {city['country_code']} ({city['population']:,})")
    
    # ----------------------------------------
    # Step B: Insert cities into PostGIS
    # ----------------------------------------
    logger.info("\n💾 Inserting cities into PostGIS...")
    geonames_to_uuid = await insert_cities(cities)
    logger.info(f"✅ Inserted {len(geonames_to_uuid)} cities into database")
    
    # ----------------------------------------
    # Step C: Fetch and insert districts
    # ----------------------------------------
    logger.info(f"\n🗺️ Fetching districts for top {NUM_CITIES_WITH_DISTRICTS} cities...")
    
    top_cities_for_districts = cities[:NUM_CITIES_WITH_DISTRICTS]
    osm_failures = []
    total_districts = 0
    
    for city in tqdm(top_cities_for_districts, desc="Fetching districts"):
        city_uuid = geonames_to_uuid.get(city["geonames_id"])
        if not city_uuid:
            continue
        
        try:
            # Rate limiting
            time.sleep(OSM_RATE_LIMIT)
            
            # Fetch districts from OSM
            districts = fetch_districts_for_city(
                city_name=city["name"],
                country_code=city["country_code"],
            )
            
            if districts:
                # Insert into database
                count = await insert_districts(
                    city_uuid=city_uuid,
                    city_name=city["name"],
                    districts=districts,
                )
                total_districts += count
                logger.info(f"  ✅ {city['name']}: {count} districts")
            else:
                logger.warning(f"  ⚠️ {city['name']}: No districts found")
                osm_failures.append({
                    "city": city["name"],
                    "country": city["country_code"],
                    "reason": "No districts found at any admin level",
                })
        
        except Exception as e:
            logger.error(f"  ❌ {city['name']}: {str(e)}")
            osm_failures.append({
                "city": city["name"],
                "country": city["country_code"],
                "reason": str(e),
            })
    
    # Log OSM failures
    if osm_failures:
        with open(osm_failure_log, "w") as f:
            f.write(f"OSM Ingestion Failures - {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            for failure in osm_failures:
                f.write(f"City: {failure['city']}, {failure['country']}\n")
                f.write(f"Reason: {failure['reason']}\n\n")
        logger.info(f"📝 OSM failures logged to: {osm_failure_log}")
    
    # ----------------------------------------
    # Summary
    # ----------------------------------------
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"  Cities loaded:     {len(cities)}")
    print(f"  Cities in DB:      {len(geonames_to_uuid)}")
    print(f"  Districts loaded:  {total_districts}")
    print(f"  OSM failures:      {len(osm_failures)}")
    print(f"  Time elapsed:      {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print("=" * 60 + "\n")
    
    # Verification queries
    logger.info("Running verification queries...")
    await verify_data()


async def verify_data():
    """Run verification queries to confirm data integrity."""
    from backend_v2.db.session import async_session_factory
    
    async with async_session_factory() as session:
        # Count cities
        result = await session.execute(text("SELECT COUNT(*) FROM cities"))
        city_count = result.scalar()
        
        # Count districts
        result = await session.execute(text("SELECT COUNT(*) FROM districts"))
        district_count = result.scalar()
        
        # Count cities with districts
        result = await session.execute(text("""
            SELECT COUNT(DISTINCT city_id) FROM districts
        """))
        cities_with_districts = result.scalar()
        
        # Sample spatial query (Hong Kong coordinates)
        result = await session.execute(text("""
            SELECT name, country_code, 
                   ST_Distance(location::geography, ST_GeogFromText('POINT(114.1694 22.3193)')) as distance_m
            FROM cities
            ORDER BY location <-> ST_SetSRID(ST_MakePoint(114.1694, 22.3193), 4326)
            LIMIT 5
        """))
        nearby = result.fetchall()
        
        print("\n📊 VERIFICATION RESULTS:")
        print(f"  Total cities:           {city_count}")
        print(f"  Total districts:        {district_count}")
        print(f"  Cities with districts:  {cities_with_districts}")
        print(f"\n  Nearest cities to Hong Kong (22.32°N, 114.17°E):")
        for row in nearby:
            print(f"    - {row[0]}, {row[1]} ({row[2]/1000:.1f} km)")


if __name__ == "__main__":
    asyncio.run(run_ingestion())
