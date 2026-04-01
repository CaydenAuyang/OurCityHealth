# Our City Health — Context Brief

**Goal:** Turn public news + Reddit into a transparent, comparable Civic Health Pulse per city (12 dimensions), with traceable citations.

**Pipeline (authoritative file: `Automation-Project/conclusive_scraper_and_analysis.py`):**
1) Discover links (RSS/sitemaps → homepage fallback), fetch concurrently (timeouts/retries).
2) Parse + normalize; tag cities (local domains, synonyms, spaCy NER).
3) Score documents: reputation, civic relevance, coverage/length, recency, domain diversity; dedup titles.
4) Fairness: enforce per-city cap (`--city_docs`).
5) LLM scoring to strict JSON: overall + 12 dimensions + rationales + top issues.
6) Aggregate globals; write outputs:
   - `data/latest/full_results.json`
   - `data/latest/city_boundaries.geojson`
   - `data/visited.sqlite` (visited URLs, cumulative metrics)

**Dashboards:**
- `map.html`: globe with per-run & cumulative stats.
- `city_health_dashboard_MASSIVE.html`: city cards, modal tabs (Scores, Issues, Articles, Reddit Posts), all citations.

**Non-negotiables:** fairness, transparency, deterministic JSON schema, respectful scraping.

**Common Commands:**
- Fast sample:
  ```
  python3 Automation-Project/conclusive_scraper_and_analysis.py --num_cities 20 --per_source_limit 120 --reddit_pages 3 --reddit_comments 50 --city_docs 200 --out data/latest
  ```
- Serve UI:
  ```
  cd Automation-Project
  python3 -m http.server 8765
  # open /map.html and /city_health_dashboard_MASSIVE.html
  ```

**Future Roadmap Hints (safe to propose behind flags):** add verified local sources, better boundary polygons, comment-level dedup, multilingual.
