# Our City Health
**Interactive, transparent civic health analytics for global cities. We transform large-scale news and Reddit data into a comparable Civic Health Pulse with per-category scores, top issues, and full citations  — [ourcityhealth.com](https://ourcityhealth.com)**


### What’s included
- `Automation-Project/conclusive_scraper_and_analysis.py`: end‑to‑end data pipeline (scraping → NLP/LLM → JSON outputs).
- `Automation-Project/map.html`: interactive 3D globe with clickable cities, search, and high‑contrast borders.
- `Automation-Project/city_health_dashboard_MASSIVE.html`: modern dashboard with city cards, modal details, and full citations.

## Key capabilities

### Massive, reliable data collection
- RSS/sitemaps-first link discovery with homepage fallback; requests + BeautifulSoup parsing.
- Fast + safe fetching: connection pooling, concurrency, gzip/br, 8s timeouts, limited retries/backoff.
- Thread‑safe SQLite cache (`data/visited.sqlite`) for visited URLs and resume; deduped by URL.
- Reddit via JSON endpoints (`api`, `old`, `www`) with concurrency and backoff; parallel comment fetching.

### NLP + fair LLM analysis
- City tagging: local domain mapping + city/synonym matches + spaCy NER.
- Smart selection per city: quality (source reputation, length), relevance (civic keywords), recency, diversity (domain caps), dedup.
- Fairness: balanced per‑city document cap for scoring (configurable via `--city_docs`).
- LLM output: overall score + 12 categories with rationales, top issues; strict JSON.

### Transparency & cumulative metrics
- Full citations (articles + Reddit links) per city exposed in outputs and UI.
- Per‑run summary and cumulative metrics (distinct articles/posts, total comments) stored and surfaced.
- Last run timestamp embedded in results for dashboards to display.

## How it works (pipeline)

1) Discover links (RSS/sitemaps → fallback to homepage), fetch concurrently with pooled sessions.  
2) Parse title/body, normalize, dedupe, and tag cities (local domains + synonyms + NER).  
3) Score documents (quality/relevance/recency/diversity), fairness-normalized selection.  
4) LLM scoring per city (overall + 12 categories + top issues) → structured JSON.  
5) Aggregate global topics; write `data/latest/full_results.json` and `data/latest/city_boundaries.geojson`.  
6) Update cumulative metrics in `data/visited.sqlite` (`metrics` table).

## Outputs

- `data/latest/full_results.json`
  - `summary`: per‑run counts (`news_articles`, `reddit_posts`, `reddit_comments`, `cities_covered`), `run_timestamp` (UTC).
  - `summary.cumulative`: `news_articles_distinct`, `reddit_posts_distinct`, `reddit_comments_total`.
  - `topics`: ranked global issues (with descriptions, top cities).
  - `cities[]`: `{ name, health_score, dimensions{…}, top_issues[], citations[], articles[], reddit_posts[] }`.

- `data/latest/city_boundaries.geojson`: best-effort city boundaries for map highlighting.

- `data/visited.sqlite`: thread-safe cache
  - `visited(url, first_seen)` – distinct articles across runs.
  - `metrics(k,v)` – cumulative counters (distinct articles, distinct Reddit posts, total Reddit comments).

## Dashboards

### Globe (`map.html`)
- Earth-like globe (Three.js/Three-Globe), white labels, white hover glow, crisp country borders.
- City boundary polygons (when available) glow on hover; search city/country; decluttered labels by zoom.
- Top bar shows: per‑run stats, last run timestamp, and cumulative counts.

### Dashboard (`city_health_dashboard_MASSIVE.html`)
- Modern minimalist UI; two rows of stats:
  - Per‑run: articles, Reddit posts, comments, cities.
  - Cumulative: distinct articles, distinct Reddit posts, total comments, last run.
- Data-driven city cards; modal tabs: Scores, Top Issues, Articles, Reddit Posts; all citations listed for auditability.

## Setup

### Requirements
- Python 3.9+ recommended
- Packages (install once):
```bash
pip install -r requirements.txt
```
- OpenAI key (for scoring):
```bash
export OPENAI_API_KEY="your-api-key"
```

### Run the analysis
- Full run (example):
```bash
cd Automation-Project
python3 conclusive_scraper_and_analysis.py \
  --cities_link "https://en.wikipedia.org/wiki/List_of_largest_cities" \
  --num_cities 100 \
  --per_source_limit 500 \
  --reddit_pages 10 \
  --reddit_comments 100 \
  --city_docs 500 \
  --out data/latest
```
- Faster check (small sample):
```bash
python3 conclusive_scraper_and_analysis.py --num_cities 20 --per_source_limit 120 --reddit_pages 3 --reddit_comments 50 --city_docs 200
```
- Reuse previous Reddit links (skip scraping, still show posts in UI):
```bash
python3 conclusive_scraper_and_analysis.py --reddit_pages 0
```

### View dashboards locally
```bash
cd Automation-Project
python3 -m http.server 8765
# Globe:
open http://localhost:8765/map.html
# Dashboard:
open http://localhost:8765/city_health_dashboard_MASSIVE.html
```

## Configuration (CLI flags)
- `--cities_link`: source for top cities table (e.g., Wikipedia).
- `--num_cities`: number of cities to analyze.
- `--per_source_limit`: max articles per global source.
- `--reddit_pages`: pages per subreddit (0 to reuse prior posts).
- `--reddit_comments`: max comments per post.
- `--city_docs`: per‑city fairness cap for LLM scoring inputs.
- `--out`: output directory (default `data/latest`).

## Methodology highlights

- 12 dimensions: Affordability, Services, Safety, Opportunity, Culture, Environment, Transportation, Governance, Housing, Economy, Education, Health.
- Document selection: reputation + civic relevance + coverage/length + recency + domain diversity + title dedup.
- LLM scoring: strict JSON; balanced snippets; rationales per category; top issues; deterministic settings.
- Global topics: aggregated from city issues and representative snippets; descriptions + notable cities.

## Performance & resilience
- Concurrency: parallel fetching for articles and Reddit comments (capped workers).
- Connection pooling: shared session with keep‑alive; tuned pool sizes.
- Smarter link discovery: RSS/sitemaps first; fewer dead links/wasted requests.
- Timeouts/retries: 8s timeout; limited backoff on 429/5xx.
- Compression: gzip/deflate/br by default.
- Caching/resume: SQLite visited URLs and cumulative metrics across runs.

## Project structure
```
Automation-Project/
  conclusive_scraper_and_analysis.py     # Main pipeline
  map.html                               # Interactive globe (per-run + cumulative stats)
  city_health_dashboard_MASSIVE.html     # City dashboard (per-run + cumulative stats)
  data/
    latest/
      full_results.json                  # Structured results (per-run + cumulative)
      city_boundaries.geojson            # City polygons for globe
  full_results.json                      # (example snapshot)
  full_results_MASSIVE.json              # (example snapshot)
  full_analysis_MASSIVE.txt              # (example snapshot)
  requirements.txt
```

## Automation
- Daily cron (example):
```bash
# Runs every day at 3:15 AM
15 3 * * * cd "/path/to/Automation-Project" && /usr/bin/python3 conclusive_scraper_and_analysis.py --out data/latest >> daily.log 2>&1
```
- Because of SQLite caching, reruns only fetch new articles; cumulative metrics update automatically.

## Roadmap
- Expand verified local sources per city and improve boundary polygons coverage.
- Per-comment ID tracking for true distinct Reddit comments.
- Multi-language coverage and localized models.
- Optional API endpoints for live integration.

## License
MIT (see LICENSE).

## Acknowledgments
OpenAI (LLM scoring), spaCy (NLP), Three.js/Three‑Globe (globe), TopoJSON/OSM sources (geodata), Reddit and global news publishers (content).
