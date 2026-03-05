# Our City Health — Predictive Civic Intelligence Platform

> **Every location decision deserves real-time civic intelligence.**  
> We turn global news, social media, and event data into a standardized 12-dimension "Civic Health Score" for 1,000+ cities — giving the private sector a predictive edge before protests, delays, and community opposition materialize.

[![Pitch Deck](https://img.shields.io/badge/Pitch%20Deck-View%20Live-brightgreen)](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/JAN20_pitch_deck.html)
[![Globe Demo](https://img.shields.io/badge/V2%20Globe-Live%20Demo-00d4ff)](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-V2%20Active%20Development-blue)]()

---

## What We're Building

**Our City Health** is a geo-centric predictive civic intelligence platform that quantifies the invisible risks embedded in location-based decisions. We ingest unstructured global data — news, social media, government event feeds — and transform it into auditable, citation-backed "Civic Health Scores" across 12 standardized dimensions for cities and their districts.

The core thesis: the signals that predict community opposition, safety deterioration, economic decline, and governance breakdown are already public. They exist in news coverage, in Reddit threads, in GDELT event databases. But no platform has built the right architecture to turn that noise into actionable intelligence for the private sector.

**We solve that.**

### The Problem

Real estate developers, retail site selection teams, logistics operators, and corporate security teams lose billions annually to risks that were *visible in the data* weeks or months before they materialized:

- **Real Estate:** 70% of housing developments face community opposition delays. In major global cities, a 3-year delay costs **15–25% of total project value** annually in financing costs and lost opportunity.
- **Retail:** **30–50% of retail locations fail within 3 years globally** (JLL Global Retail Report 2024) — many because neighborhood sentiment trends weren't detected during site selection, before the lease was signed.
- **Logistics & Corporate Security:** Labor unrest, anti-foreign sentiment, and civil instability are detectable in local forum and news data 4–8 weeks before they disrupt operations.

Existing tools don't address this gap. Brandwatch is entity-centric (tracks brand mentions, not locations). Zencity is built for governments, not private developers. Placer.ai measures foot traffic, not adversarial sentiment. Dataminr tells you when the riot starts — we tell you which neighborhood will reach a tipping point 3 months in advance.

### Our Differentiation

| Dimension | Competitors | Our City Health |
|-----------|-------------|-----------------|
| **Architecture** | Entity-centric (Brandwatch) or government-focused (Zencity) | **Geo-centric** — select a location, get *all* sentiment about that place |
| **Insight Level** | Event alerts (Dataminr) or store traffic (Placer.ai) | **12-dimension city and district scores** |
| **Audit Trail** | Black box outputs | **Every score cites its source articles** |
| **Time Horizon** | Real-time only, or historical-only reports | **Real-time + historical + 30/60/90-day projections** |
| **Setup Cost** | Complex boolean queries per city, per language | **Zero query engineering — click a city, see all 12 dimensions** |

---

## The Platform: V1 → V2

### V1 — Proof of Concept (2025)

The first version proved the core technical thesis: that civic health can be scraped, scored, and visualized at scale.

**What was built:**
- A Python scraping pipeline ingesting hundreds of news sources (Reuters, BBC, NYTimes, Bloomberg, The Guardian) and Reddit communities concurrently
- A FastAPI backend with a job queue system for parallel city processing
- An LLM-powered semantic scoring engine using GPT-4 to evaluate 12 civic dimensions from raw article text
- A Three.js 3D globe interface rendering color-coded Civic Health Scores for 108 cities
- An HTML/CSS corporate dashboard prototype with portfolio management, dimension filtering, and a grounded AI chat system (RAG architecture — no hallucinations)

**What V1 proved:**
- Geo-centric architecture is technically feasible: select coordinates → get all relevant sentiment
- LLM semantic analysis detects implicit sentiment (sarcasm, local slang, culturally-specific phrasing) that keyword matching misses
- The 12-dimension framework produces consistent, interpretable scores across diverse cities
- An audit trail (every score linked to source articles) is achievable without sacrificing speed

**V1 limitations:** 100-city ceiling, on-demand processing only, no historical data, LLM prompts were generative rather than schema-validated.

---

### V2 — Enterprise Rebuild (2025–2026, Active)

V2 is a ground-up rebuild targeting institutional-grade reliability, 1,000+ city scale, and 5-year historical depth. It runs in parallel to V1 — the original demo remains live.

#### Infrastructure

- **Database:** PostgreSQL with PostGIS (geospatial queries) and TimescaleDB (time-series hypertables), containerized with Docker
- **Cities:** 1,000+ cities loaded from GeoNames with PostGIS POINT geometries; district-level boundaries from OpenStreetMap via OSMnx
- **Historical Data:** GDELT BigQuery pipeline ingesting 5 years of global event data, partitioned into Parquet archives and aggregated into TimescaleDB daily stats
- **Caching:** Redis with 6-hour TTL on LLM scoring responses
- **API:** FastAPI with async SQLAlchemy, deployed on Railway

#### Scoring Engine

The V2 scoring engine replaces generative LLM prompting with **deterministic, schema-validated output**:

- **Instructor + Pydantic V2:** Every LLM response is forced into a strict schema (`CityHealthScore`, `DimensionScore`, `RiskOrStrength`). Validation failures trigger automatic retries. Temperature is set to 0 for reproducibility.
- **Enriched Context:** Before scoring, the aggregator constructs a rich context object from:
  - Top 25 GDELT events ranked by `abs(goldstein_scale) × mentions`, deduplicated by CAMEO code + actor + temporal proximity
  - GKG article intelligence: named entities (persons, organizations), theme distribution, source tone by credibility tier
  - Event clusters grouped by CAMEO root code with statistics
  - Period-over-period score deltas from TimescaleDB
- **Source Credibility Ranking:** Articles are ranked into 4 tiers (Tier 1: Reuters, BBC, AP; Tier 2: major nationals; Tier 3: industry/wire; Tier 4: unknown) with article-count limits per domain to prevent single-source dominance
- **Causal Attribution:** Each dimension score includes a `causal_driver` field — a direct causal explanation for why the score moved, grounded in specific events
- **Full Citations:** Every risk, strength, and evidence snippet links to source URLs with tier badges

#### Frontend — The Iron Man HUD

The V2 frontend is built around a **CesiumJS 3D globe** with a floating glassmorphism HUD overlay:

- **Globe:** 1,000+ city dots color-coded by stability score across a continuous 7-stop gradient (red → yellow → green → teal). No-data cities render as faint white dots to maintain visual hierarchy. District polygons render semi-transparently when zoomed below 200km altitude for a selected city.
- **HUD Panels:** Glassmorphism (`backdrop-filter: blur`) panels for city detail, sidebar city list, time scrubber, and comparison mode
- **City Detail Panel:** Stability score with delta arrow, intelligence metadata bar (articles analyzed, outlet count, source tier breakdown), analyst summary, entity tags, theme distribution mini-chart, expandable civic dimensions with causal drivers, structured risks/strengths with tiered citations, key events feed, collapsible media landscape section
- **Time Machine:** A timeline scrubber with playback animation (1×/2×/5× speed), data coverage indicator, and city color reactivity — drag to any date in the historical archive and watch the globe recolor
- **Sidebar:** Virtualized city list with debounced search, population/score filters, and fly-to animation on select
- **Comparison Mode:** Side-by-side city cards with a Recharts RadarChart for 12-dimension comparison
- **Keyboard Navigation, URL State, Mobile Responsive**

#### V2 API Endpoints

```
GET /api/v2/cities                          — 1,000+ cities with coordinates
GET /api/v2/cities/scores?date=&window_days= — globe color data
GET /api/v2/score/{city_id}?date=           — full LLM intelligence score
GET /api/v2/score/{city_id}/history         — TimescaleDB time series
GET /api/v2/sources/{city_id}?start=&end=   — GKG source breakdown by tier
GET /api/v2/events/{city_id}               — raw GDELT events with CAMEO descriptions
GET /api/v2/cities/{city_id}/districts      — GeoJSON district boundaries
GET /api/v2/data-coverage                   — dates with available GDELT data
```

---

## The 12-Dimension Taxonomy

Our proprietary scoring framework decomposes civic health into 12 independently measurable dimensions:

| Dimension | What It Captures |
|-----------|-----------------|
| **Safety** | Crime perception, policing trust, public order |
| **Housing** | Affordability stress, rental market tension, availability |
| **Economy** | Job market sentiment, business confidence, economic optimism |
| **Governance** | Trust in local government, corruption perception, policy effectiveness |
| **Transport** | Public transit quality, traffic, infrastructure investment |
| **Environment** | Air quality perception, green space access, sustainability discourse |
| **Health** | Healthcare access, public health sentiment, disease risk |
| **Culture** | Arts, entertainment, community identity, social vibrancy |
| **Education** | School quality perception, access, educational opportunity |
| **Technology** | Digital infrastructure, tech adoption, innovation ecosystem |
| **Community** | Social cohesion, civic engagement, neighborhood trust |
| **Cost of Living** | Broad affordability perception, price stress, purchasing power |

Each dimension carries a 0–100 score, a confidence level (0.0–1.0 calibrated to evidence quality), period-over-period delta, causal driver, evidence snippets, and source citations.

---

## Product Suite

### Corporate Dashboard — SaaS (HK$1,500/mo → HK$50K/yr)

Real-time civic intelligence for location-based decisions:

- **Portfolio Management:** Organize monitored cities into logical groupings ("GBA Expansion Assets", "European Retail Pipeline")
- **12-Dimension Scores:** City and district-level granularity, updated on a rolling basis
- **Watchlists & Alerts:** "Notify me if Safety in Hong Kong drops below 50" — threshold-based alerting across any dimension
- **Predictive Analytics:** 30/60/90-day sentiment projections with confidence intervals and leading indicator detection
- **Multi-Location Comparison:** Side-by-side analysis with exportable reports
- **5-Year Historical Trend Lines:** Pattern detection, backtesting, recovery cycle identification

### Custom Intelligence Reports — Enterprise (HK$50K+/yr)

Forecast-first bespoke analysis, not post-mortems:

- **Market Entry Forecasts:** 12-month trajectory predictions for target cities with confidence intervals
- **Comparative Advantage Analysis:** "Jakarta vs. Manila — which city will be more stable in 18 months?"
- **Crisis Root Cause Analysis:** "What caused Safety to drop 15 points in Lagos in Q3?"
- Delivered as 20+ page PDFs with full audit trails. Fast turnaround: 3–5 business days.

### API Firehose & Data License — Institutional (HK$100K+/yr)

For quantitative trading firms and enterprise data teams:

- Real-time JSON feed for 1,000+ cities
- 5-year historical archive
- District-level granularity
- Raw scores, GDELT events, GKG article metadata
- Custom webhooks for real-time threshold alerts

---

## Current Status

| Metric | V1 (Shipped) | V2 (Active Development) | Target |
|--------|-------------|-------------------------|--------|
| **Cities** | 108 | 1,000+ loaded | 1,000+ with live data |
| **Data Depth** | On-demand scraping | 5-year GDELT historical | Rolling daily updates |
| **Scoring** | Generative LLM | Schema-validated + citations | Production-grade |
| **Globe** | Three.js, basic | CesiumJS + HUD, deployed | Live at GitHub Pages |
| **Backend** | SQLite + FastAPI | PostGIS + TimescaleDB + Railway | Live API |
| **Customers** | 0 | 0 (pre-revenue) | 10+ enterprise (EOY 2026) |

### Milestones Completed

- ✅ Scraped and scored 108 cities with full 12-dimension analysis (V1)
- ✅ Built functional 3D globe visualization with smooth interaction (V1 → V2)
- ✅ Demonstrated RAG-grounded AI chat system with zero hallucinations (V1)
- ✅ Rebuilt on PostGIS + TimescaleDB with async SQLAlchemy for 10× data scale (V2)
- ✅ Ingested 5 years of GDELT historical event data for Shanghai (V2 pilot)
- ✅ Deployed deterministic Pydantic/Instructor scoring engine — no schema drift (V2)
- ✅ Implemented source credibility ranking, event deduplication, named entity extraction from GKG (V2.2)
- ✅ Launched V2 globe publicly on GitHub Pages with full HUD interface (V2)
- ✅ Implemented score deltas, causal attribution per dimension, period-over-period intelligence (V2.2)

### Roadmap (2026)

**Q1–Q2:** Production data pipeline for 1,000+ cities (GDELT daily ingestion); Corporate Dashboard v1.0 with watchlists and alerts; predictive model v1 with backtesting validation

**Q3:** API + Dashboard beta launch; 10 beta users (real estate and retail teams); pricing validation

**Q4:** Full commercial availability; enterprise sales outreach; first paid contracts; target 10+ enterprise customers

---

## Who We're Building For

### Primary Markets

**Commercial Real Estate — Land Acquisition Teams**  
Before bidding on land in a major city, developers need to quantify "Entitlement Risk" — the probability that community opposition will delay or kill the project. Our scoring detects low social cohesion, active housing affordability campaigns, and governance distrust *before* the first community meeting.

**Retail & QSR Site Selection**  
Site selection teams overlay our Safety and Cultural Vibrancy scores on top of Placer.ai traffic data. We explain the *why* behind foot traffic trends and predict future performance — not just the current state.

### Scale Markets (Year 2–3)

- **P&C Insurance:** Parametric civic risk triggers for pricing and reserve adjustments
- **Government & Smart City:** Real-time policy effectiveness measurement replacing expensive annual surveys
- **Logistics & Corporate Security:** Soft-signal alerts for labor unrest and civil instability at shipping hubs and travel destinations
- **Quantitative Trading:** Municipal bond and EM currency signals derived from civic stability trends

### Launch Market: Hong Kong & GBA

Hong Kong is our beachhead — direct access to HK/GBA companies expanding overseas, where they lack local intelligence. Our native Cantonese, Mandarin, and English processing (including local slang and cultural context) is a competitive advantage that tools built for Western markets cannot match.

---

## Team

### Cayden Auyang — Founder & Chief Architect

Gap year (2025–2026) fully dedicated to Our City Health. Incoming undergraduate (2026).

Technical background in AI/ML engineering, agentic AI workflows, and full-stack development. Founded the Civic AI Group at Hunter College High School — a 20+ person student and advisor initiative using AI to automate workflows for school faculty. Previously built market intelligence tools at Wisers combining web scraping, LLM analysis, and API integration for fashion brand competitive intelligence.

Expert in modern AI development workflows (Cursor, Claude, GPT-4, LangChain) enabling rapid prototyping cycles. Has independently built macOS GUI automation agents, browser-based games, and data intelligence pipelines.

**Contact:** caydenauyang@gmail.com · +1 (646) 889-4501 · [LinkedIn](https://linkedin.com/in/cayden-auyang) · [GitHub @CaydenAuyang](https://github.com/CaydenAuyang)

### Alvin Mok — Key Advisor

Chief Information and Data Officer, Select Equity Group (USD $25B+ AUM). Former Global Head of Platform and Insights at Orbis Investments (9 years). Former Engagement Manager, McKinsey & Company (Asia/China — high tech, travel, infrastructure). Harvard Business School MBA (Baker Scholar, Top 5%). University of Toronto BASc Computer Engineering (highest cumulative average, 2003).

Advisory role: data infrastructure strategy, alternative data acquisition, AI/ML product development, institutional investor positioning.

---

## Links

| | |
|-|-|
| **V2 Globe (Live)** | [caydenauyang.github.io/Our-City-Health---Sentiment-Project](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/) |
| **Pitch Deck** | [JAN20 Pitch Deck — HKSTP Ideation](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/JAN20_pitch_deck.html) |

---

## Collaboration

We're open to:

- **Early Adopter Partnerships:** Beta testers from commercial real estate, retail site selection, insurance, or corporate security
- **Academic Collaborations:** Urban planning researchers, sentiment analysis experts, social sensing scholars
- **Strategic Advisors:** Industry veterans in PropTech, location intelligence, alternative data, or civic technology
- **Investors:** Pre-seed/seed stage interest in SaaS, alternative data, or civic technology

The repository is public for portfolio and demonstration purposes. Core scoring algorithms and data pipelines are proprietary.

---

*Last updated: February 2026*
