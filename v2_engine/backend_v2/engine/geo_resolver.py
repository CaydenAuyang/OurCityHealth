"""
Geo Resolver Service for V2 Engine

Provides spatial query functions using PostGIS:
- Resolve coordinates to districts (ST_Contains)
- Find cities by name (fuzzy search)
- Find cities within radius (ST_DWithin)
- Get districts for a city
"""

import uuid
from typing import Optional, List
from dataclasses import dataclass

from sqlalchemy import select, func, text, or_, type_coerce
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.types import Geography

from backend_v2.db.models import City, District
from backend_v2.db.session import get_db, async_session_factory


@dataclass
class CityResult:
    """Lightweight city result for API responses."""
    id: str
    geonames_id: int
    name: str
    country_code: str
    country_name: Optional[str]
    population: int
    latitude: float
    longitude: float
    distance_km: Optional[float] = None


@dataclass
class DistrictResult:
    """Lightweight district result for API responses."""
    id: str
    name: str
    admin_level: int
    boundary_type: Optional[str]
    city_id: str
    city_name: Optional[str] = None


class GeoResolver:
    """
    Geospatial resolver service for V2 Engine.
    
    Usage:
        resolver = GeoResolver()
        district = await resolver.resolve_district(22.3193, 114.1694)
        cities = await resolver.get_cities_in_radius(22.3193, 114.1694, 50)
    """
    
    def __init__(self, session: Optional[AsyncSession] = None):
        """
        Initialize GeoResolver.
        
        Args:
            session: Optional AsyncSession. If not provided, creates new sessions.
        """
        self._session = session
    
    async def _get_session(self) -> AsyncSession:
        """Get or create an async session."""
        if self._session:
            return self._session
        return async_session_factory()
    
    # ============================================
    # Core Spatial Queries
    # ============================================
    
    async def resolve_district(
        self,
        lat: float,
        lng: float,
    ) -> Optional[DistrictResult]:
        """
        Find the district that contains the given coordinates.
        
        Uses PostGIS ST_Contains for point-in-polygon query.
        
        Args:
            lat: Latitude (WGS84)
            lng: Longitude (WGS84)
        
        Returns:
            DistrictResult if found, None otherwise
        """
        session = await self._get_session()
        
        try:
            # Build the point geometry
            point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
            
            # Query for containing district
            result = await session.execute(
                select(District, City.name.label("city_name"))
                .join(City, District.city_id == City.id)
                .where(func.ST_Contains(District.boundary, point))
                .limit(1)
            )
            
            row = result.first()
            if row:
                district = row[0]
                city_name = row[1]
                
                return DistrictResult(
                    id=str(district.id),
                    name=district.name,
                    admin_level=district.admin_level,
                    boundary_type=district.boundary_type,
                    city_id=str(district.city_id),
                    city_name=city_name,
                )
            
            return None
        
        finally:
            if not self._session:
                await session.close()
    
    async def resolve_city(
        self,
        lat: float,
        lng: float,
        max_distance_km: float = 50.0,
    ) -> Optional[CityResult]:
        """
        Find the nearest city to the given coordinates.
        
        Args:
            lat: Latitude (WGS84)
            lng: Longitude (WGS84)
            max_distance_km: Maximum search radius in kilometers
        
        Returns:
            CityResult if found within radius, None otherwise
        """
        session = await self._get_session()
        
        try:
            # Convert km to meters for ST_DWithin
            max_distance_m = max_distance_km * 1000
            
            # Build point geometry
            point_geom = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
            
            # Query with distance calculation
            result = await session.execute(
                select(
                    City,
                    func.ST_Distance(
                        type_coerce(City.location, Geography),
                        type_coerce(point_geom, Geography)
                    ).label("distance_m")
                )
                .where(
                    func.ST_DWithin(
                        type_coerce(City.location, Geography),
                        type_coerce(point_geom, Geography),
                        max_distance_m
                    )
                )
                .order_by(text("distance_m"))
                .limit(1)
            )
            
            row = result.first()
            if row:
                city = row[0]
                distance_m = row[1]
                
                # Extract lat/lng from geometry
                coords = await self._get_city_coords(session, city.id)
                
                return CityResult(
                    id=str(city.id),
                    geonames_id=city.geonames_id,
                    name=city.name,
                    country_code=city.country_code,
                    country_name=city.country_name,
                    population=city.population,
                    latitude=coords[0] if coords else 0.0,
                    longitude=coords[1] if coords else 0.0,
                    distance_km=distance_m / 1000 if distance_m else None,
                )
            
            return None
        
        finally:
            if not self._session:
                await session.close()
    
    async def get_cities_in_radius(
        self,
        lat: float,
        lng: float,
        radius_km: float,
        limit: int = 100,
    ) -> List[CityResult]:
        """
        Find all cities within a given radius of coordinates.
        
        Uses PostGIS ST_DWithin for efficient radius search.
        
        Args:
            lat: Center latitude (WGS84)
            lng: Center longitude (WGS84)
            radius_km: Search radius in kilometers
            limit: Maximum number of results
        
        Returns:
            List of CityResult objects sorted by distance
        """
        session = await self._get_session()
        
        try:
            # Convert km to meters
            radius_m = radius_km * 1000
            
            # Create point geometry using func.ST_SetSRID
            point_geom = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
            
            # Query cities within radius
            result = await session.execute(
                select(
                    City,
                    func.ST_Distance(
                        type_coerce(City.location, Geography),
                        type_coerce(point_geom, Geography)
                    ).label("distance_m"),
                    func.ST_Y(City.location).label("lat"),
                    func.ST_X(City.location).label("lng"),
                )
                .where(
                    func.ST_DWithin(
                        type_coerce(City.location, Geography),
                        type_coerce(point_geom, Geography),
                        radius_m
                    )
                )
                .order_by(text("distance_m"))
                .limit(limit)
            )
            
            cities = []
            for row in result:
                city = row[0]
                distance_m = row[1]
                city_lat = row[2]
                city_lng = row[3]
                
                cities.append(CityResult(
                    id=str(city.id),
                    geonames_id=city.geonames_id,
                    name=city.name,
                    country_code=city.country_code,
                    country_name=city.country_name,
                    population=city.population,
                    latitude=city_lat,
                    longitude=city_lng,
                    distance_km=distance_m / 1000 if distance_m else None,
                ))
            
            return cities
        
        finally:
            if not self._session:
                await session.close()
    
    # ============================================
    # Name-Based Queries
    # ============================================
    
    async def get_city_by_name(
        self,
        name: str,
        country_code: Optional[str] = None,
        fuzzy: bool = True,
    ) -> Optional[CityResult]:
        """
        Find a city by name with optional fuzzy matching.
        
        Args:
            name: City name to search
            country_code: Optional 2-letter country code filter
            fuzzy: If True, uses ILIKE for partial matching
        
        Returns:
            CityResult if found, None otherwise
        """
        session = await self._get_session()
        
        try:
            query = select(
                City,
                func.ST_Y(City.location).label("lat"),
                func.ST_X(City.location).label("lng"),
            )
            
            if fuzzy:
                # Case-insensitive partial match
                query = query.where(
                    or_(
                        City.name.ilike(f"%{name}%"),
                        City.ascii_name.ilike(f"%{name}%"),
                    )
                )
            else:
                # Exact match (case-insensitive)
                query = query.where(func.lower(City.name) == name.lower())
            
            if country_code:
                query = query.where(City.country_code == country_code.upper())
            
            # Order by population (return most populous match)
            query = query.order_by(City.population.desc()).limit(1)
            
            result = await session.execute(query)
            row = result.first()
            
            if row:
                city = row[0]
                return CityResult(
                    id=str(city.id),
                    geonames_id=city.geonames_id,
                    name=city.name,
                    country_code=city.country_code,
                    country_name=city.country_name,
                    population=city.population,
                    latitude=row[1],
                    longitude=row[2],
                )
            
            return None
        
        finally:
            if not self._session:
                await session.close()
    
    async def search_cities(
        self,
        query: str,
        limit: int = 20,
    ) -> List[CityResult]:
        """
        Search cities by name prefix.
        
        Args:
            query: Search query (prefix match)
            limit: Maximum number of results
        
        Returns:
            List of matching CityResult objects
        """
        session = await self._get_session()
        
        try:
            result = await session.execute(
                select(
                    City,
                    func.ST_Y(City.location).label("lat"),
                    func.ST_X(City.location).label("lng"),
                )
                .where(
                    or_(
                        City.name.ilike(f"{query}%"),
                        City.ascii_name.ilike(f"{query}%"),
                    )
                )
                .order_by(City.population.desc())
                .limit(limit)
            )
            
            cities = []
            for row in result:
                city = row[0]
                cities.append(CityResult(
                    id=str(city.id),
                    geonames_id=city.geonames_id,
                    name=city.name,
                    country_code=city.country_code,
                    country_name=city.country_name,
                    population=city.population,
                    latitude=row[1],
                    longitude=row[2],
                ))
            
            return cities
        
        finally:
            if not self._session:
                await session.close()
    
    # ============================================
    # District Queries
    # ============================================
    
    async def get_districts_for_city(
        self,
        city_id: str,
    ) -> List[DistrictResult]:
        """
        Get all districts for a given city.
        
        Args:
            city_id: UUID of the city
        
        Returns:
            List of DistrictResult objects
        """
        session = await self._get_session()
        
        try:
            result = await session.execute(
                select(District, City.name.label("city_name"))
                .join(City, District.city_id == City.id)
                .where(District.city_id == uuid.UUID(city_id))
                .order_by(District.name)
            )
            
            districts = []
            for row in result:
                district = row[0]
                city_name = row[1]
                
                districts.append(DistrictResult(
                    id=str(district.id),
                    name=district.name,
                    admin_level=district.admin_level,
                    boundary_type=district.boundary_type,
                    city_id=str(district.city_id),
                    city_name=city_name,
                ))
            
            return districts
        
        finally:
            if not self._session:
                await session.close()
    
    async def get_districts_for_city_by_name(
        self,
        city_name: str,
        country_code: Optional[str] = None,
    ) -> List[DistrictResult]:
        """
        Get all districts for a city by name.
        
        Args:
            city_name: Name of the city
            country_code: Optional 2-letter country code
        
        Returns:
            List of DistrictResult objects
        """
        city = await self.get_city_by_name(city_name, country_code, fuzzy=False)
        if not city:
            return []
        
        return await self.get_districts_for_city(city.id)
    
    # ============================================
    # Utility Methods
    # ============================================
    
    async def _get_city_coords(
        self,
        session: AsyncSession,
        city_id: uuid.UUID,
    ) -> Optional[tuple[float, float]]:
        """Extract lat/lng from city geometry."""
        result = await session.execute(
            select(
                func.ST_Y(City.location).label("lat"),
                func.ST_X(City.location).label("lng"),
            )
            .where(City.id == city_id)
        )
        row = result.first()
        if row:
            return (row[0], row[1])
        return None


# ============================================
# Convenience Functions
# ============================================

async def resolve_district(lat: float, lng: float) -> Optional[DistrictResult]:
    """
    Convenience function to resolve coordinates to a district.
    
    Args:
        lat: Latitude (WGS84)
        lng: Longitude (WGS84)
    
    Returns:
        DistrictResult if found, None otherwise
    """
    resolver = GeoResolver()
    return await resolver.resolve_district(lat, lng)


async def resolve_city(lat: float, lng: float) -> Optional[CityResult]:
    """
    Convenience function to find the nearest city to coordinates.
    
    Args:
        lat: Latitude (WGS84)
        lng: Longitude (WGS84)
    
    Returns:
        CityResult if found, None otherwise
    """
    resolver = GeoResolver()
    return await resolver.resolve_city(lat, lng)


async def get_city_by_name(name: str) -> Optional[CityResult]:
    """
    Convenience function to find a city by name.
    
    Args:
        name: City name to search
    
    Returns:
        CityResult if found, None otherwise
    """
    resolver = GeoResolver()
    return await resolver.get_city_by_name(name)
