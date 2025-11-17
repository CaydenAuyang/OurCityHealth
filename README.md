# Our City Health
**Interactive, transparent civic health analytics for global cities. We transform large-scale news and Reddit data into a comparable Civic Health Pulse with per-category scores, top issues, and full citations  — [ourcityhealth.com](https://ourcityhealth.com) (not functional site yet)**

## What's included
- `conclusive_scaper_and_analysis_v3.py`: end‑to‑end data pipeline (scraping → NLP/LLM → JSON outputs).
- `map.html`: interactive 3D globe with clickable cities, search, auto-rotation, and smooth camera transitions.
- `city_health_dashboard_MASSIVE.html`: modern dashboard with city cards, modal details, and full citations.

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

### Interactive 3D Globe (`map.html`)

**Overview:**
An immersive 3D Earth visualization built with Three.js and ThreeGlobe that displays city health scores as interactive markers on a rotating globe. The interface combines real-time data visualization with intuitive navigation controls.

**Visual Features:**

**Color-Coded City Markers:**
- **Green (#22c55e)**: Excellent health (score ≥ 80)
- **Light Green (#4ade80)**: Good health (score 65-79)
- **Yellow (#facc15)**: Moderate health (score 50-64)
- **Orange (#f97316)**: Poor health (score 35-49)
- **Red (#ef4444)**: Critical health (score < 35)
- **Gray (#9ca3af)**: No data available

City markers are rendered as clickable spheres/arrows that extend from the globe surface. Marker size scales dynamically with zoom level (0.5-0.95 radius units). Higher health scores result in markers positioned slightly above the globe surface (altitude: 0.012 + score/6000).

**Top Information Bar:**
Three pill-shaped badges display:
- **Summary Pill**: Shows current run statistics (e.g., "1,234 articles · 567 Reddit posts · 58 cities")
- **Run Timestamp Pill**: Displays last data collection timestamp in UTC (e.g., "Last run: 2025-11-17 05:45:50")
- **Cumulative Pill**: Shows aggregated metrics across all runs (e.g., "Cumulative: 5,678 articles · 2,345 posts · 12,456 comments")

**Search Bar:**
- **Location**: Top panel, full-width input field with dark background
- **Placeholder**: "Search city or country"
- **Features**:
  - Real-time filtering as you type
  - Case-insensitive matching
  - Searches both city names and country names
  - Handles common abbreviations (NYC → New York City, SF → San Francisco, LA → Los Angeles)
  - Normalizes diacritics and special characters
  - **Auto-center feature**: When search returns exactly one result, automatically centers camera on that city after 100ms delay
  - Fuzzy matching fallback for partial matches
- **Visual Feedback**: Filtered city list updates instantly; empty state shows "No cities match your search"

**City List Sidebar (Right Panel):**
- **Layout**: Fixed-width panel (380px) on the right side of the globe
- **Sorting**: Cities sorted by health score (highest first)
- **City Cards**: Each city displays:
  - City name (bold, 700 weight)
  - Country name (muted color, if available)
  - Health score (highlighted in green #9ef2c5)
  - Visual indicator for cities missing coordinates (red "· no map pin" text)
- **Interactivity**:
  - Hover effect: Card background changes to rgba(34,197,94,.06)
  - Click: Centers camera on city and opens detail sidebar
  - Cards with missing coordinates are dimmed (65% opacity)

**Interactive Globe Controls:**

**Mouse/Touch Interactions:**
- **Drag**: Rotate globe around center (panning disabled - globe stays centered)
- **Scroll/Pinch**: Zoom in/out (range: 140-360 distance units)
- **Click City Marker**: Opens city detail sidebar and centers camera
- **Click City List Item**: Centers camera on city and opens sidebar

**Auto-Rotation:**
- **Default State**: Globe automatically rotates slowly (speed: 0.5)
- **Pause Triggers**: Auto-rotation pauses when:
  - User starts dragging
  - User scrolls/zooms
  - Camera animation is active (city centering)
- **Resume**: Auto-rotation resumes:
  - 2 seconds after drag ends
  - 1.6 seconds after zoom ends
  - After camera animation completes

**Camera Transitions:**
When clicking a city (from marker or list), the camera performs a smooth 4-step animation:
1. **Rotate** (2 seconds): Camera rotates to face the city while maintaining distance
2. **Zoom In** (1.5 seconds): Camera moves closer (from ~280 to ~200 units) for detail view
3. **Hold** (30 seconds): Camera stays focused on the city
4. **Restore** (3.5 seconds): Camera zooms out and returns to original position

All transitions use easing functions for smooth motion. The camera always targets the globe center (0,0,0) to maintain centered rotation.

**City Detail Sidebar:**

**Opening**: Slides in from the right (420px width, 90vw max on mobile) with 0.3s ease transition

**Header**:
- City name (24px, bold)
- Close button (✕) in top-right corner (green #a8f3c7, hover effect)

**Tab Navigation** (4 tabs):
- **Scores Tab** (default): Displays all 12 dimension scores in a table format
  - Each row shows: Dimension name, Score (0-100), Rationale text
  - Scores displayed in green (#9ef2c5)
  - Rationales explain the scoring reasoning
- **Top Issues Tab**: Lists up to 20 top issues for the city
  - Each issue displayed as a list item with padding
  - Issues include "why it matters" explanations
- **Articles Tab**: Scrollable list of all news article citations
  - Each link opens in new tab (target="_blank")
  - Links styled in cyan (#8ff0c1)
  - Background cards with hover effects
- **Reddit Tab**: Scrollable list of all Reddit post citations
  - Same styling as Articles tab
  - Filters for reddit.com URLs

**Tab Styling**:
- Inactive tabs: Light green background (rgba(34,197,94,.08))
- Active tab: Darker green background (rgba(34,197,94,.18))
- Smooth transitions between tabs (0.2s)

**Closing**: Click ✕ button, click outside sidebar, or press Escape key

**Smart Label System:**

**Visibility Rules**:
- **Zoomed In** (< 180 distance): All labels hidden for clarity
- **Zoomed Out** (≥ 180 distance): Labels shown with smart decluttering

**Decluttering Algorithm**:
- Priority-based: Higher health scores shown first
- Overlap detection: Minimum 2px spacing between labels
- Greedy algorithm: Maximizes visible labels without overlap
- Viewport culling: Only shows labels visible on screen

**Label Styling**:
- White text (#ffffff)
- Size scales with zoom: 1.0x (far) to 1.7x (close)
- Positioned 0.02 units above globe surface
- No dots (clean text-only labels)

**Visual Elements:**

**Globe Appearance**:
- Earth texture: Blue Marble image from ThreeGlobe examples
- Bump map: Earth topology for 3D relief
- Country borders: White lines (0.88 opacity) from TopoJSON
- City boundaries: Green glow (rgba(34,197,94,0.22)) when GeoJSON available
- Background: Dark gradient (radial green glow + grid pattern)
- Atmosphere: Disabled (removed green film overlay)

**Legend** (Bottom-left):
- "• Green dots: clickable cities"
- "• Drag to rotate • Scroll to zoom"
- Dark semi-transparent background
- Updates to show count of cities missing coordinates

**Global Issues Panel**:
- Located below the globe
- Displays top 10 global issues
- Each issue card shows:
  - Issue number (padded, e.g., "01")
  - Issue name (bold)
  - Description text
  - Notable cities affected
  - Civic signals (tags)

**Scoring Methodology Panel**:
- Detailed explanation of the 4-step scoring process
- Exact percentages for document selection
- Fairness normalization details
- AI scoring methodology
- Transparency statement

**Technical Features:**

**Cache-Busting**:
- Multiple layers prevent stale data:
  - Meta tags: Cache-Control, Pragma, Expires headers
  - Fetch headers: no-cache, no-store directives
  - Query parameters: Timestamp + random string + session ID
  - Fetch option: cache: 'no-store'

**Path Resolution**:
Tries multiple paths for data files (handles different deployment scenarios):
1. `data/latest/full_results.json`
2. `./data/latest/full_results.json`
3. `../data/latest/full_results.json`
4. Relative to current pathname
5. `full_results.json` (fallback)

**Error Handling**:
- Graceful fallbacks if data fails to load
- GitHub Pages-specific error messages
- Console logging for debugging
- User-friendly error displays

**Performance Optimizations**:
- Throttled label updates (150ms intervals)
- Efficient scene traversal
- Matrix world caching
- RequestAnimationFrame loop
- Memory management (event listener cleanup)

**Responsive Design**:
- Mobile-friendly sidebar (90vw max width)
- Adaptive label sizing
- Touch-friendly click targets
- Responsive grid layout

### Dashboard (`city_health_dashboard_MASSIVE.html`)

**Overview:**
A modern, minimalist dashboard displaying city health scores in card format with detailed modal views.

**Layout:**
- **Hero Section**: Title and project description
- **Stats Rows**: Two rows of statistics pills
  - Row 1: Per-run metrics (articles, posts, comments, cities)
  - Row 2: Cumulative metrics (distinct articles, distinct posts, total comments, last run timestamp)
- **Global Issues**: Top 20 issues displayed in grid cards
- **City Grid**: Sortable city cards with health scores

**City Cards:**
- Sorted by health score (highest first)
- Color-coded score badges:
  - Green (≥75): Excellent
  - Yellow (60-74): Moderate  
  - Red (<60): Poor
- Hover effect: Card scales to 1.02x with enhanced shadow
- Mini dimensions preview on hover (first 4 dimensions)
- Top 3 issues preview

**City Modal:**
- Opens on card click
- Four tabs: Scores, Top Issues, Articles, Reddit Posts
- Scores table: All 12 dimensions with scores and rationales
- Coverage stats: Article count, Reddit links, total citations
- All citations are clickable links (open in new tab)

**Scoring Methodology Section:**
- Detailed 4-step process explanation
- Exact percentages and formulas
- Fairness normalization details
- AI scoring methodology
- Transparency statement

## Setup

### Requirements
- Python 3.9+ recommended
- Packages (install once):sh
pip install -r requirements.txt- OpenAI key (for scoring):
export OPENAI_API_KEY="your-api-key"### Run the analysis
- Full run (example):
python3 conclusive_scaper_and_analysis_v3.py \
  --cities_link "https://en.wikipedia.org/wiki/List_of_largest_cities" \
  --num_cities 100 \
  --per_source_limit 500 \
  --reddit_pages 10 \
  --reddit_comments 100 \
  --city_docs 500 \
  --out data/latest- Faster check (small sample):
python3 conclusive_scaper_and_analysis_v3.py --num_cities 20 --per_source_limit 120 --reddit_pages 3 --reddit_comments 50 --city_docs 200 --out data/latest- Reuse previous Reddit links (skip scraping, still show posts in UI):
python3 conclusive_scaper_and_analysis_v3.py --reddit_pages 0 --out data/latest### View dashboards locally
python3 -m http.server 8000
# Globe:
open http://localhost:8000/map.html
# Dashboard:
open http://localhost:8000/city_health_dashboard_MASSIVE.html### View dashboards online
- **Map**: https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/map.html
- **Dashboard**: https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/city_health_dashboard_MASSIVE.html

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
