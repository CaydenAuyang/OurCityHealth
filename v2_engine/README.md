# V2 Engine - Geospatial Intelligence Platform

Enterprise-grade geospatial backend for Our City Health.

## Features

- **1,000+ Cities**: PostgreSQL + PostGIS database with GeoNames data
- **District Granularity**: OpenStreetMap administrative boundaries
- **Spatial Queries**: Fast ST_Contains, ST_DWithin operations with GIST indexes
- **Async Architecture**: SQLAlchemy 2.0 + asyncpg for high-performance operations

## Quick Start

### 1. Start Infrastructure

```bash
cd v2_engine
docker-compose up -d
```

This starts:
- PostgreSQL 16 + PostGIS 3.4 on port `5433`
- Redis 7 on port `6380`

### 2. Install Dependencies

```bash
pip install -r requirements_v2.txt

# If using spaCy for NER (optional):
python -m spacy download en_core_web_md
```

### 3. Configure Environment

```bash
cp env.template .env
# Edit .env if needed (defaults work for local Docker)
```

### 4. Run Data Ingestion

```bash
python scripts/v2_ingest_geo.py
```

This will:
- Load 1,000 cities from GeoNames (sorted by population)
- Fetch district boundaries for top 50 cities from OpenStreetMap
- Insert all data into PostGIS with spatial indexes

**Expected output:**
```
V2 GEOSPATIAL DATA INGESTION
============================================================
📍 Loading top 1000 cities from GeoNames...
✅ Loaded 1000 cities from GeoNames cache

💾 Inserting cities into PostGIS...
✅ Inserted 1000 cities into database

🗺️ Fetching districts for top 50 cities...
Fetching districts: 100%|████████████| 50/50 [~10min]

============================================================
INGESTION COMPLETE
  Cities loaded:     1000
  Districts loaded:  ~500-800
  Time elapsed:      ~10-15 minutes
============================================================
```

### 5. Verify Installation

```bash
# Connect to database
docker exec -it v2_postgres psql -U ochv2 -d ochv2_geo

# Check data
SELECT COUNT(*) FROM cities;
SELECT COUNT(*) FROM districts;

# Test spatial query (Hong Kong)
SELECT name, country_code FROM cities 
ORDER BY location <-> ST_SetSRID(ST_MakePoint(114.1694, 22.3193), 4326) 
LIMIT 5;
```

## Project Structure

```
v2_engine/
├── docker-compose.yml      # PostgreSQL + PostGIS + Redis
├── env.template            # Environment variables template
├── requirements_v2.txt     # Python dependencies
├── README.md               # This file
│
├── backend_v2/
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py      # Async SQLAlchemy engine
│   │   └── models.py       # City + District models
│   └── engine/
│       ├── __init__.py
│       └── geo_resolver.py # Spatial query service
│
├── scripts/
│   └── v2_ingest_geo.py    # Data ingestion script
│
└── logs/
    ├── ingest.log          # Ingestion logs
    └── osm_failures.log    # OSM query failures
```

## API Usage

### GeoResolver Service

```python
from v2_engine.backend_v2.engine import GeoResolver

# Initialize resolver
resolver = GeoResolver()

# Resolve coordinates to district
district = await resolver.resolve_district(lat=22.3193, lng=114.1694)
# Returns: DistrictResult(name="Central", city_name="Hong Kong", ...)

# Find nearest city
city = await resolver.resolve_city(lat=22.3193, lng=114.1694)
# Returns: CityResult(name="Hong Kong", distance_km=0.5, ...)

# Find cities within radius
cities = await resolver.get_cities_in_radius(lat=22.3193, lng=114.1694, radius_km=100)
# Returns: [CityResult(...), ...]

# Search by name
city = await resolver.get_city_by_name("Hong Kong")
# Returns: CityResult(name="Hong Kong", ...)

# Get districts for a city
districts = await resolver.get_districts_for_city(city_id="uuid-here")
# Returns: [DistrictResult(...), ...]
```

### Direct Database Access

```python
from v2_engine.backend_v2.db import get_db, City, District
from sqlalchemy import select

async with get_db() as session:
    # Query cities by country
    result = await session.execute(
        select(City).where(City.country_code == "HK")
    )
    cities = result.scalars().all()
```

## Database Schema

### cities

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| geonames_id | INT | GeoNames reference (unique) |
| name | VARCHAR(255) | City name |
| ascii_name | VARCHAR(255) | ASCII name for search |
| country_code | CHAR(2) | ISO country code |
| country_name | VARCHAR(100) | Full country name |
| population | INT | Population |
| timezone | VARCHAR(100) | Timezone identifier |
| location | GEOMETRY(Point, 4326) | PostGIS point |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Update timestamp |

### districts

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| city_id | UUID | Foreign key to cities |
| osm_id | BIGINT | OpenStreetMap ID |
| name | VARCHAR(255) | District name |
| admin_level | INT | OSM admin level (6-10) |
| boundary_type | VARCHAR(50) | Type of boundary |
| boundary | GEOMETRY(MultiPolygon, 4326) | PostGIS polygon |
| created_at | TIMESTAMP | Creation timestamp |

## Troubleshooting

### Docker Issues

```bash
# Check container status
docker-compose ps

# View PostgreSQL logs
docker-compose logs postgres_v2

# Restart containers
docker-compose down && docker-compose up -d
```

### Database Connection Issues

```bash
# Test connection
docker exec -it v2_postgres pg_isready -U ochv2 -d ochv2_geo

# Check PostGIS extension
docker exec -it v2_postgres psql -U ochv2 -d ochv2_geo -c "SELECT PostGIS_Version();"
```

### OSM Query Failures

Check `logs/osm_failures.log` for cities that failed to fetch districts. Common issues:
- City name ambiguity (multiple cities with same name)
- No admin boundaries at requested level
- Overpass API rate limiting

## Next Steps (Phase 2+)

- [ ] GDELT historical data ingestion
- [ ] TimescaleDB hypertables for time-series
- [ ] Pydantic V2 scoring schemas
- [ ] FastAPI V2 endpoints
- [ ] Cesium.js 3D globe frontend
