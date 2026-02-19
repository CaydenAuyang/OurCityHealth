"""
GeoAlchemy2 Models for V2 Engine

Defines City and District entities with PostGIS spatial columns.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry


class Base(DeclarativeBase):
    """Base class for all V2 models."""
    pass


class City(Base):
    """
    City entity with geospatial point location.
    
    Stores 1,000+ cities from GeoNames with their coordinates.
    """
    __tablename__ = "cities"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # GeoNames reference
    geonames_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        index=True,
    )
    
    # City attributes
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    
    # ASCII name for search (no diacritics)
    ascii_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        index=True,
    )
    
    country_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    population: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    
    timezone: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # PostGIS Point geometry (SRID 4326 = WGS84)
    location: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    districts: Mapped[List["District"]] = relationship(
        "District",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    
    # Spatial index for fast geospatial queries
    __table_args__ = (
        Index("idx_cities_location", location, postgresql_using="gist"),
        Index("idx_cities_name_lower", text("lower(name)")),
    )
    
    def __repr__(self) -> str:
        return f"<City(id={self.id}, name='{self.name}', country='{self.country_code}')>"


class District(Base):
    """
    District/Neighborhood entity with polygon boundary.
    
    Stores administrative boundaries from OpenStreetMap.
    """
    __tablename__ = "districts"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Foreign key to city
    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # OpenStreetMap reference
    osm_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )
    
    # District attributes
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # OSM admin_level (6-10 typically for districts)
    admin_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=8,
    )
    
    # Type of boundary (e.g., "neighbourhood", "suburb", "district")
    boundary_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # PostGIS Polygon/MultiPolygon geometry (SRID 4326 = WGS84)
    boundary: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326),
        nullable=False,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    
    # Relationships
    city: Mapped["City"] = relationship(
        "City",
        back_populates="districts",
    )
    
    # Spatial index for fast ST_Contains queries
    __table_args__ = (
        Index("idx_districts_boundary", boundary, postgresql_using="gist"),
        Index("idx_districts_city_name", city_id, name),
    )
    
    def __repr__(self) -> str:
        return f"<District(id={self.id}, name='{self.name}', city_id={self.city_id})>"
