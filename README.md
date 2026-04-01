# OurCityHealth

> A city intelligence API that scores cities across 12 civic dimensions using AI analysis of 380,000+ global news sources.

[![CCMF Pitch Deck](https://img.shields.io/badge/CCMF%20Pitch%20Deck-View%20Live-00D4AA)](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/CCMF_pitch_deck.html)
[![Globe Demo](https://img.shields.io/badge/V2%20Globe-Live%20Demo-00d4ff)](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-blue)]()

---

## What is OurCityHealth?

OurCityHealth is an API where you call a city name and get back structured JSON with scores across 12 civic dimensions: safety, economy, transport, governance, housing, environment, health, culture, education, technology, community, and cost of living.

Scores update weekly based on a rolling window of global news data. Each score includes a week-over-week delta showing direction of change, a causal explanation of what drove the change, and links to the original source articles. Historical scores are stored for trend tracking over months.

Data comes from AI analysis of 380,000+ news outlets via GDELT, with every source ranked across a 4-tier credibility system (Tier 1: major international wire services, down to Tier 4: unverified sources).

### The Problem

Decisions worth billions of dollars depend on understanding how cities are performing, yet there is no standardized, programmatic way to assess a city's conditions:

- **Consultancy reports** (McKinsey, EIU) are deep but cost six figures, cover a few hundred cities, and publish once a year as PDFs.
- **Raw event data** (GDELT) is free but requires building an entire processing pipeline from scratch.
- **Sentiment tools** (Brandwatch, Meltwater) track brand mentions, not places. Their architecture is entity-centric, not geo-centric.
- **Civic platforms** (ZenCity) serve individual city governments, not cross-city comparison or developer integration.

We have not found an actively maintained city intelligence API that is simultaneously continuously updated, multi-dimensional, geo-centric, source-verified with causal attribution, and delivered as structured JSON.

### How It Works

```
380,000+ news sources (GDELT)
        │
        ▼
   INGEST: BigQuery extraction, geospatial filtering (haversine distance)
        │
        ▼
   PROCESS: Event deduplication (25K raw events → 24 real stories),
            4-tier source credibility ranking,
            named entity and theme extraction (GKG)
        │
        ▼
   SCORE: AI evaluation engine produces structured 12-dimension assessments
          with causal attribution and source citations
        │
        ▼
   SERVE: Pre-computed scores via REST API, sub-50ms response times
```

### Example API Response

```json
GET /api/v2/score/{city_id}

{
  "city": "Hong Kong",
  "overall_score": 54,
  "dimensions": {
    "safety": {
      "score": 45,
      "delta": -5.0,
      "causal_driver": "11 police-involved incidents over 4 days, corroborated by 3 Tier-2 sources",
      "confidence": 0.78
    },
    "economy": {
      "score": 60,
      "delta": +3.0,
      "causal_driver": "Trade expo coverage and positive investment sentiment from 5 Tier-1 sources",
      "confidence": 0.85
    }
  },
  "total_articles_analyzed": 39,
  "unique_sources_analyzed": 26,
  "source_tier_breakdown": { "tier_1": 3, "tier_2": 8, "tier_3": 3, "tier_4": 12 }
}
```

---

## What's Built

OurCityHealth has gone through two major versions. V1 was a proof of concept. V2 is the current production system.

### V2 (Current, 2025-2026)

The V2 system is a ground-up rebuild targeting data integrity and commercial viability.

**Backend:**
- Python/FastAPI with async SQLAlchemy
- PostgreSQL with PostGIS for geospatial queries and TimescaleDB for time-series data
- GDELT BigQuery ingestion pipeline covering 380,000+ global news sources
- GKG (Global Knowledge Graph) article-level intelligence extraction: named entities, themes, tone, multi-language processing
- Custom event deduplication engine grouping events by CAMEO code, shared actors, and temporal proximity
- 4-tier source credibility ranking system
- AI evaluation engine with schema-enforced structured outputs (Pydantic V2 + Instructor)
- Pre-computed scoring pipeline serving responses in under 50ms from PostgreSQL
- Redis caching layer

**Frontend:**
- React/TypeScript with CesiumJS 3D globe rendering 1,000+ cities
- Glassmorphism HUD interface with city detail panels, score deltas with causal drivers, source tier badges on all citations
- Timeline scrubber with playback controls and interactive calendar
- City comparison mode with radar charts
- Sidebar explorer with search, filters, and sorting

**Cities scored:** Hong Kong, Shanghai, Shenzhen, Singapore, Tokyo, London, New York (with infrastructure ready for 1,000+)

**API Endpoints:**
```
GET /api/v2/cities                              List all cities with coordinates
GET /api/v2/cities/scores?date=&window_days=    Globe color data (all cities)
GET /api/v2/score/{city_id}?date=               Full intelligence score for a city
GET /api/v2/score/{city_id}/history             Historical time series
GET /api/v2/sources/{city_id}?start=&end=       Source breakdown by credibility tier
GET /api/v2/events/{city_id}                    Raw GDELT events
GET /api/v2/data-coverage                       Dates with available data
```

### V1 (Archived, 2025)

The first version proved the core technical thesis. It used direct web scraping of news sources and Reddit, a Three.js 3D globe, and generative LLM scoring. V1 code is preserved in the `archive/v1/` directory for reference.

---

## The 12-Dimension Taxonomy

| Dimension | What It Captures |
|-----------|-----------------|
| Safety | Crime patterns, policing, public order |
| Housing | Affordability, availability, quality |
| Economy | Job market, business confidence, growth signals |
| Governance | Government trust, corruption, policy effectiveness |
| Transport | Public transit quality, infrastructure investment |
| Environment | Air quality, green space, sustainability |
| Health | Healthcare access, public health conditions |
| Culture | Arts, entertainment, social vibrancy |
| Education | School quality, access, opportunity |
| Technology | Digital infrastructure, tech adoption |
| Community | Social cohesion, civic engagement, trust |
| Cost of Living | Broad affordability, price stress |

Each dimension produces a 0-100 score with a confidence level, week-over-week delta, causal driver explanation, evidence snippets, and source citations with credibility tier badges.

---

## Business Model

OurCityHealth is an API-first data utility. Free public dashboard for civic transparency, with paid tiers for developers and companies who integrate city intelligence into their products.

| Tier | Price | What You Get |
|------|-------|-------------|
| Free | HK$0 | Public dashboard at ourcityhealth.com |
| Developer | HK$380/mo | 500 API calls/day, 30-day history |
| Pro | HK$2,300/mo | Unlimited calls, full history, webhooks, source-level detail |
| Enterprise | HK$7,800+/mo | Custom weighting, white-label, dedicated SLA |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, async SQLAlchemy |
| Database | PostgreSQL + PostGIS + TimescaleDB |
| Data Source | GDELT via Google BigQuery (380,000+ outlets) |
| AI Scoring | Frontier LLM with Instructor/Pydantic schema enforcement |
| Caching | Redis |
| Frontend | React, TypeScript, CesiumJS |
| Deployment | Railway (backend), GitHub Pages (frontend) |
| CI/CD | GitHub Actions |

---

## Repository Structure

```
├── v2_engine/                 Current production system
│   ├── backend_v2/            FastAPI backend, scoring engine, data pipeline
│   ├── frontend_v2/           React/CesiumJS globe interface
│   ├── scripts/               Ingestion and utility scripts
│   ├── Dockerfile             Railway deployment
│   └── requirements.txt
├── archive/                   V1 code and old pitch decks (preserved for reference)
├── docs/                      Documentation and images
├── screenshots/               Product screenshots and demo videos
├── .github/workflows/         CI/CD configuration
└── README.md
```

---

## Team

**Cayden Auyang, Founder**
18 years old. Built the entire platform solo. Previously interned at Wisers Information Limited (Hong Kong) on the AI team, where he built an LLM-powered market analysis pipeline and a macOS GUI automation agent combining computer vision with LLM reasoning. Runs AI Simply, a productivity consulting business serving clients across 7 industries. Founded the Civic AI Group at Pomfret School (20+ members). Head of School Scholar. Hong Kong ID holder, based in Hong Kong for summer 2026 and planned gap year starting 2027.

**Alvin Mok, Key Advisor**
Chief Information and Data Officer at Select Equity Group, L.P. (New York). Former Head of Global Platform and Insights at Orbis Investments ($25B+ AUM). Former Engagement Manager at McKinsey (Asia/China). Harvard Business School MBA, Baker Scholar (top 5%). University of Toronto BASc Computer Engineering (highest cumulative average). Regular calls reviewing product decisions and advising on data buyer expectations.

---

## Contact

caydenauyang@gmail.com

---

## License

[MIT](LICENSE)
