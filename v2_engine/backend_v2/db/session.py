"""
Async SQLAlchemy Session Configuration for V2 Engine

Uses asyncpg driver for high-performance PostgreSQL + PostGIS operations.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment.
# Railway Postgres provides "postgresql://…" — convert to asyncpg driver scheme.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://ochv2:ochv2_secure_password@localhost:5433/ochv2_geo",
)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session factory - expire_on_commit=False allows detached object access
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    
    Usage:
        async with get_db() as session:
            result = await session.execute(query)
    """
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for FastAPI routes.
    
    Usage:
        @app.get("/cities")
        async def get_cities(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with get_db() as session:
        yield session


async def init_db() -> None:
    """
    Initialize database: create tables and enable PostGIS extension.
    
    Call this once at application startup or during initial setup.
    """
    from .models import Base
    
    # Use connect() instead of begin() to have more control over transactions
    async with engine.connect() as conn:
        # Enable PostGIS extension (idempotent) - commit immediately
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        await conn.commit()
        
        # Check if tables already exist
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'cities'
            )
        """))
        tables_exist = result.scalar()
        
        if not tables_exist:
            # Create tables manually with raw SQL to avoid index creation issues
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cities (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    geonames_id INTEGER UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    ascii_name VARCHAR(255),
                    country_code CHAR(2) NOT NULL,
                    country_name VARCHAR(100),
                    population INTEGER NOT NULL DEFAULT 0,
                    timezone VARCHAR(100),
                    location GEOMETRY(Point, 4326) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS districts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
                    osm_id BIGINT,
                    name VARCHAR(255) NOT NULL,
                    admin_level INTEGER NOT NULL DEFAULT 8,
                    boundary_type VARCHAR(50),
                    boundary GEOMETRY(MultiPolygon, 4326) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create indexes with IF NOT EXISTS (PostgreSQL 9.5+)
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cities_geonames_id ON cities(geonames_id);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cities_name ON cities(name);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cities_country_code ON cities(country_code);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cities_location ON cities USING gist(location);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cities_name_lower ON cities(lower(name));"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_districts_city_id ON districts(city_id);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_districts_osm_id ON districts(osm_id);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_districts_boundary ON districts USING gist(boundary);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_districts_city_name ON districts(city_id, name);"))
            
            await conn.commit()
            print("✅ Database tables created")
        else:
            print("✅ Database tables already exist, skipping creation")

        # V2.1: city_events table (idempotent — always attempt creation)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS city_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
                event_date DATE NOT NULL,
                actor1 VARCHAR(255),
                actor2 VARCHAR(255),
                event_code VARCHAR(10),
                goldstein_scale DOUBLE PRECISION,
                num_mentions INTEGER,
                source_url TEXT,
                action_geo_lat DOUBLE PRECISION,
                action_geo_long DOUBLE PRECISION,
                CONSTRAINT uq_city_events_city_date_url
                    UNIQUE (city_id, event_date, source_url)
            );
        """))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_city_events_city_date "
            "ON city_events (city_id, event_date);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_city_events_city_goldstein "
            "ON city_events (city_id, goldstein_scale);"
        ))
        await conn.commit()

        # V2.2: city_articles table (idempotent)
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

        # V2 Prompt 8: city_scores table (pre-computed LLM scores)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS city_scores (
                id SERIAL PRIMARY KEY,
                city_id VARCHAR NOT NULL,
                city_name VARCHAR NOT NULL,
                scored_date DATE NOT NULL,
                overall_score DOUBLE PRECISION NOT NULL,
                overall_confidence DOUBLE PRECISION,
                score_json TEXT NOT NULL,
                model_used VARCHAR DEFAULT 'gpt-4o',
                computed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_city_score_date UNIQUE (city_id, scored_date)
            );
        """))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_city_scores_lookup "
            "ON city_scores (city_id, scored_date);"
        ))
        await conn.commit()
    
    print("✅ Database initialized with PostGIS extension")


async def drop_all_tables() -> None:
    """
    Drop all tables. USE WITH CAUTION - for development/testing only.
    """
    from .models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("⚠️ All tables dropped")


async def health_check() -> bool:
    """
    Check database connectivity.
    
    Returns:
        True if database is reachable, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
