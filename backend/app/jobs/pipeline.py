import os
import json
import time
import spacy
from typing import List, Dict, Any, Set
from collections import defaultdict

from backend.app.models import JobRequest, Entry, CityResult, DimensionScore, Issue
from backend.app.jobs.db import update_job, get_job_request
from backend.app.core.constants import CITY_SUBREDDITS
from backend.app.scrape.news import scrape_news_site
from backend.app.scrape.reddit import scrape_reddit_for_cities
from backend.app.score.engine import openai_score_city, openai_top_topics, top_keyword_counts
from backend.app.score.selection import smart_select_for_city

# Global nlp model (loaded once)
nlp = None

def load_nlp():
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load("en_core_web_md")
        except:
            print("Warning: en_core_web_md not found, trying en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

def run_job(job_id: str):
    try:
        load_nlp()
        req = get_job_request(job_id)
        if not req:
            return

        update_job(job_id, status="running", progress=5, message="Starting scrape...")
        
        # Setup directories
        out_dir = f"data/jobs/{job_id}"
        os.makedirs(out_dir, exist_ok=True)
        
        # Determine scope
        cities = req.cities
        
        # 1. Scrape News (Generalized for now, could be city-specific if we had city->news map)
        # For this MVP, we scrape global sources but filter by city mentions later, 
        # OR we could rely on Reddit mostly for specific cities if news discovery is hard.
        # v3 logic scrapes GLOBAL sources then filters. We'll do that but lighter.
        
        update_job(job_id, progress=10, message="Scraping global news sources...")
        
        # Use a subset of reliable sources to save time
        sources = [
            "https://www.nytimes.com", "https://www.bbc.com", "https://www.reuters.com",
            "https://www.theguardian.com", "https://www.bloomberg.com"
        ]
        
        all_entries: List[Entry] = []
        
        # Parallel scrape news
        # In a real "deep" scrape we might want local sources too.
        # For now, sticking to v3's global approach but we filter aggressively later.
        for src in sources:
            label = src.replace("https://", "").replace("www.", "").split("/")[0]
            entries = scrape_news_site(src, label, limit=20 if req.depth == "standard" else 50)
            all_entries.extend(entries)
            
        update_job(job_id, progress=30, message="Scraping Reddit communities...")
        
        # 2. Scrape Reddit (Targeted)
        city_subs = {}
        for c in cities:
            # Try exact match or fallback
            sub = CITY_SUBREDDITS.get(c)
            if sub:
                city_subs[c] = sub
            else:
                # Naive fallback
                city_subs[c] = c.replace(" ", "").lower()
                
        reddit_entries = scrape_reddit_for_cities(
            city_subs, 
            max_pages=2 if req.depth == "standard" else 5,
            comments_per_post_limit=20 if req.depth == "standard" else 50
        )
        all_entries.extend(reddit_entries)
        
        update_job(job_id, progress=50, message="Analyzing content...")
        
        # 3. Detect cities in news (heuristic + NLP)
        # v3 logic simplified: just string match for now + NLP if available
        # We already know which cities we want, so we just check if they are in the text.
        
        city_to_entries: Dict[str, List[Entry]] = defaultdict(list)
        
        for e in all_entries:
            # If Reddit, it's already tagged
            if e.cities:
                for c in e.cities:
                    if c in cities:
                        city_to_entries[c].append(e)
            else:
                # News: check text for city name
                # Simple case-insensitive match for the target cities
                found = []
                blob = (e.title + " " + e.text).lower()
                for c in cities:
                    if c.lower() in blob:
                        found.append(c)
                
                if found:
                    e.cities = found
                    for c in found:
                        city_to_entries[c].append(e)

        update_job(job_id, progress=60, message="Generating scoring & insights...")
        
        # 4. Score Cities
        results: List[CityResult] = []
        
        total_c = len(cities)
        for i, city in enumerate(cities):
            items = city_to_entries.get(city, [])
            
            # Select best items
            selected = smart_select_for_city(city, items, 200, nlp)
            
            # Prepare snippets
            snippets = []
            for e in selected:
                snip = f"Title: {e.title}\nText: {e.text[:500]}\nSource: {e.source} [{e.source_site}] {e.url}"
                snippets.append(snip)
            
            # Score with OpenAI
            score_data = openai_score_city(city, snippets)
            
            # Convert to Pydantic
            cat_scores = {}
            for k, v in score_data.get("category_scores", {}).items():
                cat_scores[k] = DimensionScore(score=v.get("score", 0), rationale=v.get("rationale", ""))
            
            top_issues = []
            for iss in score_data.get("top_issues", []):
                top_issues.append(Issue(name=iss.get("name", ""), why_it_matters=iss.get("why_it_matters", "")))
            
            # Collect URLs
            urls = []
            reddit_posts = []
            seen_urls = set()
            for e in items: # Use all items for citations, not just selected
                if e.url not in seen_urls:
                    urls.append(e.url)
                    seen_urls.add(e.url)
                    if e.source == "RedditPost":
                        reddit_posts.append(e.url)
            
            results.append(CityResult(
                city_name=city,
                overall_health=score_data.get("overall_health", 0),
                category_scores=cat_scores,
                top_issues=top_issues,
                citations=urls,
                reddit_posts=reddit_posts
            ))
            
            update_job(job_id, progress=60 + int(30 * (i+1)/total_c), message=f"Analyzed {city}")

        # 5. Save results
        final_json = {
            "cities": [r.model_dump() for r in results],
            "job_id": job_id,
            "timestamp": time.time()
        }
        
        with open(f"{out_dir}/results.json", "w") as f:
            json.dump(final_json, f, indent=2)
            
        # Also save raw entries for chat grounding
        with open(f"{out_dir}/entries.json", "w") as f:
            # serialize entries
            json.dump([e.model_dump() for e in all_entries], f, indent=2)

        update_job(job_id, status="completed", progress=100, message="Analysis complete.")

    except Exception as e:
        print(f"Job failed: {e}")
        update_job(job_id, status="failed", progress=0, message=str(e))
