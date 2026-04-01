"""
Stub module for city and source discovery functions.
These functions are used when --cities_link is provided, otherwise the script falls back to static sources.
"""

from typing import List, Tuple, Dict, Optional

def load_top_cities_from_table(url: str, max_cities: int = 100) -> List[Tuple[str, Optional[str]]]:
    """
    Load top cities from a Wikipedia table or similar source.
    Returns list of (city_name, country) tuples.
    """
    # This is a stub - actual implementation would parse the URL
    # For now, return empty list to trigger fallback to static sources
    return []

def build_city_subreddits(cities: List[Tuple[str, Optional[str]]]) -> Dict[str, str]:
    """
    Discover subreddits for given cities.
    Returns dict mapping city_name -> subreddit_name.
    """
    # Stub implementation
    return {}

def build_city_sources_map(cities: List[Tuple[str, Optional[str]]], per_city_min: int = 30) -> Dict[str, List[str]]:
    """
    Discover per-city news sources.
    Returns dict mapping city_name -> list of source URLs.
    """
    # Stub implementation
    return {}

def build_global_sources(city_sources_map: Dict[str, List[str]], global_min: int = 150) -> List[str]:
    """
    Build global news source pool from city sources.
    Returns list of unique source URLs.
    """
    # Stub implementation
    return []

