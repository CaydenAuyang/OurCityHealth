import json
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from collections import Counter
import spacy

from backend.app.core.config import settings
from backend.app.models import Entry, Topic, DimensionScore, Issue
from backend.app.scrape.utils import truncate_words
from backend.app.score.selection import DIMENSION_SYNONYMS

CIVIC_DIMENSIONS = list(DIMENSION_SYNONYMS.keys())
CITY_DOCS_PER_MODEL_CALL = 200 # Default cap

def get_openai_client() -> Optional[OpenAI]:
    if not settings.OPENAI_API_KEY:
        return None
    try:
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception:
        return None

def extract_candidate_keywords(text: str, nlp) -> List[str]:
    doc = nlp(text)
    candidates = set()
    for chunk in doc.noun_chunks:
        cleaned = chunk.text.strip().lower()
        if len(cleaned.split()) > 0:
            candidates.add(cleaned)
    return list(candidates)

def top_keyword_counts(entries: List[Entry], nlp, limit: int) -> List[Tuple[str, int]]:
    counter = Counter()
    for e in entries:
        text = truncate_words(e.title + " " + e.text, 120)
        for kw in extract_candidate_keywords(text, nlp):
            counter[kw] += 1
    return counter.most_common(limit)

def openai_top_topics(keyword_counts: List[Tuple[str, int]], sample_titles: List[str]) -> List[Topic]:
    client = get_openai_client()
    if not client:
        return []
        
    prompt = {
        "role": "user",
        "content": (
            "You are analyzing a global corpus of news and social posts about cities. "
            "Given a list of keyword phrases with counts and a small sample of titles, "
            "derive the 20 most prevalent topics (high-level issues), suitable for a civic dashboard.\n\n"
            "Return strict JSON with key 'topics': an array of 20 items. Each item has:\n"
            "  - name (short, human-readable)\n"
            "  - description (1-2 sentences)\n"
            "  - signals (array subset of: affordability, services, safety, opportunity, culture, "
            "environment, transportation, governance, housing, economy, education, health)\n"
            "  - representative_phrases (3-6 items from the phrases list)\n\n"
            f"Keyword phrases (phrase :: count):\n" +
            "\n".join([f"- {p} :: {c}" for p, c in keyword_counts]) +
            "\n\nSample titles:\n" +
            "\n".join([f"- {t}" for t in sample_titles])
        )
    }
    
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Return only valid JSON."}, prompt],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        topics = []
        for t in data.get("topics", []):
            topics.append(Topic(
                name=t.get("name", ""),
                description=t.get("description", ""),
                signals=t.get("signals", []),
                representative_phrases=t.get("representative_phrases", [])
            ))
        return topics
    except Exception:
        return []

def openai_score_city(city: str, snippets: List[str]) -> Dict[str, Any]:
    """
    Returns raw dict matching the v3 output structure.
    """
    client = get_openai_client()
    if not client:
        return {
            "overall_health": 50,
            "category_scores": {k: {"score": 50, "rationale": "insufficient data"} for k in CIVIC_DIMENSIONS},
            "top_issues": [],
        }
        
    bundle = "\n\n".join(snippets[:CITY_DOCS_PER_MODEL_CALL])
    
    prompt = {
        "role": "user",
        "content": (
            f"You are scoring civic health for the city: {city}.\n"
            "Given the following short snippets from recent news and social discussions, "
            "produce a structured assessment.\n\n"
            "Return strict JSON with:\n"
            "  - overall_health (integer 0-100)\n"
            "  - category_scores: object with keys affordability, services, safety, opportunity, culture, "
            "environment, transportation, governance, housing, economy, education, health; each value is "
            "an object { score: integer 0-100, rationale: concise, specific rationale citing signals and tradeoffs }\n"
            "  - top_issues: array of 10 items { name: string, why_it_matters: string }\n"
            "Guidance: higher score means better civic health signal net of sentiment. "
            "Weigh recency (implied), quality/reputation, length, diversity across sources (news vs social).\n"
            "Favor specificity: name policies, programs, metrics when evident; avoid generic text.\n\n"
            "Snippets:\n" + bundle
        )
    }
    
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Return only valid JSON."}, prompt],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception:
        return {
            "overall_health": 50,
            "category_scores": {k: {"score": 50, "rationale": "API error"} for k in CIVIC_DIMENSIONS},
            "top_issues": [],
        }
