from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict
from datetime import datetime, timezone

from backend.app.models import Entry

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

def _norm_domain(host: str) -> str:
    host = (host or "").lower().strip()
    if host.startswith("r/"):
        return "reddit"
    host = host.replace("https://", "").replace("http://", "")
    host = host.split("/")[0]
    if host.startswith("www."):
        host = host[4:]
    return host

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
        # Use timezone-aware now if dt is timezone-aware
        now = datetime.now(timezone.utc)
        delta = now - dt if dt.tzinfo else datetime.utcnow() - dt
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
    # Be fairly aggressive to get variety
    max_per_domain = max(3, target_n // max(8, approx_domains))

    picked: List[Entry] = []
    used_titles: Set[str] = set()
    per_domain: Dict[str, int] = defaultdict(int)

    def _title_key(e: Entry) -> str:
        t = (e.title or "").lower()
        return " ".join([w for w in t.replace("-", " ").split()[:12]])

    # Pass 1: pick best scores respecting diversity limits
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

    # Pass 2: fill up remaining slots with next best scores
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
