# =====================================================================
# OUR CITY HEALTH - CIVIC HEALTH DASHBOARD PIPELINE
# =====================================================================
# This script scrapes international news and social media to analyze
# civic health across global cities using AI-powered analysis
# =====================================================================

# Import all the libraries we need for this program
import os                           # For reading environment variables (like API keys)
import time                         # For adding delays between web requests (to be polite)
import json                         # For working with JSON data from APIs
import random                       # For randomly sampling data when we have too much
import requests                     # For making HTTP requests to websites
from bs4 import BeautifulSoup      # For parsing HTML content from websites
import spacy                        # For natural language processing (understanding text)
import numpy as np                  # For mathematical operations on arrays
from collections import Counter, defaultdict  # For counting things and organizing data
from dataclasses import dataclass  # For creating simple data structures
from typing import List, Dict, Any, Optional, Tuple, Set  # For type hints (helps with code clarity)
from contextlib import contextmanager  # For creating context managers
import signal                       # For handling system signals
from urllib.parse import urljoin, urlparse  # For working with URLs
from datetime import datetime, timezone     # For handling dates and times
from concurrent.futures import ThreadPoolExecutor, as_completed  # For safe parallel requests
import sqlite3                     # For caching visited URLs across runs (resume)
import threading                  # For thread-safe SQLite access
import xml.etree.ElementTree as ET # For lightweight XML parsing (RSS/Sitemaps)

try:
    # Optional dependency for robust RSS parsing; we will gracefully fallback if missing
    import feedparser              # For parsing RSS/Atom feeds reliably
except Exception:                  # If not installed, we'll use a simple XML fallback
    feedparser = None

try:
    # Retry utilities for robust HTTP sessions
    from urllib3.util.retry import Retry
except Exception:
    Retry = None

from sklearn.cluster import AgglomerativeClustering  # For grouping similar keywords together
import argparse                   # For command-line flags to control scale and inputs

# Import dynamic discovery helpers to scale to 100 cities
from cities_and_sources import (
    load_top_cities_from_table,   # Load top-N cities from a provided table URL
    build_city_subreddits,        # Discover subreddits for those cities
    build_city_sources_map,       # Discover per-city news sources (>= 10 per city)
    build_global_sources,         # Build global pool (>= 100 unique sources)
)

def fetch_city_boundary_geojson(city: str, country: Optional[str] = None, session: Optional[requests.Session] = None, delay_sec: float = 1.0) -> Optional[Dict[str, Any]]:
    s = session or build_http_session()
    q = city if not country else f"{city}, {country}"
    url = "https://nominatim.openstreetmap.org/search"
    params = {"format": "json", "polygon_geojson": 1, "q": q}
    headers = {
        "User-Agent": DEFAULT_HEADERS.get("User-Agent", "OurCityHealth/1.0"),
        "Accept-Language": DEFAULT_HEADERS.get("Accept-Language", "en-US,en;q=0.9"),
    }
    try:
        resp = s.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            arr = resp.json()
            for item in arr:
                gj = item.get("geojson")
                if gj and gj.get("type") in ("Polygon", "MultiPolygon"):
                    time.sleep(delay_sec)
                    return gj
    except Exception:
        return None
    return None

def build_city_boundaries_geojson(cities: List[Tuple[str, Optional[str]]], out_path: str) -> int:
    features: List[Dict[str, Any]] = []
    s = build_http_session()
    for city, country in cities:
        gj = fetch_city_boundary_geojson(city, country, session=s)
        if not gj:
            continue
        feat = {
            "type": "Feature",
            "properties": {"name": city, "country": country or ""},
            "geometry": gj,
        }
        features.append(feat)
    fc = {"type": "FeatureCollection", "features": features}
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(fc, f)
    except Exception:
        pass
    return len(features)

# =========================
# CONFIGURATION SECTION
# =========================

# List of international news websites we want to scrape
# Each website will be visited to collect recent articles
NEWS_SOURCES = [
    # Major US and Global news sources
    "https://www.nytimes.com",          # New York Times
    "https://www.cnn.com",              # CNN
    "https://www.bbc.com",              # BBC (British)
    "https://www.reuters.com",          # Reuters (International)
    "https://www.theguardian.com",      # The Guardian (British)
    "https://apnews.com",               # Associated Press
    "https://www.aljazeera.com",        # Al Jazeera (Middle East)
    "https://www.economist.com",        # The Economist

    # Asian news sources
    "https://www.scmp.com",                  # South China Morning Post (Hong Kong)
    "https://www.japantimes.co.jp",          # Japan Times
    "https://www.asahi.com/ajw",             # Asahi Shimbun (Japan, English version)
    "https://koreaherald.com",               # Korea Herald
    "https://www.koreatimes.co.kr",          # Korea Times
    "https://www.channelnewsasia.com",       # Channel News Asia (Singapore)
    "https://www.straitstimes.com",          # Straits Times (Singapore)
    "https://www.thehindu.com",              # The Hindu (India)
    "https://timesofindia.indiatimes.com",   # Times of India
    "https://www.bangkokpost.com",           # Bangkok Post (Thailand)
    "https://www.thejakartapost.com",        # Jakarta Post (Indonesia)
    "https://www.rappler.com",               # Rappler (Philippines)
    "https://www.dawn.com",                  # Dawn (Pakistan)

    # Australian and New Zealand sources
    "https://www.abc.net.au/news",           # ABC News Australia
    "https://www.smh.com.au",                # Sydney Morning Herald
    "https://www.theage.com.au",             # The Age (Melbourne)
    "https://www.news.com.au",               # News.com.au
    "https://www.nzherald.co.nz",            # New Zealand Herald
    "https://www.stuff.co.nz",               # Stuff (New Zealand)

    # Additional European sources
    "https://www.dw.com",                    # Deutsche Welle (Germany)
    "https://www.euronews.com",              # Euronews
    # Additional major and high-reliability outlets to expand static pool (>150 overall after discovery)
    "https://www.ft.com",                    # Financial Times (UK)
    "https://www.washingtonpost.com",        # Washington Post (US)
    "https://www.wsj.com",                   # Wall Street Journal (US)
    "https://www.latimes.com",               # Los Angeles Times (US)
    "https://www.usatoday.com",              # USA Today (US)
    "https://www.nbcnews.com",               # NBC News (US)
    "https://www.abcnews.go.com",            # ABC News (US)
    "https://www.cbsnews.com",               # CBS News (US)
    "https://www.foxnews.com",               # Fox News (US)
    "https://www.pbs.org/newshour",          # PBS NewsHour (US)
    "https://www.npr.org",                   # NPR (US)
    "https://www.bloomberg.com",             # Bloomberg (US)
    "https://www.politico.com",              # Politico (US/EU)
    "https://www.time.com",                  # TIME (US)
    "https://www.newsweek.com",              # Newsweek (US)
    "https://www.theatlantic.com",           # The Atlantic (US)
    "https://www.vox.com",                   # Vox (US)
    "https://www.axios.com",                 # Axios (US)
    "https://www.thetimes.co.uk",            # The Times (UK)
    "https://www.telegraph.co.uk",           # The Telegraph (UK)
    "https://www.independent.co.uk",         # The Independent (UK)
    "https://www.standard.co.uk",            # Evening Standard (UK)
    "https://www.irishtimes.com",            # Irish Times (IE)
    "https://www.rte.ie/news/",              # RTE News (IE)
    "https://www.lemonde.fr",                # Le Monde (FR)
    "https://www.lefigaro.fr",               # Le Figaro (FR)
    "https://www.liberation.fr",             # Libération (FR)
    "https://www.elpais.com",                # El País (ES)
    "https://www.elmundo.es",                # El Mundo (ES)
    "https://www.lavanguardia.com",          # La Vanguardia (ES)
    "https://www.corriere.it",               # Corriere della Sera (IT)
    "https://www.repubblica.it",             # La Repubblica (IT)
    "https://www.lastampa.it",               # La Stampa (IT)
    "https://www.spiegel.de",                # Der Spiegel (DE)
    "https://www.sueddeutsche.de",           # Süddeutsche Zeitung (DE)
    "https://www.faz.net",                   # Frankfurter Allgemeine (DE)
    "https://www.tagesschau.de",             # Tagesschau (DE)
    "https://www.nos.nl",                    # NOS (NL)
    "https://www.volkskrant.nl",             # de Volkskrant (NL)
    "https://www.nrc.nl",                    # NRC (NL)
    "https://www.aftonbladet.se",            # Aftonbladet (SE)
    "https://www.dn.se",                     # Dagens Nyheter (SE)
    "https://www.vg.no",                     # VG (NO)
    "https://www.aftenposten.no",            # Aftenposten (NO)
    "https://www.yle.fi",                    # Yle (FI)
    "https://www.hs.fi",                     # Helsingin Sanomat (FI)
    "https://www.rtve.es",                   # RTVE (ES, TV)
    "https://www.france24.com",              # France 24 (FR)
    "https://www.ansa.it",                   # ANSA (IT)
    "https://www.eluniversal.com.mx",        # El Universal (MX)
    "https://www.milenio.com",               # Milenio (MX)
    "https://www.lanacion.com.ar",           # La Nación (AR)
    "https://www.clarin.com",                # Clarín (AR)
    "https://oglobo.globo.com",              # O Globo (BR)
    "https://www.folha.uol.com.br",          # Folha de S.Paulo (BR)
    "https://www.estadao.com.br",            # O Estado de S. Paulo (BR)
    "https://www.oantagonista.com",          # O Antagonista (BR)
    "https://www.eltiempo.com",              # El Tiempo (CO)
    "https://www.semana.com",                # Semana (CO)
    "https://www.elcomercio.pe",             # El Comercio (PE)
    "https://www.eluniverso.com",            # El Universo (EC)
    "https://www.elmercurio.com",            # El Mercurio (CL)
    "https://www.aa.com.tr/en",              # Anadolu Agency (TR)
    "https://english.alarabiya.net",         # Al Arabiya (SA/UAE)
    "https://www.thenationalnews.com",       # The National (UAE)
    "https://www.haaretz.com",               # Haaretz (IL)
    "https://www.timesofisrael.com",         # Times of Israel (IL)
    "https://www.hindustantimes.com",        # Hindustan Times (IN)
    "https://indianexpress.com",             # The Indian Express (IN)
    "https://www.livemint.com",              # Mint (IN)
    "https://www.deccanherald.com",          # Deccan Herald (IN)
    "https://www.japantimes.co.jp",          # Japan Times (JP)
    "https://www.asahi.com/ajw",             # Asahi Shimbun (JP)
    "https://www.mainichi.jp/english",       # Mainichi (JP)
    "https://www.yomiuri.co.jp/world/asia/", # Yomiuri (JP, EN section varies)
    "https://koreaherald.com",               # Korea Herald (KR)
    "https://www.koreatimes.co.kr",          # Korea Times (KR)
    "https://www.scmp.com",                   # SCMP (HK)
    "https://www.channelnewsasia.com",       # CNA (SG)
    "https://www.straitstimes.com",          # Straits Times (SG)
    "https://www.thejakartapost.com",        # Jakarta Post (ID)
    "https://www.rappler.com",               # Rappler (PH)
    "https://www.dawn.com",                  # Dawn (PK)
    "https://www.abc.net.au/news",           # ABC Australia (AU)
    "https://www.smh.com.au",                # Sydney Morning Herald (AU)
    "https://www.theage.com.au",             # The Age (AU)
    "https://www.nzherald.co.nz",            # NZ Herald (NZ)
]

# Dictionary mapping city names to their Reddit community names
# Key = Official city name, Value = Reddit subreddit name
CITY_SUBREDDITS = {
    "New York City": "nyc",                 # r/nyc subreddit
    "Los Angeles": "LosAngeles",            # r/LosAngeles subreddit
    "San Francisco": "sanfrancisco",        # r/sanfrancisco subreddit
    "Chicago": "chicago",                   # r/chicago subreddit
    "Seattle": "Seattle",                   # r/Seattle subreddit
    "Boston": "boston",                     # r/boston subreddit
    "London": "london",                     # r/london subreddit
    "Paris": "paris",                       # r/paris subreddit
    "Berlin": "berlin",                     # r/berlin subreddit
    "Toronto": "toronto",                   # r/toronto subreddit
    "Vancouver": "vancouver",               # r/vancouver subreddit
    "Sydney": "sydney",                     # r/sydney subreddit
    "Melbourne": "melbourne",               # r/melbourne subreddit
    "Singapore": "singapore",               # r/singapore subreddit
    "Hong Kong": "hongkong",                # r/hongkong subreddit
    "Tokyo": "tokyo",                       # r/tokyo subreddit
    "Seoul": "seoul",                       # r/seoul subreddit
    "Mumbai": "mumbai",                     # r/mumbai subreddit
    "Delhi": "delhi",                       # r/delhi subreddit
    "Dubai": "dubai",                       # r/dubai subreddit
    "Johannesburg": "johannesburg",         # r/johannesburg subreddit
    "Nairobi": "nairobi",                   # r/nairobi subreddit
    "Mexico City": "mexicocity",            # r/mexicocity subreddit
    "Sao Paulo": "saopaulo",                # r/saopaulo subreddit
    "Rio de Janeiro": "riodejaneiro",       # r/riodejaneiro subreddit
    "Buenos Aires": "buenosaires",          # r/buenosaires subreddit
    "Madrid": "madrid",                     # r/madrid subreddit
    "Barcelona": "barcelona",               # r/barcelona subreddit
    "Rome": "rome",                         # r/rome subreddit
    "Amsterdam": "amsterdam",               # r/amsterdam subreddit
}

# Dictionary for recognizing different ways cities can be mentioned in text
# This helps us detect when articles are talking about specific cities
CITY_SYNONYMS = {
    # New York City variations
    "new york": "New York City",            # Standard name
    "nyc": "New York City",                 # Common abbreviation
    "new york city": "New York City",       # Full official name
    "manhattan": "New York City",           # Borough name
    "brooklyn": "New York City",            # Borough name
    "queens": "New York City",              # Borough name
    "bronx": "New York City",               # Borough name
    "staten island": "New York City",       # Borough name
    
    # Los Angeles variations
    "los angeles": "Los Angeles",           # Full name
    "la": "Los Angeles",                    # Common abbreviation
    "l.a.": "Los Angeles",                  # Abbreviation with periods
    
    # San Francisco variations
    "san francisco": "San Francisco",       # Full name
    "sf": "San Francisco",                  # Common abbreviation
    "bay area": "San Francisco",            # Regional name
    
    # Other major cities (one entry each for simplicity)
    "london": "London",                     # UK capital
    "paris": "Paris",                       # French capital
    "berlin": "Berlin",                     # German capital
    "toronto": "Toronto",                   # Canadian city
    "vancouver": "Vancouver",               # Canadian city
    "sydney": "Sydney",                     # Australian city
    "melbourne": "Melbourne",               # Australian city
    "singapore": "Singapore",               # City-state
    "hong kong": "Hong Kong",               # Special administrative region
    "hk": "Hong Kong",                      # Common abbreviation
    "tokyo": "Tokyo",                       # Japanese capital
    "seoul": "Seoul",                       # South Korean capital
    "mumbai": "Mumbai",                     # Indian city
    "bombay": "Mumbai",                     # Old name for Mumbai
    "delhi": "Delhi",                       # Indian capital region
    "new delhi": "Delhi",                   # Capital city
    "dubai": "Dubai",                       # UAE city
    "johannesburg": "Johannesburg",         # South African city
    "joburg": "Johannesburg",               # Nickname for Johannesburg
    "nairobi": "Nairobi",                   # Kenyan capital
    "mexico city": "Mexico City",           # Mexican capital
    "cdmx": "Mexico City",                  # Spanish abbreviation
    "sao paulo": "Sao Paulo",               # Brazilian city
    "rio": "Rio de Janeiro",                # Common short name
    "rio de janeiro": "Rio de Janeiro",     # Full name
    "buenos aires": "Buenos Aires",         # Argentine capital
    "madrid": "Madrid",                     # Spanish capital
    "barcelona": "Barcelona",               # Spanish city
    "rome": "Rome",                         # Italian capital
    "amsterdam": "Amsterdam",               # Dutch capital
}

# The 12 dimensions we use to measure civic health
# These represent different aspects of city life quality
CIVIC_DIMENSIONS = [
    "affordability",    # How expensive it is to live in the city
    "services",         # Quality of public services (hospitals, schools, etc.)
    "safety",           # Crime rates and public safety measures
    "opportunity",      # Job opportunities and economic mobility
    "culture",          # Arts, events, cultural life, diversity
    "environment",      # Air quality, sustainability, climate resilience
    "transportation",   # Public transit, traffic, infrastructure quality
    "governance",       # Government effectiveness and transparency
    "housing",          # Housing availability, quality, and accessibility
    "economy",          # Economic health, growth, and stability
    "education",        # Quality of educational institutions and access
    "health",           # Healthcare access, quality, and public health
]

# Settings that control how much data we collect
# MAXIMIZED FOR HIGHEST ACCURACY - Collect as much data as possible
PER_SOURCE_ARTICLE_LIMIT = 500      # How many articles to get from each news site (MAXIMIZED)
REDDIT_MAX_PAGES = 10               # How many pages of Reddit posts to scrape per city (MAXIMIZED)
REDDIT_COMMENTS_PER_POST_LIMIT = 100 # How many comments to collect per Reddit post (MAXIMIZED)
GLOBAL_SAMPLE_TITLES_FOR_TOPICS = 200  # How many article titles to send to AI for topic analysis (INCREASED)
KEYWORD_PHRASE_LIMIT_FOR_TOPICS = 1000 # How many keyword phrases to analyze for topics (MAXIMIZED)
CITY_DOCS_PER_MODEL_CALL = 100     # How many documents to send to AI per city (INCREASED for better analysis)

# OpenAI API settings
# The AI model to use and where to find the API key
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Use environment variable or default to mini model
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Must be set in your shell before running script

# Standard headers to send with web requests
# This makes our requests look like they're coming from a real web browser
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",  # Pretend to be Chrome browser
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",  # Accept HTML and XML content
    "Accept-Language": "en-US,en;q=0.9",    # Prefer English content
    "Connection": "keep-alive",              # Keep connection open for efficiency
    "Referer": "https://www.google.com/",    # Pretend we came from Google
    "Accept-Encoding": "gzip, deflate, br",  # Enable compression
}

# =========================
# DATA STRUCTURES
# =========================

# Define a data structure to hold information about each article/post/comment
@dataclass
class Entry:
    source: str                 # Type of content: 'News', 'RedditPost', or 'RedditComment'
    source_site: str            # Which website it came from (e.g., 'www.nytimes.com' or 'r/nyc')
    url: str                    # The web address of the article/post
    title: str                  # The headline or title of the content
    date: Optional[str]         # When it was published (if available, None if unknown)
    text: str                   # The main content text
    cities: List[str]           # Which cities this content is about (detected by AI)

# =========================
# UTILITY FUNCTIONS
# =========================

def safe_request(url: str, headers: Optional[dict] = None, timeout: int = 20, max_retries: int = 2) -> Optional[str]:
    """
    Safely download a web page with error handling and retries
    
    Args:
        url: The web address to download
        headers: HTTP headers to send (defaults to our standard browser headers)
        timeout: How long to wait before giving up (in seconds)
        max_retries: How many times to try if it fails
    
    Returns:
        The HTML content of the page, or None if it failed
    """
    hdrs = headers or DEFAULT_HEADERS  # Use provided headers or our default browser headers
    
    # Try multiple times in case of temporary network issues
    for attempt in range(max_retries):         # Loop through retry attempts
        try:
            # Make the HTTP request to download the webpage
            r = requests.get(url, headers=hdrs, timeout=timeout)  # Send GET request with headers and timeout
            # Check if the request was successful (status code 200 means "OK")
            if r.status_code == 200:           # If server responded with success
                return r.text                  # Return the HTML content as text
            # Backoff on rate-limit
            if r.status_code == 429:
                backoff = min(8.0, 0.5 * (2 ** attempt)) + random.uniform(0.0, 0.5)
                time.sleep(backoff)
                continue
            # Retry on transient server errors
            if 500 <= r.status_code < 600:
                time.sleep(0.4 + 0.2 * attempt)
                continue
        except Exception:                      # If any error occurs (network, timeout, etc.)
            pass                               # Ignore the error and try again
        
        # Wait a bit before trying again (longer wait each time)
        time.sleep(0.6 * (attempt + 1))       # Sleep 0.6s on first retry, 1.2s on second, etc.
    
    # If all attempts failed, return None
    return None                                # Indicate that the download completely failed

def build_http_session() -> requests.Session:
    """
    Create a shared HTTP session with connection pooling, compression, and retries.
    """
    sess = requests.Session()
    sess.headers.update(DEFAULT_HEADERS)
    # Retry policy: 1 retry with exponential backoff for idempotent methods
    if Retry is not None:
        retry = Retry(total=1, backoff_factor=0.6, status_forcelist=(502, 503, 504), allowed_methods=("GET",))
        adapter = requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=retry)
    else:
        adapter = requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32)
    sess.mount('http://', adapter)
    sess.mount('https://', adapter)
    return sess

def truncate_words(s: str, max_words: int) -> str:
    """
    Cut off text after a certain number of words to keep things manageable
    
    Args:
        s: The text to truncate
        max_words: Maximum number of words to keep
    
    Returns:
        The truncated text with "…" at the end if it was cut off
    """
    parts = s.split()                          # Split the text into individual words using spaces
    if len(parts) <= max_words:                # If the text is already short enough
        return s                               # Return the original text unchanged
    # Otherwise, take only the first max_words and add "…" to show it was cut off
    return " ".join(parts[:max_words]) + " …"  # Join first max_words with spaces, add ellipsis

def unique_preserve_order(seq: List[str]) -> List[str]:
    """
    Remove duplicates from a list while keeping the original order
    
    Args:
        seq: List that might have duplicate items
    
    Returns:
        New list with duplicates removed, original order preserved
    """
    seen = set()                               # Keep track of items we've already encountered
    out = []                                   # The new list we're building without duplicates
    for x in seq:                              # Go through each item in the original list
        if x not in seen:                      # If we haven't seen this item before
            seen.add(x)                        # Remember that we've now seen it
            out.append(x)                      # Add it to our new deduplicated list
    return out                                 # Return the list without duplicates

# -------------------------
# SMART SELECTION HELPERS
# -------------------------

def _norm_domain(host: str) -> str:
    host = (host or "").lower().strip()
    if host.startswith("r/"):
        return "reddit"
    host = host.replace("https://", "").replace("http://", "")
    host = host.split("/")[0]
    if host.startswith("www."):
        host = host[4:]
    return host

# Baseline domain reputation (extendable). Values in [0,1]
DOMAIN_REPUTATION: Dict[str, float] = {
    "nytimes.com": 0.95, "bbc.com": 0.95, "bbc.co.uk": 0.95, "reuters.com": 0.95,
    "apnews.com": 0.92, "theguardian.com": 0.90, "wsj.com": 0.92, "washingtonpost.com": 0.92,
    "aljazeera.com": 0.88, "bloomberg.com": 0.92, "ft.com": 0.92, "economist.com": 0.92,
    "scmp.com": 0.88, "abc.net.au": 0.86, "straitstimes.com": 0.86, "cna.asia": 0.85,
    "cnn.com": 0.88, "latimes.com": 0.87, "smh.com.au": 0.86, "lemonde.fr": 0.90,
}

# Simple keyword sets per civic dimension for relevance scoring
DIMENSION_SYNONYMS: Dict[str, List[str]] = {
    "affordability": ["affordable", "cost of living", "rent", "rents", "price", "prices", "inflation", "wage", "income", "poverty"],
    "services": ["public service", "hospital", "clinic", "school", "sanitation", "utilities", "welfare", "childcare"],
    "safety": ["crime", "violent", "police", "homicide", "shooting", "assault", "theft", "robbery", "burglary", "safety"],
    "opportunity": ["job", "jobs", "employment", "unemployment", "startup", "entrepreneur", "mobility", "wages", "career", "hiring"],
    "culture": ["culture", "arts", "museum", "festival", "music", "theater", "sport", "diversity", "community"],
    "environment": ["air quality", "pollution", "emissions", "carbon", "sustainability", "climate", "flood", "heat", "waste", "recycle"],
    "transportation": ["transport", "subway", "metro", "bus", "train", "rail", "traffic", "congestion", "road", "bike", "parking", "airport"],
    "governance": ["governance", "mayor", "council", "policy", "corruption", "transparency", "budget", "tax", "regulation", "zoning"],
    "housing": ["housing", "home", "apartment", "mortgage", "eviction", "homeless", "shelter", "tenant", "landlord", "affordable housing"],
    "economy": ["economy", "gdp", "investment", "industry", "business", "tourism", "trade", "market", "growth"],
    "education": ["education", "school", "university", "college", "teacher", "student", "curriculum", "literacy", "enrollment", "graduation"],
    "health": ["health", "healthcare", "hospital", "clinic", "disease", "vaccination", "mental health", "public health", "mortality"],
}

def _civic_relevance_score(text: str, title: str) -> float:
    blob = (title + " " + text).lower()
    hits = 0
    for terms in DIMENSION_SYNONYMS.values():
        for t in terms:
            if t in blob:
                hits += 1
    return min(hits / 8.0, 1.0)

def _days_ago_from_iso(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt if dt.tzinfo else datetime.utcnow() - dt
        return max(0, int(delta.total_seconds() // 86400))
    except Exception:
        return None

def _recency_score(iso_date: Optional[str]) -> float:
    d = _days_ago_from_iso(iso_date)
    if d is None:
        return 0.5
    if d <= 14: return 1.0
    if d <= 30: return 0.9
    if d <= 90: return 0.7
    if d <= 180: return 0.55
    if d <= 365: return 0.45
    return 0.35

def score_entry_for_city(e: Entry, city: str, nlp) -> float:
    if e.source == "News":
        q = DOMAIN_REPUTATION.get(_norm_domain(e.source_site), 0.60)
    elif e.source == "RedditPost":
        q = 0.58
    else:
        q = 0.52

    length_score = min(len((e.text or "").split()) / 600.0, 1.0)
    rel_score = _civic_relevance_score(e.text or "", e.title or "")
    time_score = _recency_score(e.date)
    return (0.30 * q) + (0.45 * rel_score) + (0.15 * length_score) + (0.10 * time_score)

def smart_select_for_city(city: str, entries: List[Entry], target_n: int, nlp) -> List[Entry]:
    if target_n <= 0 or not entries:
        return []
    if len(entries) <= target_n:
        return entries[:]

    scored: List[Tuple[float, str, Entry]] = []
    for e in entries:
        try:
            s = score_entry_for_city(e, city, nlp)
        except Exception:
            s = 0.0
        if e.source == "News":
            dkey = _norm_domain(e.source_site)
        else:
            dkey = e.source
        scored.append((s, dkey, e))

    scored.sort(key=lambda x: x[0], reverse=True)

    domains = {d for _, d, _ in scored}
    approx_domains = max(1, len(domains))
    max_per_domain = max(3, target_n // max(8, approx_domains))

    picked: List[Entry] = []
    used_titles: Set[str] = set()
    per_domain: Dict[str, int] = defaultdict(int)

    def _title_key(e: Entry) -> str:
        t = (e.title or "").lower()
        return " ".join([w for w in t.replace("-", " ").split()[:12]])

    for _, d, e in scored:
        if len(picked) >= target_n:
            break
        if per_domain[d] >= max_per_domain:
                continue
        tk = _title_key(e)
        if tk in used_titles:
            continue
        picked.append(e)
        used_titles.add(tk)
        per_domain[d] += 1

    if len(picked) < target_n:
        for _, d, e in scored:
            if len(picked) >= target_n:
                break
            tk = _title_key(e)
            if tk in used_titles:
                continue
            if e in picked:
                continue
            picked.append(e)
            used_titles.add(tk)

    return picked[:target_n]

@contextmanager
def time_limit(seconds: int):
    """
    A placeholder function for timeout functionality
    (This is a simplified version - the real timeout logic was removed for stability)
    """
    yield                                      # Just continue without actually implementing timeout

def get_domain(url: str) -> str:
    """
    Extract the domain name from a URL
    
    Args:
        url: A full URL like "https://www.nytimes.com/article/123"
    
    Returns:
        Just the domain part like "www.nytimes.com"
    """
    try:
        # Use urlparse to break down the URL and get just the domain part
        return urlparse(url).netloc            # Extract the network location (domain) from URL
    except Exception:                          # If URL parsing fails for any reason
        return ""                              # Return empty string as fallback

# =========================
# WEB SCRAPING FUNCTIONS
# =========================

# -------------------------
# SQLITE CACHE (VISITED URLS)
# -------------------------

CACHE_LOCK = threading.Lock()

def _init_cache(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS visited (url TEXT PRIMARY KEY, first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS visited_reddit_posts (url TEXT PRIMARY KEY, first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    # Cumulative distinct counters table
    conn.execute("CREATE TABLE IF NOT EXISTS metrics (k TEXT PRIMARY KEY, v INTEGER NOT NULL)")
    for k in ("articles_distinct", "reddit_posts_distinct", "reddit_comments_total"):
        conn.execute("INSERT OR IGNORE INTO metrics(k,v) VALUES(?,0)", (k,))
    conn.commit()
    return conn

def cache_has(conn: sqlite3.Connection, url: str) -> bool:
    with CACHE_LOCK:
        cur = conn.execute("SELECT 1 FROM visited WHERE url=?", (url,))
        return cur.fetchone() is not None

def cache_put(conn: sqlite3.Connection, url: str) -> None:
    try:
        with CACHE_LOCK:
            conn.execute("INSERT OR IGNORE INTO visited(url) VALUES(?)", (url,))
            conn.commit()
    except Exception:
        pass

def extract_links_from_homepage(base_url: str, html: str, limit: int) -> List[str]:
    """
    Find article links on a news website's homepage
    
    Args:
        base_url: The main website URL (e.g., "https://www.nytimes.com")
        html: The HTML content of the homepage
        limit: Maximum number of links to collect
    
    Returns:
        List of article URLs found on the homepage
    """
    soup = BeautifulSoup(html, "html.parser")  # Parse the HTML content into a searchable structure
    links: List[str] = []                      # Initialize empty list to store the links we find
    base_domain = get_domain(base_url)         # Get the domain of the main site (e.g., "www.nytimes.com")
    
    # Words that indicate a link is probably not a news article
    # We want to avoid login pages, ads, newsletters, etc.
    disallow = (
        "login", "subscribe", "privacy", "terms", "contact", "about", "account",     # Account-related pages
        "profile", "help", "signup", "register", "cookie", "advert", "ads",         # User/admin pages
        "newsletter", "newsletters", "video", "videos", "watch", "live", "sport",   # Media/entertainment
        "sports", "weather", "sso", "comment-policy"                                # Other non-article pages
    )
    
    # Look through all the links on the page
    for a in soup.find_all("a", href=True):   # Find all <a> tags that have an href attribute
        href = a.get("href").strip()           # Get the link URL and remove any whitespace
        if not href or href.startswith("#"):  # Skip empty links or page anchors (internal links)
            continue                           # Move to the next link
        
        # Convert relative URLs to absolute URLs (e.g., "/article" becomes "https://site.com/article")
        full = urljoin(base_url, href)         # Combine base URL with the link to make it complete
        d = get_domain(full)                   # Get the domain of this link
        
        # Only keep links that are on the same website (avoid external links)
        if d != base_domain:                   # If this link goes to a different website
            continue                           # Skip it and move to the next link
        
        # Parse the URL to examine its structure
        parsed = urlparse(full)                # Break down the URL into components
        path = parsed.path or "/"              # Get the path part of the URL (everything after domain)
        
        # Skip links that contain words from our disallow list
        if any(k in path.lower() for k in disallow):  # Check if any forbidden words are in the path
            continue                           # Skip this link if it matches forbidden patterns
        
        # Break the path into segments (parts separated by "/")
        segments = [seg for seg in path.split("/") if seg]  # Split path by "/" and remove empty segments
        
        # Skip if the path is too short (probably not an article)
        if len(segments) < 2:                  # If path has fewer than 2 segments
            continue                           # Skip it (probably just the homepage)
        
        # Check if the path looks like it could be an article
        # Articles usually have segments with letters, hyphens, and reasonable length
        if not any(("-" in seg or seg.isalpha()) and len(seg) >= 4 for seg in segments):
            continue                           # Skip if path doesn't look like an article URL
        
        # If this link passes all our tests, add it to our collection
        if full not in links:                  # If we haven't already collected this link
            links.append(full)                 # Add it to our list of article URLs
        
        # Stop when we have enough links (collect extra since some might not be real articles)
        if len(links) >= limit * 6:           # Collect 6x the limit to account for filtering (increased for more coverage)
            break                              # Stop searching for more links
    
    return links                               # Return the list of article URLs we found

def parse_rss_for_links(feed_xml: str, limit: int) -> List[str]:
    links: List[str] = []
    if feedparser is not None:
        try:
            fp = feedparser.parse(feed_xml)
            for e in fp.entries[:limit]:
                link = getattr(e, 'link', None)
                if link:
                    links.append(link)
            return links
        except Exception:
            pass
    # Fallback simple XML
    try:
        root = ET.fromstring(feed_xml)
        for item in root.findall('.//item'):
            link = item.findtext('link')
            if link:
                links.append(link)
                if len(links) >= limit:
                    break
    except Exception:
        return []
    return links

def discover_article_links(base_url: str, session: requests.Session, limit: int) -> List[str]:
    """
    Prefer RSS/sitemap discovery; then TOP-UP with homepage extraction to reach a healthy candidate set.
    """
    candidates: List[str] = []
    seen: Set[str] = set()

    def add_links(links: List[str]):
        for u in links:
            if u and u not in seen:
                seen.add(u)
                candidates.append(u)

    # Try common RSS endpoints and accumulate
    rss_paths = ["/rss", "/feed", "/rss.xml", "/feeds/all.rss", "/feeds/rss.xml"]
    for p in rss_paths:
        try:
            resp = session.get(urljoin(base_url, p), timeout=8)
            if resp.status_code == 200 and resp.text:
                links = parse_rss_for_links(resp.text, limit)
                add_links(links)
                if len(candidates) >= limit * 2:
                    break
        except Exception:
            continue

    # Try sitemap and accumulate
    try:
        resp = session.get(urljoin(base_url, "/sitemap.xml"), timeout=8)
        if resp.status_code == 200 and resp.text:
            try:
                root = ET.fromstring(resp.text)
                for loc in root.findall('.//{*}loc'):
                    url = loc.text or ""
                    if url and any(seg in url for seg in ("/news/", "/article", "/stories", "/world/", "/business/")):
                        add_links([url])
                        if len(candidates) >= limit * 2:
                            break
            except Exception:
                pass
    except Exception:
        pass

    # Fallback/top-up via homepage parsing
    try:
        homepage_html = session.get(base_url, timeout=8).text if base_url else ""
    except Exception:
        homepage_html = ""
    if homepage_html:
        more = extract_links_from_homepage(base_url, homepage_html, limit)
        add_links(more)

    return candidates[: max(limit * 2, len(candidates))]

def extract_title_and_text(html: str) -> Tuple[str, str]:
    """
    Extract the title and main text content from an article's HTML
    
    Args:
        html: The HTML content of the article page
    
    Returns:
        A tuple containing (title, main_text)
    """
    soup = BeautifulSoup(html, 'html.parser')  # Parse the HTML content into a searchable structure
    
    # Remove elements we don't want (scripts, navigation, ads, etc.)
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):  # Find unwanted tags
        tag.decompose()                        # Completely remove these tags from the HTML
    
    # Try to find the article title using multiple methods
    title = ''                                 # Initialize empty title string
    
    # Method 1: Look for Open Graph title (used by social media sharing)
    og = soup.find('meta', attrs={'property': 'og:title'})  # Find the Open Graph title meta tag
    if og and og.get('content'):               # If the tag exists and has content
        title = og['content'].strip()          # Use this as the title, removing whitespace
    
    # Method 2: Use the HTML <title> tag if we didn't find Open Graph title
    if not title and soup.title and soup.title.string:  # If no title yet and <title> tag exists
        title = soup.title.string.strip()     # Use the title tag content, removing whitespace
    
    # Method 3: Look for the main headline (<h1> tag) as last resort
    if not title:                              # If we still don't have a title
        h1 = soup.find('h1')                   # Find the first <h1> tag on the page
        if h1:                                 # If an <h1> tag exists
            title = h1.get_text(strip=True)    # Use its text content as the title
    
    # Now extract the main article text content
    texts: List[str] = []                      # Initialize list to store paragraphs of text
    
    # Try to find the main content area using different common HTML patterns
    roots = [
        soup.find('article'),                           # Look for <article> tag (semantic HTML)
        soup.find('main'),                              # Look for <main> tag (semantic HTML)
        soup.find(attrs={'role': 'main'}),              # Look for role="main" attribute
        soup.find('div', attrs={'itemprop': 'articleBody'}),  # Look for structured data markup
        soup.find('section', class_='article'),         # Look for article section with class
        soup.find('div', id='main-content'),            # Look for main content div by ID
    ]
    
    # Use the first content container we find, or fall back to searching the whole page
    container = next((r for r in roots if r), None)    # Get first non-None container from the list
    
    # Find all paragraph tags in the content area (or whole page if no container found)
    ps = container.find_all('p') if container else soup.find_all('p')  # Get all <p> tags from container or page
    
    # Extract text from each paragraph
    for p in ps:                               # Loop through each paragraph tag
        t = p.get_text(" ", strip=True)        # Get text content, replace line breaks with spaces, strip whitespace
        if t and len(t.split()) >= 3:          # Only keep paragraphs with at least 3 words (relaxed filter for more content)
            texts.append(t)                    # Add this paragraph to our text collection
        if len(texts) >= 200:                  # Stop after collecting 200 paragraphs (MAXIMIZED for comprehensive analysis)
            break                              # Exit the loop early
    
    # Join all paragraphs into one text block
    text = "\n".join(texts)                    # Combine all paragraphs with newlines between them
    
    return title, text                         # Return both the title and the combined text

def scrape_news_site(base_url: str, label: str, limit: int) -> List[Entry]:
    """
    Scrape articles from a single news website
    
    Args:
        base_url: The main URL of the news site (e.g., "https://www.nytimes.com")
        label: A friendly name for the site (for display purposes)
        limit: Maximum number of articles to collect from this site
    
    Returns:
        List of Entry objects containing the scraped articles
    """
    print(f"[news] Using requests extractor for {label}")  # Show progress message to user
    entries: List[Entry] = []                  # Initialize empty list to store articles we find

    session = build_http_session()             # Connection pooling session
    cache = _init_cache(os.path.join("data", "visited.sqlite"))  # SQLite cache
    
    # Step 1: Prefer RSS/sitemap, fallback to homepage
    candidates = discover_article_links(base_url, session, limit * 2)  # Discover article URLs efficiently
    if not candidates:
        return entries
    
    # Step 2: Download and process each article (parallel)
    count = 0                                  # Initialize counter for successfully processed articles
    total_candidates = len(candidates)         # Get total number of candidate URLs for progress tracking
    def fetch_one(u: str) -> Optional[Entry]:
        try:
            if cache_has(cache, u):
                return None
            resp = session.get(u, timeout=8)
            if resp.status_code != 200 or not resp.text:
                return None
            title, text = extract_title_and_text(resp.text)
            if not (title or text) or (len(text.split()) < 5 and len(title) < 2):
                return None
            cache_put(cache, u)
            return Entry(
                source="News",
                source_site=label,
                url=u,
                title=title,
                date=None,
                text=text,
                cities=[],
            )
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=24) as ex:  # Concurrency (cap per site)
        futures = [ex.submit(fetch_one, u) for u in candidates[: limit * 3]]
        for i, fut in enumerate(as_completed(futures), 1):
            if count >= limit:
                break
            if i % 50 == 0:
                print(f"    Progress: {i}/{total_candidates} URLs processed, {count} articles collected")
            res = fut.result()
            if res is not None:
                entries.append(res)
                count += 1
    
    return entries                             # Return all the articles we successfully collected

def print_progress_bar(current: int, total: int, prefix: str = "", length: int = 50):
    """
    Print a progress bar showing completion percentage
    
    Args:
        current: Current progress count
        total: Total items to process
        prefix: Text to show before the progress bar
        length: Length of the progress bar in characters
    """
    if total == 0:                             # Avoid division by zero
        percent = 100                          # If no items, show 100%
    else:
        percent = (current / total) * 100      # Calculate percentage completed
    
    filled_length = int(length * current // total) if total > 0 else length  # How many characters to fill
    bar = '█' * filled_length + '-' * (length - filled_length)  # Create the visual bar
    print(f'\r{prefix} |{bar}| {percent:.1f}% ({current}/{total})', end='', flush=True)  # Print progress bar

def scrape_all_news(sites: List[str], per_site_limit: int) -> List[Entry]:
    """
    Scrape articles from all news websites in our list
    
    Args:
        sites: List of news website URLs to scrape
        per_site_limit: How many articles to get from each site
    
    Returns:
        Combined list of all articles from all sites
    """
    results: List[Entry] = []                  # Initialize empty list to store all articles
    total_sites = len(sites)                   # Get total number of sites for progress tracking

    # Parallelize across sites (light concurrency) to speed up total runtime
    def scrape_one(site: str) -> List[Entry]:
        label = site.replace("https://", "").replace("http://", "").split("/")[0]
        print(f"\nScraping news: {label}")
        return scrape_news_site(site, label, per_site_limit)

    with ThreadPoolExecutor(max_workers=8) as ex:  # Cap to be polite across domains
        futs = {ex.submit(scrape_one, s): s for s in sites}
        for i, fut in enumerate(as_completed(futs), 1):
            print_progress_bar(i, total_sites, f"Scraping news sites")
            try:
                chunk = fut.result()
            except Exception:
                chunk = []
            results.extend(chunk)
            time.sleep(0.05)  # small jitter to spread load

    print_progress_bar(total_sites, total_sites, f"Scraping news sites")
    print(f"\nCompleted news scraping: {len(results)} total articles")

    return results

def reddit_fetch_subreddit_json(sub: str, max_pages: int) -> List[Dict[str, Any]]:
    """
    Get posts from a Reddit subreddit using Reddit's JSON API
    
    Args:
        sub: The subreddit name (e.g., "nyc" for r/nyc)
        max_pages: How many pages of posts to collect
    
    Returns:
        List of dictionaries containing post information
    """
    items: List[Dict[str, Any]] = []           # Initialize empty list to store posts
    after: Optional[str] = None                # Reddit pagination token (starts as None)
    
    # Get multiple pages of posts from this subreddit
    for _ in range(max_pages):                 # Loop for the specified number of pages
        # Try multiple endpoints to reduce rate limiting issues
        bases = (
            f"https://api.reddit.com/r/{sub}/.json?limit=50&raw_json=1",
            f"https://old.reddit.com/r/{sub}/.json?limit=50&raw_json=1",
            f"https://www.reddit.com/r/{sub}/.json?limit=50&raw_json=1",
        )
        jtxt = None
        for base in bases:
            url = base + (f"&after={after}" if after else "")
            jtxt = safe_request(url, headers={**DEFAULT_HEADERS, "Accept": "application/json", "Referer": f"https://www.reddit.com/r/{sub}/"}, timeout=12, max_retries=4)
            if jtxt:
                break
        if not jtxt:                           # If download failed
            break                              # Stop trying to get more pages
        
        try:
            # Parse the JSON response from Reddit
            data = json.loads(jtxt)             # Convert JSON string to Python dictionary
        except Exception:                      # If JSON parsing failed
            break                              # Stop trying to get more pages
        
        # Extract the list of posts from Reddit's JSON structure
        children = data.get('data', {}).get('children', [])  # Navigate to the posts array in JSON
        if not children:                       # If no posts found on this page
            break                              # Stop trying to get more pages
        
        # Process each post we found
        for ch in children:                    # Loop through each post in the JSON response
            d = ch.get('data', {})             # Get the post data dictionary
            permalink = d.get('permalink')     # Get the post's permalink (unique path)
            title = d.get('title', '')         # Get the post title (empty string if missing)
            
            # Build the full URL for this post
            full_url = urljoin("https://www.reddit.com/", permalink) if permalink else None  # Create complete URL
            
            # Convert Reddit's timestamp to a readable date format
            created = d.get('created_utc')     # Reddit stores creation time as Unix timestamp
            iso_date = None                    # Initialize date as None
            if isinstance(created, (int, float)):  # If we have a valid timestamp
                # Convert Unix timestamp to ISO format date string
                iso_date = datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
            
            # If we have a valid URL, add this post to our collection
            if full_url:                       # If we successfully built a URL
                items.append({                 # Add post information to our list
                    "url": full_url,           # The complete URL to the post
                    "title": title,            # The post's title
                    "date": iso_date,          # The post's creation date
                    "permalink": permalink     # The permalink for getting comments later
                })
        
        # Get the pagination token for the next page
        after = data.get('data', {}).get('after')  # Reddit provides this token to get next page
        if not after:                          # If no next page token
            break                              # We've reached the end, stop here
        
        # Wait a bit before getting the next page (be gentle with API)
        time.sleep(0.2)
    
    return items                               # Return all the posts we collected

def reddit_fetch_comments_json(permalink: str, limit: int, session: Optional[requests.Session] = None) -> List[str]:
    """
    Get comments from a specific Reddit post using JSON API
    
    Args:
        permalink: The post's permalink (like "/r/nyc/comments/abc123/title/")
        limit: Maximum number of comments to collect
    
    Returns:
        List of comment text strings
    """
    # Try multiple endpoints for the post's JSON data
    bases = (
        "https://api.reddit.com",
        "https://old.reddit.com",
        "https://www.reddit.com",
    )
    jtxt = None
    for host in bases:
        url = urljoin(host, permalink) + ".json?limit=50&raw_json=1"
        jtxt = safe_request(url, headers={**DEFAULT_HEADERS, "Accept": "application/json", "Referer": url}, timeout=12, max_retries=4)
        if jtxt:
            break
    if not jtxt:                               # If download failed
        return []                              # Return empty list
    
    try:
        # Parse the JSON response from Reddit
        data = json.loads(jtxt)                # Convert JSON string to Python data structure
    except Exception:                          # If JSON parsing failed
        return []                              # Return empty list
    
    out: List[str] = []                        # Initialize list to store comment texts
    
    # Reddit returns an array where [0] is the post info and [1] is the comments
    if isinstance(data, list) and len(data) > 1:  # If we have the expected array structure
        comments_listing = data[1]             # Get the comments section (second element)
        
        # Go through each comment in the listing
        for ch in comments_listing.get('data', {}).get('children', []):  # Navigate to comments array
            # Check if this is actually a comment (Reddit has different types of objects)
            if ch.get('kind') != 't1':          # 't1' is Reddit's code for comments
                continue                       # Skip non-comment objects
            
            # Get the comment text content
            body = ch.get('data', {}).get('body')  # Extract the comment body text
            if body:                           # If the comment has text content
                out.append(body.strip())       # Add the comment text to our list (removing whitespace)
            
            # Stop when we have enough comments
            if len(out) >= limit:              # If we've collected the maximum number we want
                break                          # Stop processing more comments
    
    return out                                 # Return all the comment texts we collected

def scrape_reddit_for_cities(city_subreddits: Dict[str, str],
                             max_pages: int,
                             comments_per_post_limit: int) -> List[Entry]:
    """
    Scrape Reddit posts and comments for all cities in our list
    
    Args:
        city_subreddits: Dictionary mapping city names to subreddit names
        max_pages: How many pages to scrape per subreddit
        comments_per_post_limit: How many comments to get per post
    
    Returns:
        List of Entry objects for all posts and comments we collected
    """
    all_entries: List[Entry] = []              # Initialize list to store everything we collect
    total_cities = len(city_subreddits)        # Get total number of cities for progress tracking
    session = build_http_session()             # Shared session for pooling
    
    # Go through each city and its corresponding subreddit
    for i, (city, sub) in enumerate(city_subreddits.items()): # Loop through city -> subreddit mappings with index
        # Show progress bar for Reddit scraping
        print_progress_bar(i, total_cities, f"Scraping Reddit cities")  # Show progress
        print(f"\nScraping subreddit: r/{sub} for {city}")  # Show which city/subreddit we're working on
        
        # Get posts from this subreddit using Reddit's JSON API
        posts = reddit_fetch_subreddit_json(sub, max_pages)  # Fetch posts for this subreddit
        print(f"  -> {len(posts)} posts")      # Show how many posts we successfully got
        
        # Add post entries first
        for p in posts:
            all_entries.append(Entry(
                source="RedditPost",
                source_site=f"r/{sub}",
                url=p["url"],
                title=p["title"],
                date=p.get("date"),
                text=p["title"],
                cities=[city],
            ))

        # Fetch comments for all posts concurrently per subreddit
        permalinks = [(p, p.get("permalink")) for p in posts if p.get("permalink")]
        comments_by_post: Dict[str, List[str]] = {}
        if permalinks:
            with ThreadPoolExecutor(max_workers=16) as ex:
                futs = {ex.submit(reddit_fetch_comments_json, pl, comments_per_post_limit, session): p for p, pl in permalinks}
                for idx, fut in enumerate(as_completed(futs), 1):
                    post = futs[fut]
                    try:
                        comments_by_post[post["url"]] = fut.result() or []
                    except Exception:
                        comments_by_post[post["url"]] = []
                    if idx % 10 == 0:
                        print(f"    Reddit comments progress: {idx}/{len(permalinks)} posts")

        # Create an Entry object for each comment
        for p in posts:
            for c in comments_by_post.get(p["url"], []):
                all_entries.append(Entry(
                    source="RedditComment",
                    source_site=f"r/{sub}",
                    url=p["url"],
                    title=p["title"],
                    date=p.get("date"),
                    text=c,
                    cities=[city],
                ))
            time.sleep(0.01)
    
    # Final progress update for Reddit scraping
    print_progress_bar(total_cities, total_cities, f"Scraping Reddit cities")  # Show 100% completion
    print(f"\nCompleted Reddit scraping: {len(all_entries)} total items")  # Show final count
    
    return all_entries                         # Return all posts and comments we collected

# =========================
# NATURAL LANGUAGE PROCESSING FUNCTIONS
# =========================

def detect_cities_in_text(text: str, title: str, nlp, known_cities: Set[str]) -> List[str]:
    """
    Analyze text to find which cities are mentioned using AI and pattern matching
    
    Args:
        text: The main article text to analyze
        title: The article title to analyze
        nlp: The spaCy language model for AI analysis
        known_cities: Set of city names we're looking for
    
    Returns:
        List of city names found in the text
    """
    found: Set[str] = set()                    # Use a set to automatically avoid duplicate city names
    
    # Combine title and text, convert to lowercase for easier matching
    blob = (title + " " + text).lower()        # Merge title and text, make lowercase for consistent matching
    
    # Method 1: Look for city synonyms and nicknames in the text
    for k, canonical in CITY_SYNONYMS.items():  # Loop through our city synonyms dictionary
        if k in blob:                          # If this synonym appears anywhere in the text
            found.add(canonical)               # Add the canonical city name to our results
    
    # Method 2: Use AI (spaCy) to find geographic entities
    try:
        # Use spaCy NLP to analyze the text (truncate first to save processing time)
        doc = nlp(truncate_words(title + " " + text, 200))  # Process first 200 words with AI
        
        # Look through all the named entities that spaCy identified
        for ent in doc.ents:                   # Loop through each entity found by AI
            # Check if this entity is a geographic place
            if ent.label_ in ("GPE", "LOC"):   # GPE = Geopolitical Entity, LOC = Location
                name = ent.text.lower().strip()  # Get the entity name in lowercase, remove whitespace
                
                # Check if this matches any of our known city synonyms
                if name in CITY_SYNONYMS:      # If AI found a name that's in our synonyms
                    found.add(CITY_SYNONYMS[name])  # Add the canonical city name
        else:
                    # Check if it directly matches any of our known city names
                    for c in known_cities:     # Loop through our list of cities we care about
                        if name == c.lower():  # If AI entity matches a known city (case-insensitive)
                            found.add(c)       # Add this city to our results
    except Exception:                          # If NLP processing fails for any reason
        pass                                   # Just continue with what we found from synonym matching
    
    # Return the cities we found, sorted alphabetically for consistency
    return sorted(found)                       # Convert set to sorted list

def extract_candidate_keywords(text: str, nlp) -> List[str]:
    """
    Extract important phrases and keywords from text using AI
    
    Args:
        text: The text to analyze for keywords
        nlp: The spaCy language model for AI processing
    
    Returns:
        List of important phrases found in the text
    """
    doc = nlp(text)                            # Process the text with spaCy AI model
    candidates = set()                         # Use a set to automatically avoid duplicate phrases
    
    # spaCy identifies "noun chunks" - meaningful phrases like "the housing crisis" or "public transportation"
    for chunk in doc.noun_chunks:              # Loop through each noun phrase identified by AI
        cleaned = chunk.text.strip().lower()  # Clean up the phrase (remove whitespace, make lowercase)
        if len(cleaned.split()) > 0:           # Make sure the phrase isn't empty after cleaning
            candidates.add(cleaned)            # Add this phrase to our set of keywords
    
    return list(candidates)                    # Convert set back to list and return

def top_keyword_counts(entries: List[Entry], nlp, limit: int) -> List[Tuple[str, int]]:
    """
    Find the most frequently mentioned keywords across all our collected data
    
    Args:
        entries: All the articles/posts/comments we collected
        nlp: The spaCy language model for keyword extraction
        limit: How many top keywords to return
    
    Returns:
        List of (keyword, count) tuples, sorted by frequency (most common first)
    """
    counter = Counter()                        # Counter object keeps track of how many times we see each keyword
    
    # Go through every piece of content we collected
    for e in entries:                          # Loop through each Entry (article/post/comment)
        # Combine title and text, but truncate to save processing time
        text = truncate_words(e.title + " " + e.text, 120)  # Merge title and text, limit to 120 words
        
        # Extract keywords from this text using AI
        for kw in extract_candidate_keywords(text, nlp):  # Get keywords from this piece of content
            counter[kw] += 1                   # Increment the count for this keyword
    
    # Return the most common keywords with their counts
    return counter.most_common(limit)          # Get the top 'limit' most frequent keywords

# =========================
# OPENAI INTEGRATION FUNCTIONS
# =========================

def try_get_openai_client():
    """
    Try to create an OpenAI client if we have an API key available
    
    Returns:
        OpenAI client object if successful, or None if not available
    """
    # Check if we have an API key set in environment variables
    if not OPENAI_API_KEY:                     # If no API key is available
        return None                            # Return None to indicate OpenAI is not available
    
    try:
        # Try to import and create the OpenAI client
        from openai import OpenAI              # Import OpenAI library (might fail if not installed)
        return OpenAI(api_key=OPENAI_API_KEY)  # Create and return OpenAI client with our API key
    except Exception:                          # If import fails or client creation fails
        return None                            # Return None to indicate OpenAI is not available

def openai_top_topics(keyword_counts: List[Tuple[str, int]],
                      sample_titles: List[str]) -> List[Dict[str, Any]]:
    """
    Use OpenAI to identify the top 20 civic issues from our collected data
    
    Args:
        keyword_counts: List of (keyword, frequency) pairs from our data
        sample_titles: Sample of article titles to provide context
    
    Returns:
        List of topic dictionaries with names, descriptions, and civic signals
    """
    client = try_get_openai_client()           # Try to get an OpenAI client
    if client is None:                         # If we don't have OpenAI available
        return []                              # Return empty list (caller will use fallback method)
    
    # Create a detailed prompt for OpenAI explaining what we want
    prompt = {
        "role": "user",                        # We are the user asking OpenAI to do something
        "content": (                           # The actual request we're making
            "You are analyzing a global corpus of news and social posts about cities. "  # Explain the context
            "Given a list of keyword phrases with counts and a small sample of titles, "  # Explain the input data
            "derive the 20 most prevalent topics (high-level issues), suitable for a civic dashboard.\n\n"  # Explain what we want
            "Return strict JSON with key 'topics': an array of 20 items. Each item has:\n"  # Specify output format
            "  - name (short, human-readable)\n"                                           # Topic name
            "  - description (1-2 sentences)\n"                                            # Topic description
            "  - signals (array subset of: affordability, services, safety, opportunity, culture, environment, "  # Civic dimensions
            "transportation, governance, housing, economy, education, health)\n"           # More civic dimensions
            "  - representative_phrases (3-6 items from the phrases list)\n\n"             # Example phrases
            f"Keyword phrases (phrase :: count):\n" +                                      # Start of data section
            "\n".join([f"- {p} :: {c}" for p, c in keyword_counts]) +                     # Format keyword data
            "\n\nSample titles:\n" +                                                       # Start of titles section
            "\n".join([f"- {t}" for t in sample_titles])                                   # Format sample titles
        )
    }
    
    try:
        # Send the request to OpenAI's API
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,                # Use the AI model specified in our config
            messages=[{"role": "system", "content": "Return only valid JSON."}, prompt],  # System message + our prompt
            temperature=0.2,                   # Low temperature for more consistent/focused results
            response_format={"type": "json_object"},  # Force OpenAI to return valid JSON
        )
        
        # Extract the response content from OpenAI
        content = resp.choices[0].message.content  # Get the AI's response text
        
        # Parse the JSON response into Python data
        data = json.loads(content)             # Convert JSON string to Python dictionary
        
        # Return the topics array from the response
        return data.get("topics", [])          # Get the 'topics' key, or empty list if missing
        
    except Exception:                          # If anything goes wrong (API error, JSON parsing, etc.)
        return []                              # Return empty list (caller will use fallback method)

def openai_score_city(city: str, snippets: List[str]) -> Dict[str, Any]:
    """
    Use OpenAI to analyze and score a city's civic health across multiple dimensions
    
    Args:
        city: Name of the city to analyze
        snippets: Short text excerpts about this city from news/social media
    
    Returns:
        Dictionary containing health scores, rationales, and top issues for the city
    """
    client = try_get_openai_client()           # Try to get an OpenAI client
    
    # If we don't have OpenAI available, return default neutral scores
    if client is None:                         # If no OpenAI client available
        return {                               # Return a default scoring structure
            "overall_health": 50,              # Default overall score of 50/100
            "category_scores": {k: {"score": 50, "rationale": "insufficient data"} for k in CIVIC_DIMENSIONS},  # 50/100 for each dimension
            "top_issues": [],                  # Empty issues list
        }
    
    # Combine the text snippets (but limit to save on API costs)
    bundle = "\n\n".join(snippets[:CITY_DOCS_PER_MODEL_CALL])  # Join snippets with double newlines, limit quantity
    
    # Create a detailed prompt asking OpenAI to analyze this specific city
    prompt = {
        "role": "user",                        # We are the user making a request
        "content": (                           # The detailed analysis request
            f"You are scoring civic health for the city: {city}.\n"  # Specify which city to analyze
            "Given the following short snippets from recent news and social discussions, "  # Explain the input
            "produce a structured assessment.\n\n"                                          # Ask for structured output
            "Return strict JSON with:\n"                                                    # Specify output format
            "  - overall_health (integer 0-100)\n"                                          # Overall score
            "  - category_scores: object with keys affordability, services, safety, opportunity, culture, "  # Category scores
            "environment, transportation, governance, housing, economy, education, health; each value is "   # More categories
            "an object { score: integer 0-100, rationale: concise, specific rationale citing signals and tradeoffs }\n"  # Score format
            "  - top_issues: array of 10 items { name: string, why_it_matters: string }\n"                 # Issues format
            "Guidance: higher score means better civic health signal net of sentiment. "                   # Scoring guidance
            "Weigh recency (implied), quality/reputation, length, diversity across sources (news vs social).\n"  # More guidance
            "Favor specificity: name policies, programs, metrics when evident; avoid generic text.\n\n"     # Specificity
            "Snippets:\n" + bundle                                                                          # The actual data to analyze
        )
    }
    
    try:
        # Send the request to OpenAI's API
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,                # Use the AI model specified in our config
            messages=[{"role": "system", "content": "Return only valid JSON."}, prompt],  # System instruction + our prompt
            temperature=0.2,                   # Low temperature for consistent, focused results
            response_format={"type": "json_object"},  # Force OpenAI to return valid JSON format
        )
        
        # Parse and return the response from OpenAI
        content = resp.choices[0].message.content  # Extract the AI's response text
        return json.loads(content)             # Parse JSON and return as Python dictionary
        
    except Exception:                          # If anything goes wrong (API error, JSON parsing, network, etc.)
        # Return default neutral scores as fallback
        return {
            "overall_health": 50,              # Default overall score
            "category_scores": {k: {"score": 50, "rationale": "insufficient data"} for k in CIVIC_DIMENSIONS},  # Default category scores
            "top_issues": [],                  # Empty issues list
        }

# =========================
# OUTPUT FORMATTING FUNCTIONS
# =========================

def print_header(title: str):
    """
    Print a nicely formatted header with the given title
    
    Args:
        title: The text to display in the header
    """
    print("\n" + "=" * 80)                    # Print a blank line followed by 80 equals signs
    print(title)                               # Print the title text
    print("=" * 80)                           # Print another line of 80 equals signs

def print_topics(topics: List[Dict[str, Any]]):
    """
    Print the list of top topics in a nicely formatted way
    
    Args:
        topics: List of topic dictionaries from OpenAI analysis
    """
    # Go through the first 20 topics (or fewer if we don't have 20)
    for i, t in enumerate(topics[:20], 1):     # Loop with index starting at 1, limit to 20 topics
        name = t.get("name", "")               # Get the topic name (empty string if missing)
        desc = t.get("description", "")        # Get the topic description (empty string if missing)
        signals = ", ".join(t.get("signals", []))  # Join the civic signals with commas (empty if missing)
        reps = ", ".join(t.get("representative_phrases", [])[:6])  # Get up to 6 example phrases, join with commas
        
        # Print the topic information in a formatted way
        print(f"{i}. {name}")                  # Print topic number and name
        if desc:                               # If we have a description
            print(f"   - {desc}")              # Print the description with indentation
        if signals:                            # If we have civic signals
            print(f"   - Signals: {signals}")  # Print the signals with indentation
        if reps:                               # If we have representative phrases
            print(f"   - Phrases: {reps}")     # Print the phrases with indentation

def print_city_score(city: str, score: Dict[str, Any]):
    """
    Print a city's health score and analysis in a nicely formatted way
    
    Args:
        city: Name of the city being analyzed
        score: Dictionary containing the city's scores and analysis from OpenAI
    """
    # Get the overall health score for this city
    overall = score.get("overall_health", "NA")  # Get overall score, use "NA" if missing
    print(f"\n{city}: Health Score = {overall}/100")  # Print city name and overall score
    
    # Get the detailed category scores
    cats = score.get("category_scores", {})    # Get the category scores dictionary
    
    # Print each civic dimension score in a formatted table
    for k in CIVIC_DIMENSIONS:                 # Loop through each civic dimension we track
        if k in cats:                          # If we have data for this dimension
            v = cats[k]                        # Get the score and rationale for this dimension
            # Print formatted line: "Dimension Name    Score/100  | Rationale"
            print(f"  - {k.title():<15} {v.get('score','NA'):>3}/100  | {truncate_words(v.get('rationale',''), 22)}")
    
    # Print the top issues identified for this city
    issues = score.get("top_issues", [])       # Get the list of top issues
    if issues:                                 # If we have issues to display
        print("  Top Issues:")                 # Print section header
        # Print each issue with a number
        for j, it in enumerate(issues[:10], 1):  # Loop through up to 10 issues, numbered starting at 1
            # Print issue number, name, and why it matters (truncated)
            print(f"    {j}. {it.get('name','')} — {truncate_words(it.get('why_it_matters',''), 28)}")

# =========================
# MAIN PROGRAM EXECUTION
# =========================

def main():
    """
    The main function that runs our entire civic health analysis pipeline
    This orchestrates all the steps from data collection to final analysis
    """
    # -----------------------
    # Parse CLI flags
    # -----------------------
    parser = argparse.ArgumentParser()                                 # Create an argument parser for command-line flags
    parser.add_argument("--cities_link", type=str, required=False,    # URL to a table of top cities (e.g., Wikipedia)
                        help="URL to a table listing the top cities by population (e.g., Wikipedia list)")
    parser.add_argument("--num_cities", type=int, default=100)        # How many cities to analyze (default now 100)
    parser.add_argument("--per_source_limit", type=int, default=500)  # How many articles per global source to fetch
    parser.add_argument("--reddit_pages", type=int, default=10)       # How many subreddit pages per city to fetch
    parser.add_argument("--reddit_comments", type=int, default=100)   # How many comments per post to fetch
    parser.add_argument("--city_docs", type=int, default=500,         # Fairness normalization: documents per city for AI
                        help="Documents per city fed into AI scoring (fairness normalization)")
    parser.add_argument("--out", type=str, default="data/latest",    # Where to write outputs (JSON/TXT)
                        help="Output directory for results")
    args = parser.parse_args()                                         # Parse the CLI arguments

    # -----------------------
    # Apply CLI config to globals
    # -----------------------
    global PER_SOURCE_ARTICLE_LIMIT, REDDIT_MAX_PAGES, REDDIT_COMMENTS_PER_POST_LIMIT, CITY_DOCS_PER_MODEL_CALL
    PER_SOURCE_ARTICLE_LIMIT = args.per_source_limit                    # Override per-source article cap
    REDDIT_MAX_PAGES = args.reddit_pages                               # Override subreddit pages to fetch
    REDDIT_COMMENTS_PER_POST_LIMIT = args.reddit_comments               # Override comments per post limit
    CITY_DOCS_PER_MODEL_CALL = args.city_docs                           # Override per-city AI document cap

    # Step 1: Load the AI language model for text processing
    nlp = spacy.load("en_core_web_md")                                 # Load spaCy's medium English model with word vectors
    
    # Step 2: Build dynamic city list, subreddits, and news sources (if cities_link provided)
    if args.cities_link:                                                # If a cities list URL was provided
        print("\n================================================================================")
        print("Loading cities")                                         # Announce city loading
        print("================================================================================")
        top_cities = load_top_cities_from_table(args.cities_link, max_cities=args.num_cities)  # Load top-N cities
        print(f"Loaded {len(top_cities)} cities")                        # Show how many cities we got

        print("\nDiscovering subreddits")                              # Announce subreddit discovery
        dynamic_city_subs = build_city_subreddits(top_cities)            # Attempt to map city -> subreddit
        print(f"Subreddits found: {len(dynamic_city_subs)} / {len(top_cities)}")  # Summary of findings

        print("\nDiscovering per-city news sources")                   # Announce city news discovery
        city_sources_map = build_city_sources_map(top_cities, per_city_min=30)  # Find >=30 local media for each city

        print("\nBuilding global news source pool")                    # Announce global pool building
        dynamic_sources = build_global_sources(city_sources_map, global_min=150)  # Build global pool >= 150
        print(f"Global news sources total (unique): {len(dynamic_sources)}")    # Show how many unique sources
        city_country_map: Dict[str, Optional[str]] = {c: country for c, country in top_cities}
    else:
        dynamic_sources = NEWS_SOURCES                                   # Fall back to static global sources
        dynamic_city_subs = CITY_SUBREDDITS                              # Fall back to static subreddit map
        city_country_map: Dict[str, Optional[str]] = {}

    # Step 3: Collect data from international/global news sources
    print_header("Collecting Data")                                      # Print a nice header for this section
    news_entries = scrape_all_news(dynamic_sources, PER_SOURCE_ARTICLE_LIMIT)  # Scrape all chosen news sites
    
    # Step 4: Collect data from Reddit city communities (dynamic or static map)
    reddit_entries = scrape_reddit_for_cities(dynamic_city_subs, REDDIT_MAX_PAGES, REDDIT_COMMENTS_PER_POST_LIMIT)  # Scrape Reddit
    
    # Step 4: Combine all our collected data into one master list
    all_entries: List[Entry] = news_entries + reddit_entries  # Merge news articles with Reddit posts/comments
    
    # Print summary statistics of what we collected
    print(f"\nTotals -> News articles: {len(news_entries)} | Reddit items (posts+comments): {len(reddit_entries)} | Overall: {len(all_entries)}")

    # Step 5: Detect which cities are mentioned in news articles
    print_header("Detecting Cities in News Items")  # Print header for this analysis phase
    known_cities: Set[str] = set(dynamic_city_subs.keys())  # Get set of all cities we care about (dynamic)
    
    # For each news article, figure out which cities it mentions using AI
    for e in all_entries:                      # Loop through every piece of content
        if e.source == "News":                 # Only analyze news articles (Reddit is already tagged by subreddit)
            e.cities = detect_cities_in_text(e.text, e.title, nlp, known_cities)  # Use AI to detect cities

    # Heuristic enrichment: tag news by local media domains so ALL relevant local articles are included
    if 'city_sources_map' in locals() and city_sources_map:
        from urllib.parse import urlparse
        def _host_only(u: str) -> str:
            try:
                h = urlparse(u).netloc.lower()
                return h[4:] if h.startswith('www.') else h
            except Exception:
                return ''
        city_hosts: Dict[str, Set[str]] = {}
        for city, domains in city_sources_map.items():
            city_hosts[city] = set(_host_only(d) for d in (domains or []))
        for e in all_entries:
            if e.source != "News":
                continue
            h = _host_only(e.url)
            if not h:
                continue
            for city, hosts in city_hosts.items():
                if h in hosts or any(h.endswith('.'+root) for root in hosts):
                    if city not in (e.cities or []):
                        e.cities.append(city)
    
    # Create a mapping from cities to all content about that city
    city_to_entries: Dict[str, List[Entry]] = defaultdict(list)  # Dictionary that creates empty lists automatically
    for e in all_entries:                      # Loop through all content
        if e.cities:                           # If this content mentions any cities
            for c in e.cities:                 # For each city mentioned in this content
                city_to_entries[c].append(e)   # Add this content to that city's list

    # Step 6: Show a sample of the sources we collected (for transparency)
    print_header("All Collected Sources (sample)")  # Print header for sources section
    
    # Group all content by source website for display
    by_site: Dict[str, List[Entry]] = defaultdict(list)  # Dictionary to group content by source
    for e in all_entries:                      # Loop through all content
        by_site[e.source_site].append(e)      # Group by the source website
    
    # Show the top 20 sources by volume (most content first)
    for site, arr in sorted(by_site.items(), key=lambda x: -len(x[1]))[:20]:  # Sort by content count, take top 20
        print(f"\nSite: {site}  ({len(arr)} items)")  # Print source name and item count
        # Show first 5 items from each source as examples
        for x in arr[:5]:                      # Loop through first 5 items from this source
            print(f" - {truncate_words(x.title, 18)}")  # Print truncated title
            print(f"   URL: {x.url}")          # Print the full URL

    # Step 7: Use AI to identify the most important global civic topics
    print_header("Deriving Global Top 20 Topics (OpenAI)")  # Print header for topics section
    
    # Get the most frequent keywords from all our collected data
    keyword_counts_list = top_keyword_counts(all_entries, nlp, KEYWORD_PHRASE_LIMIT_FOR_TOPICS)  # Extract top keywords
    
    # Get a random sample of article titles to provide context to AI
    sample_titles = [e.title for e in random.sample(all_entries, min(GLOBAL_SAMPLE_TITLES_FOR_TOPICS, len(all_entries)))]  # Random sample
    
    # Ask OpenAI to identify the top civic topics from our data
    topics = openai_top_topics(keyword_counts_list, sample_titles)  # Use AI to analyze topics
    
    # If OpenAI didn't work, use a backup machine learning method
    if not topics:                             # If we got no topics from OpenAI
        print("OpenAI topic extraction unavailable; falling back to local clustering.")  # Inform user about fallback
        
        # Use local machine learning to group similar keywords into topics
        keywords = [p for p, _ in keyword_counts_list]  # Extract just the keywords (ignore counts)
        
        # Convert keywords to numerical vectors using spaCy's word embeddings
        embeddings = np.array([nlp(k).vector for k in keywords])  # Convert each keyword to a number array
        
        # Filter out keywords that don't have good vector representations
        valid_idx = [i for i, vec in enumerate(embeddings) if np.linalg.norm(vec) != 0]  # Find non-zero vectors
        
        if valid_idx:                          # If we have valid keyword vectors
            emb = embeddings[valid_idx]        # Get only the valid embeddings
            kw_valid = [keywords[i] for i in valid_idx]  # Get only the valid keywords
            
            # Use clustering algorithm to group similar keywords into 20 topics
            clustering = AgglomerativeClustering(n_clusters=20, linkage="average", metric="cosine")  # Create clustering algorithm
            labels = clustering.fit_predict(emb)  # Run clustering on our keyword vectors
            
            # Group keywords by their cluster assignments
            clusters = defaultdict(list)       # Dictionary to group keywords by cluster
            for lab, kw in zip(labels, kw_valid):  # Loop through cluster labels and keywords together
                clusters[lab].append(kw)       # Add each keyword to its assigned cluster
            
            # Create topic objects from our clusters
            topics = [{"name": f"Cluster {k}", "description": "Similar phrases", "signals": [], "representative_phrases": v[:6]} for k, v in clusters.items()]
    
    # Display the topics we found (either from OpenAI or clustering)
    print_topics(topics)                       # Print all topics in formatted way

    # Step 8: Analyze each city's civic health using AI
    print_header("Per-City Health Scores (OpenAI)")  # Print header for city analysis section
    city_scores: Dict[str, Dict[str, Any]] = {}  # Dictionary to store scores for each city
    total_cities_to_analyze = len(city_to_entries)  # Get total number of cities for progress tracking
    
    # Go through each city, starting with those that have the most content
    for city_index, (city, items) in enumerate(sorted(city_to_entries.items(), key=lambda x: -len(x[1]))):  # Sort cities by content volume with index
        # Show progress bar for city analysis
        print_progress_bar(city_index, total_cities_to_analyze, f"Analyzing cities")  # Show progress
        print(f"\nAnalyzing {city} ({len(items)} sources)...")  # Show which city we're analyzing
        
        # Prepare text snippets for AI analysis
        snippets: List[str] = []               # List to store formatted text snippets
        
        # Fairness-normalized sampling with quality, relevance, and diversity
        sample_items = []
        by_type: Dict[str, List[Entry]] = defaultdict(list)
        for e in items:
            by_type[e.source].append(e)
        buckets = list(by_type.keys())
        if buckets:
            per_bucket = max(1, CITY_DOCS_PER_MODEL_CALL // max(1, len(buckets)))
            # Phase 1: within-bucket smart selection (fair across source types)
            for b in buckets:
                sample_items.extend(smart_select_for_city(city, by_type[b], per_bucket, nlp))
            # Phase 2: top up to city target with remaining best items across all
            remaining = CITY_DOCS_PER_MODEL_CALL - len(sample_items)
            if remaining > 0:
                remaining_pool = [e for e in items if e not in sample_items]
                sample_items.extend(smart_select_for_city(city, remaining_pool, remaining, nlp))
            # Final trim to cap
            if len(sample_items) > CITY_DOCS_PER_MODEL_CALL:
                sample_items = sample_items[:CITY_DOCS_PER_MODEL_CALL]
        else:
            sample_items = []
        
        # Create a formatted snippet for each piece of content
        for e in sample_items:                 # Loop through sampled content
            # Format: "Title: ... Text: ... Source: ..."
            snip = f"Title: {truncate_words(e.title, 20)}\nText: {truncate_words(e.text, 60)}\nSource: {e.source} [{e.source_site}] {e.url}"
            snippets.append(snip)              # Add formatted snippet to our list
        
        # Ask OpenAI to score this city's civic health
        score = openai_score_city(city, snippets)  # Use AI to analyze and score this city
        city_scores[city] = score              # Store the results for this city
        
        # Display the results for this city
        print_city_score(city, score)          # Print formatted city analysis
        
        # Show all the sources we used for this city's analysis (for transparency)
        print("  Citations:")                  # Print citations header
        urls = unique_preserve_order([e.url for e in items])  # Get unique URLs, preserving order
        for u in urls[:40]:                    # Show up to 40 URLs (to avoid overwhelming output)
            print(f"    - {u}")                # Print each URL with indentation
        if len(urls) > 40:                     # If there are more than 40 URLs
            print(f"    (+ {len(urls) - 40} more)")  # Show how many additional sources we have

    # Final progress update for city analysis
    print_progress_bar(total_cities_to_analyze, total_cities_to_analyze, f"Analyzing cities")  # Show 100% completion
    print(f"\nCompleted city analysis: {len(city_scores)} cities scored")  # Show final count

    # Step 9: Print final summary statistics
    print_header("Basic Stats")                # Print header for final statistics section
    
    # Count different types of content we collected
    news_count = len([e for e in all_entries if e.source == "News"])          # Count news articles
    reddit_posts = len([e for e in all_entries if e.source == "RedditPost"])  # Count Reddit posts
    reddit_comments = len([e for e in all_entries if e.source == "RedditComment"])  # Count Reddit comments
    
    # Display the final summary statistics
    print(f"News Articles: {news_count}")      # Print total number of news articles
    print(f"Reddit Posts: {reddit_posts}")    # Print total number of Reddit posts
    print(f"Reddit Comments: {reddit_comments}")  # Print total number of Reddit comments
    print(f"Cities covered: {len(city_to_entries)}")  # Print total number of cities analyzed
    
    # Print quick summary of top cities by health score
    print("\n" + "=" * 60)
    print("🏆 TOP PERFORMING CITIES BY HEALTH SCORE")
    print("=" * 60)
    
    # Sort cities by their health scores (highest first)
    sorted_cities = sorted(city_scores.items(), key=lambda x: x[1].get('overall_health', 0), reverse=True)
    
    # Show top 10 cities
    for i, (city, score) in enumerate(sorted_cities[:10], 1):
        health_score = score.get('overall_health', 'N/A')
        print(f"{i:2d}. {city:<20} {health_score}/100")
    
    # Build ranked global top issues from per-city outputs (frequency across cities)
    issue_to_info: Dict[str, Dict[str, Any]] = {}
    for c_name, sc in city_scores.items():
        for it in (sc.get("top_issues") or []):
            iname = (it.get("name") or it.get("issue") or "").strip()
            if not iname:
                continue
            entry = issue_to_info.setdefault(iname, {"count": 0, "why": it.get("why_it_matters") or it.get("description") or "", "cities": defaultdict(int)})
            entry["count"] += 1
            entry["cities"][c_name] += 1
    topics_ranked: List[Dict[str, Any]] = []
    for iname, info in issue_to_info.items():
        top_cities = sorted(info["cities"].items(), key=lambda x: (-x[1], x[0].lower()))[:8]
        top_city_names = [n for n, _ in top_cities]
        desc = info["why"] or f"Prominent across {info['count']} cities."
        if top_city_names:
            desc = (desc + " Top cities: " + ", ".join(top_city_names))[:480]
        topics_ranked.append({
            "name": iname,
            "description": desc,
            "signals": [],
            "cities": top_city_names,
            "count": info["count"],
        })
    topics_ranked.sort(key=lambda x: (-x.get("count", 0), x["name"].lower()))

    # Step 10: Persist full structured results (JSON + TXT) for the dashboard
    out_dir = args.out if 'args' in locals() else 'data/latest'
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        pass

    # Also build city boundary GeoJSON for the map (best-effort)
    try:
        if args.cities_link:
            print("\nBuilding city boundaries (GeoJSON) for map...")
            boundaries_path = os.path.join(out_dir, "city_boundaries.geojson")
            built = build_city_boundaries_geojson(top_cities, boundaries_path)
            print(f"City boundaries saved -> {boundaries_path} ({built} features)")
    except Exception as e:
        print(f"City boundaries build skipped: {e}")

    # Build comprehensive JSON with full citations and Reddit post links
    def entry_urls(lst, type_filter=None):
        if type_filter is None:
            return unique_preserve_order([e.url for e in lst])
        return unique_preserve_order([e.url for e in lst if e.source == type_filter])

    # Use ranked topics from per-city issues (more robust/transparent). If empty, fallback to earlier topics.
    try:
        global_topics = topics_ranked if topics_ranked else topics
    except Exception:
        global_topics = topics_ranked

    run_timestamp = datetime.now(timezone.utc).isoformat()
    results = {
        "summary": {
            "news_articles": news_count,
            "reddit_posts": reddit_posts,
            "reddit_comments": reddit_comments,
            "cities_covered": len(city_to_entries),
            "run_timestamp": run_timestamp,
        },
        "topics": global_topics,
        "cities": []
    }

    for city, score in sorted(city_scores.items(), key=lambda x: x[0].lower()):
        items = city_to_entries.get(city, [])
        # Map category_scores -> dimensions schema used by dashboard
        dims = {}
        for k, v in (score.get("category_scores") or {}).items():
            dims[k.replace('_', ' ').title()] = {
                "score": v.get("score"),
                "note": v.get("rationale")
            }
        # Top issues list
        issues = []
        for it in (score.get("top_issues") or [])[:20]:
            name = it.get("name") or it.get("issue") or ""
            why = it.get("why_it_matters") or it.get("description") or ""
            issues.append(f"{name} — {why}".strip(" —"))

        results["cities"].append({
            "name": city,
            "health_score": score.get("overall_health"),
            "dimensions": dims,
            "top_issues": issues,
            # Full transparency: include all links used in analysis
            "citations": entry_urls(items),
            "articles": entry_urls(items, "News"),
            "reddit_posts": entry_urls(items, "RedditPost"),
        })

    # If Reddit was skipped (e.g., --reddit_pages 0), reuse previous run's reddit_posts per city
    try:
        if REDDIT_MAX_PAGES == 0:
            prev_path = os.path.join(out_dir, "full_results.json")
            if os.path.exists(prev_path):
                with open(prev_path, "r", encoding="utf-8") as pf:
                    prev = json.load(pf)
                prev_map = {c.get("name"): c for c in (prev.get("cities") or [])}
                prev_summary = prev.get("summary") or {}
                for city in results.get("cities", []):
                    name = city.get("name")
                    prev_city = prev_map.get(name)
                    if not prev_city:
                        continue
                    prev_reddit = prev_city.get("reddit_posts") or []
                    if prev_reddit:
                        # If current run has no reddit posts, adopt previous
                        if not city.get("reddit_posts"):
                            city["reddit_posts"] = prev_reddit
                        # Ensure citations include these reddit links for transparency
                        existing = set(city.get("citations") or [])
                        if city.get("citations") is None:
                            city["citations"] = []
                        for u in prev_reddit:
                            if u not in existing:
                                city["citations"].append(u)
                # Update summary counts for reddit if we skipped fetching
                # Posts: count unique across all city reddit_posts
                all_posts: Set[str] = set()
                for c in results.get("cities", []):
                    for u in (c.get("reddit_posts") or []):
                        all_posts.add(u)
                if all_posts:
                    results["summary"]["reddit_posts"] = len(all_posts)
                # Comments: reuse previous summary if available
                prev_comments = prev_summary.get("reddit_comments")
                if isinstance(prev_comments, int) and prev_comments > 0:
                    results["summary"]["reddit_comments"] = prev_comments
    except Exception:
        pass

    # Write JSON
    out_json = os.path.join(out_dir, "full_results.json")
    try:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Saved results JSON -> {out_json}")
    except Exception as e:
        print(f"Failed to save results JSON: {e}")

    # Update cumulative distinct metrics in cache and attach them into results["summary"]
    try:
        cache = _init_cache(os.path.join("data", "visited.sqlite"))
        with CACHE_LOCK:
            # Distinct news articles across all runs = rows in visited
            cur = cache.execute("SELECT COUNT(*) FROM visited")
            total_articles_distinct = (cur.fetchone() or [0])[0] or 0
            cache.execute("UPDATE metrics SET v=? WHERE k='articles_distinct'", (total_articles_distinct,))

            # Distinct reddit posts across all runs = union of per-city reddit_posts
            posts_set = set()
            for c in results.get("cities", []):
                for u in (c.get("reddit_posts") or []):
                    posts_set.add(u)
            total_posts_distinct = len(posts_set)
            cache.execute("UPDATE metrics SET v=? WHERE k='reddit_posts_distinct'", (total_posts_distinct,))

            # Cumulative comments total (monotonic): add this run's comments to stored total
            cur = cache.execute("SELECT v FROM metrics WHERE k='reddit_comments_total'")
            row = cur.fetchone()
            prev_total = (row[0] if row else 0) or 0
            this_run = int(results.get("summary",{}).get("reddit_comments") or 0)
            cache.execute("UPDATE metrics SET v=? WHERE k='reddit_comments_total'", (prev_total + this_run,))
            cache.commit()

            # Attach cumulative metrics to summary
            results["summary"]["cumulative"] = {
                "news_articles_distinct": int(total_articles_distinct),
                "reddit_posts_distinct": int(total_posts_distinct),
                "reddit_comments_total": int(prev_total + this_run)
            }
    except Exception:
        pass

    # Write a compact text summary
    out_txt = os.path.join(out_dir, "full_analysis.txt")
    try:
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write("Our City Health — Analysis Summary\n\n")
            f.write(f"News Articles: {news_count}\n")
            f.write(f"Reddit Posts: {reddit_posts}\n")
            f.write(f"Reddit Comments: {reddit_comments}\n")
            f.write(f"Cities covered: {len(city_to_entries)}\n\n")
            for city, score in sorted(city_scores.items(), key=lambda x: x[0].lower()):
                f.write(f"{city}: {score.get('overall_health')}/100\n")
            f.write("\n")
        print(f"Saved analysis TXT -> {out_txt}")
    except Exception as e:
        print(f"Failed to save analysis TXT: {e}")

    print("\n🎉 ANALYSIS COMPLETE! Open the dashboard and point it to data/latest/full_results.json for full results.")

# This is the standard Python pattern for running the main function when script is executed directly
if __name__ == "__main__":                    # This condition is True when script is run directly (not imported)
    main()                                     # Execute our main function to start the entire pipeline
