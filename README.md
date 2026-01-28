# Our City Health — Predictive Civic Intelligence for Location Risk

> **Every million-dollar decision deserves real-time civic intelligence.**  
> We provide the missing **Social Layer** for site selection, operational monitoring, and community risk assessment — turning neighborhood sentiment into actionable intelligence for major cities worldwide.

[![GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-brightgreen)](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/JAN20_pitch_deck.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Proof%20of%20Concept-orange)]()
[![Coverage](https://img.shields.io/badge/Cities-108%20Operational-blue)]()

**🎯 Current Focus:** Building the world's first geo-centric predictive civic intelligence platform for private sector location risk assessment.

---

## 🎯 Our Mission & Objective

**Our City Health** is a geo-centric predictive civic intelligence platform that quantifies the invisible risks in location-based decisions. We transform unstructured global data — news, social media, forums, government portals — into a standardized "Civic Health Index" for 1,000+ cities and their districts.

### The Core Mission

**Predict, Don't React.** Before the protest. Before the town hall turns hostile. Before the 3-year delay that costs 15-25% of project value.

We're building the missing **Context Layer** for private sector location risk — a real-time, AI-powered intelligence system that:
- **Quantifies Community Sentiment:** Turn vague "neighborhood vibes" into precise, auditable 12-dimension scores
- **Predicts Adversarial Risk:** Identify which districts will resist development 3-6 months before opposition crystallizes
- **Explains the "Why":** Not just "Safety dropped 8 points" but *why* (340% increase in housing protest coverage, declining governance trust)
- **Enables Apples-to-Apples Comparison:** "Which city will be more stable 18 months from now: Jakarta or Manila?" — answered with confidence intervals and historical precedent

### What Makes This Urgent (Global Scale)

Every year, major city development projects worldwide lose **billions** to a problem that's invisible in traditional data:

- **Real Estate:** 70% of housing developments face community opposition delays. In major global cities, a 3-year delay costs **15-25% of the project value annually** in financing, lost opportunity, and carry costs (McKinsey Global Infrastructure Initiative).
- **Retail:** **30-50% of retail locations fail within 3 years globally** (JLL Global Retail Report 2024). Many failures could be prevented if sentiment trends were detected during site selection — before the lease was signed.
- **Operational Risk:** Logistics companies reroute shipments due to sudden "labor unrest" that was brewing in local forums for 2 months. Corporate security teams scramble when travel destinations become unstable — signals that were visible in social sentiment 6 weeks earlier.

**The Common Thread:** These are **preventable** risks. The signals exist. The data is public. But no one has built the "operating system" to turn this noise into actionable intelligence for the private sector.

### Our Vision (12-18 Months)

**Phase 1 (2026):** Become the go-to civic intelligence platform for location-based decision-making in commercial real estate, retail expansion, insurance, and corporate security across major global cities.

**Phase 2 (2027+):** Expand to serve quantitative trading firms (municipal bonds, EM currencies), supply chain risk teams, and government policy advisors. Build the "FICO Score for Cities" — a universally recognized standard for civic health measurement.

### The Problem We're Solving

**Existing tools measure *Activity* (foot traffic) or *Amenities* (cafe count). But no digital tool reliably captures *Adversarial Sentiment* or *Entitlement Risk*.**

Real estate developers and retail site selection teams rely on sophisticated tools like CoStar, Esri, and Placer.ai for demographics, traffic, and infrastructure data. Tools like Brandwatch and Zencity provide sentiment analysis — but Brandwatch is **entity-centric** (tracks brand mentions, not locations) and Zencity is **built for governments** (not private developers).

**The Information Gap:**  
This forces teams to rely on manual scouting of districts, like attending town hall meetings, and gut feelings to predict if a community will block their project — a "1990s workflow" for million-dollar decisions.

**Real-World Impact (Global Major Cities):**
- **Real Estate:** 70% of housing projects are delayed by community opposition (NIMBYism) globally. In major cities worldwide (London, Tokyo, Singapore, New York, Hong Kong), projects lose **15-25% of their value annually** to delay-related carry costs.
- **Retail:** **30-50% of retail locations fail within 3 years** globally (JLL Global Retail Report 2024), often because neighborhood sentiment trends weren't detected early enough during site selection.
- **The Cost:** For a typical major city development project, a 3-year delay due to community opposition can cost 15-25% of the total project value in financing costs, lost opportunity, and operational overhead — before the first tenant even moves in.

### Our Differentiation

We are **Geo-Centric**: Select a district or coordinates, and we capture *all* sentiment about that location — rent control protests, safety complaints, gentrification anger — regardless of what brands are mentioned.

**We don't replace existing tools — we complete them.**

| What We Provide | Why It Matters |
|----------------|----------------|
| **Predictive Analytics** | Know which neighborhoods will resist development 3 months in advance |
| **District-Level Granularity** | 12-dimension scores for every district in a city, not just city-wide averages |
| **Causal "Why" Analysis** | Not just "Safety dropped 8 points" but *why* (340% increase in housing protest coverage) |
| **Audit Trail** | Every score links back to source articles — no "black box" hallucinations |
| **Multi-Lingual NLP** | Native processing of Cantonese, Mandarin, English, and major global languages with cultural context understanding |

### The Killer Pitch

> *"Dataminr tells you when the riot starts. We tell you which neighborhood will reach a tipping point 3 months in advance."*

---

## 🚧 Current Progress (Proof of Concept Stage)

**Status:** Working prototype demonstrating proof-of-concept for key pipeline elements. The system is functional but not production-ready — we're validating core technical capabilities and gathering user feedback to refine product-market fit.

**What "Proof of Concept" Means:**
- ✅ Core technical feasibility proven (scraping, scoring, visualization all working)
- 🟡 Product still needs refinement (UX, predictive models, district-level granularity)
- 🟡 Not yet optimized for scale (can handle 100 cities, targeting 1,000+)
- 🟡 Scoring engine is basic (foundational algorithm in place, needs sophistication)

### ✅ What's Working Now

| Component | Status | Description | Technical Details |
|-----------|--------|-------------|-------------------|
| **🌐 3D Globe Interface** | ✅ Functional | WebGL-powered 3D globe displaying Civic Health Index scores for 108 cities. Users can rotate, zoom, and click cities for detailed 12-dimension scores. Interactive leaderboard, search & filter functionality. | Three.js rendering, real-time data updates, ~108 cities with scores |
| **📊 Universal Scraping Engine** | ✅ Operational | FastAPI backend ingests from hundreds of news sources (Reuters, BBC, NYTimes, The Guardian, Bloomberg) and Reddit communities simultaneously. Multi-threaded processing with rate limiting and retry logic. | FastAPI + Uvicorn, concurrent job processing, Reddit API integration, ~100 cities operational |
| **🤖 AI Scoring Engine** | 🟡 In Development | Foundational proprietary scoring engine for 12 dimensions currently operational. Uses LLM-based semantic analysis to score city sentiment across safety, housing, economy, governance, transport, environment, health, culture, education, technology, community, and cost of living. Research ongoing for weighting algorithms and dimension interdependencies. | OpenAI GPT-4 for semantic analysis, custom prompt engineering, basic aggregation logic |
| **📈 Corporate Dashboard (Prototype)** | 🟡 Basic Demo | Early prototype demonstrating core concepts: portfolio selection (organize cities by region/purpose), dimension filtering (select specific civic dimensions to monitor), and grounded AI chat that answers questions using only scraped data (no hallucinations). Basic 12-dimension sample visualization included. | HTML/CSS/JS prototype, basic portfolio logic, AI chat with RAG (Retrieval-Augmented Generation) |
| **🗄️ Data Pipeline (v3)** | ✅ Functional | End-to-end pipeline: scrape → deduplicate → translate → score → output JSON. Handles data from 380,000+ potential legal sources. Processes individual cities in ~2-5 minutes each depending on data volume. | Python-based, LangChain for LLM orchestration, SQLite for job queue, JSON output format |

### 🔨 What's In Active Development (Q1-Q3 2026)

| Feature | Target | Current Status | What Needs to Happen |
|---------|--------|----------------|----------------------|
| **District-Level Analysis** | Q1 2026 | Currently city-level only; expanding to district granularity | Build neighborhood/district taxonomy for each city, modify scoring to aggregate at district level, validate with local knowledge experts |
| **Predictive Engine v1** | Q1 2026 | Developing 30/60/90-day sentiment projection models | Train time-series models on historical data, establish confidence intervals, validate with backtesting against known events |
| **12-Dimension Scoring Methodology** | Q1-Q2 2026 | Foundational scoring operational; refining weighting algorithms | Conduct interviews for quantified insights, test different aggregation methods, validate with domain experts, establish industry benchmark standards |
| **Intelligent Alerts** | Q2 2026 | Email-based threshold monitoring for selected cities/districts | Build notification service, create customizable threshold system, integrate with dashboard UI, test delivery reliability |
| **Custom Intelligence Reports** | Q2 2026 | Automated 20+ page PDF report generation with predictive analytics | Build report templates, integrate charts/visualizations, create AI chatbot for scope definition, establish QA process, fast turnaround pipeline (3-5 days) |
| **Multi-Location Comparison** | Q2 2026 | Side-by-side dashboard analysis across unlimited cities | Build comparison UI, create normalization logic for fair comparison, add export functionality, enable custom groupings |
| **API Access** | Q3 2026 | RESTful API for real-time data access | Design API schema, build authentication system, create rate limiting, write documentation, establish SLAs |

### 🎯 What's Already Been Accomplished (POC Milestones Hit)

**✅ Technical Feasibility Proven:**
- Successfully scraped and analyzed 108 cities with full 12-dimension scoring
- Built functional 3D globe visualization that renders in browser with smooth interaction
- Created grounded AI chat system that answers questions without hallucinations (RAG architecture)
- Processed thousands of documents through the scoring pipeline with consistent results

**✅ Product Concepts Validated:**
- Demonstrated that civic health can be quantified into 12 distinct dimensions
- Proved that geo-centric architecture (select location → get all sentiment) is technically feasible
- Validated that LLM-based semantic analysis can detect implicit sentiment better than keyword matching
- Showed that portfolio management approach (organize cities by investment logic) resonates with target users

**✅ Infrastructure Foundations Built:**
- FastAPI backend with job queue system operational
- React frontend with component library for dashboards
- Data pipeline architecture (scrape → score → output) functioning end-to-end
- Multi-source ingestion (news + social) working concurrently

**✅ Market Research Completed:**
- Identified primary beachhead markets (commercial real estate, retail site selection)
- Validated pain points through industry research and expert interviews
- Confirmed competitive gaps (geo-centric architecture, setup tax barrier)
- Established pricing tiers based on comparable SaaS products

### 🔬 Key Technical Innovations Implemented

**1. Semantic AI vs. Keyword Matching**
- **What We Built:** LLM-powered semantic analysis that understands context, sarcasm, implicit sentiment, and local slang
- **Why It Matters:** Traditional tools miss phrases like "this neighborhood used to be nice" (implicit negative) or "perfect for money laundering" (sarcastic negative)
- **Current Status:** ✅ Operational — Successfully detects nuanced sentiment including Cantonese colloquialisms and HK slang

**2. Geo-Centric Architecture**
- **What We Built:** Location-first data model — select coordinates/district, get *all* relevant sentiment regardless of entity mentions
- **Why It Matters:** Competitors like Brandwatch require complex boolean queries per location. We eliminate the "Setup Tax" — click a district, see all 12 dimensions instantly.
- **Current Status:** ✅ Operational — 108 cities with one-click access to full sentiment profiles

**3. Full Audit Trail (Anti-Hallucination)**
- **What We Built:** Every AI-generated score links back to specific source articles with direct quotes
- **Why It Matters:** Investment committees won't approve multi-million dollar deals on "black box" alerts. Our system is audit-ready.
- **Current Status:** ✅ Operational — RAG (Retrieval-Augmented Generation) architecture ensures grounded outputs

**4. Multi-Lingual NLP with Cultural Context**
- **What We Built:** Native processing of Cantonese, Mandarin, English, and major global languages — not just translation, but cultural context understanding
- **Why It Matters:** Tools that merely translate miss idioms, local slang (e.g., HK Cantonese expressions), and culturally-specific sentiment markers
- **Current Status:** ✅ Operational for English/Cantonese/Mandarin — Expanding to more languages in Q1 2026

**5. 12-Dimension Standardization Framework**
- **What We Built:** Proprietary taxonomy that breaks "civic health" into 12 measurable dimensions (Safety, Housing, Economy, Governance, Transport, Environment, Health, Culture, Education, Technology, Community, Cost of Living)
- **Why It Matters:** Enables apples-to-apples comparison across cities/countries — a standardized "FICO Score" for locations
- **Current Status:** 🟡 Foundational algorithm operational — Refining weighting methodology through Q1-Q2 2026

### 📊 Current Data Coverage (As of January 2026)

**Geographic Coverage:**
- **Cities:** 108 operational with full 12-dimension scoring, expanding to 1,000+ major global cities (Q1 2026 target)
- **Regions:** Currently covers major cities across North America, Europe, Asia-Pacific, Latin America, and select Middle Eastern/African cities
- **Granularity:** City-level scoring operational; district-level scoring in development (Q1 2026)

**Data Sources (Current):**
- **News Outlets:** Hundreds of outlets including major wire services (Reuters, AP, AFP), global newspapers (NYTimes, BBC, The Guardian, Bloomberg, SCMP), and regional/local publications
- **Social Platforms:** Reddit (operational with full API access), X/Twitter and Weibo integration planned (Q1 2026)
- **Coverage Depth:** Currently ~100-500 documents per city per analysis cycle
- **Update Frequency:** On-demand processing (2-5 minutes per city); transitioning to daily automated updates

**Data Sources (Planned — Q1 2026):**
- **Tier 1 (News):** GDELT Project (300,000+ sources, free), NewsAPI (80,000+ sources, HK$3,500/mo), Government Open Data portals
- **Tier 2 (Social):** Reddit Data API (~HK$7,800/mo at scale), X/Twitter API (HK$780-3,900/mo)
- **Tier 3 (Regional Forums):** HKGolden, PTT, 2ch, etc. (partnership-based)
- **Total:** 380,000+ legally licensed sources globally

**Multi-Lingual Processing:**
- **Operational Languages:** English (primary), Cantonese, Mandarin
- **In Development:** Major global languages and regional dialects with cultural context understanding
- **Special Capabilities:** HK slang detection, colloquial Cantonese processing, semantic understanding (not just keyword matching)

**Historical Data:**
- **Current:** Limited historical data (testing phase)
- **Target (Q2 2026):** 5-year rolling archive per city for trend analysis, pattern detection, and predictive modeling

### 🎯 Near-Term Milestones

**Q1 2026 (Current):**
- Expand to 1,000+ cities
- Scale to 380,000+ sources via licensed APIs (GDELT, NewsAPI, Reddit API)
- Develop Predictive Engine v1, solidify 12-dimensional proprietary scoring engine
- Hire BD Lead + Data Engineer
- Conduct interviews for quantified insights

**Q2 2026:**
- Backtesting validation (5-year historical data)
- Corporate Dashboard v1.0 with full functionality
- Custom Report generation testing
- Basic pilot testing (2-3 regions and city clusters)
- Testing pilot success criteria

**Q3 2026:**
- Launch API + Dashboard Beta
- Pilot testing for 10 beta users (startups, SMEs, NGOs)
- Early adopter feedback loop
- Pricing validation & iteration

**Q4 2026:**
- Full commercial availability
- Enterprise sales outreach
- First paid contracts signed
- Target: **10+ enterprise customers, 15+ case studies**

---

## 🏗️ Project Structure

```
Our-City-Health---Sentiment-Project/
│
├── 📊 PITCH DECK & DEMOS
│   ├── JAN20_pitch_deck.html      # Main investor pitch (HKSTP Ideation)
│   ├── modern_map.html            # Interactive 3D globe visualization
│   ├── city_health_dashboard_MASSIVE.html  # Full dashboard demo
│   └── corporate_dashboard.html   # Enterprise dashboard concept
│
├── 🔧 BACKEND (Python)
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py           # FastAPI entry point
│   │   │   ├── models.py         # Pydantic data models
│   │   │   ├── scrape/           # News & Reddit scrapers
│   │   │   ├── score/            # 12-dimension scoring engine
│   │   │   ├── jobs/             # Background job management
│   │   │   └── chat/             # AI chat agent
│   │   └── requirements.txt
│   └── requirements.txt          # Root requirements
│
├── 🖥️ FRONTEND (React + Vite)
│   └── frontend/
│       ├── src/
│       │   ├── App.tsx           # Main React app
│       │   ├── components/       # UI components
│       │   └── api.ts            # Backend API client
│       └── package.json
│
├── 📁 DOCS (GitHub Pages)
│   └── docs/
│       ├── index.html            # Landing page
│       ├── JAN20_pitch_deck.html # Pitch deck (deployed)
│       └── *.png                 # Screenshots
│
├── 🗄️ DATA
│   └── data/
│       ├── latest/               # Latest analysis outputs
│       └── jobs.sqlite           # Job queue database
│
└── 📜 LEGACY (archived)
    └── archive/
        ├── conclusive_scaper_and_analysis_v1.py
        ├── conclusive_scraper_and_analysis_v2.py
        ├── basic_NYT_scraper.py
        ├── basic_reddit_scraper.py
        └── OLD_pitchdeck.html
```

---

## 🚀 Quick Start

### View the Pitch Deck (No Setup Required)

**Live Demo:** [https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/JAN20_pitch_deck.html](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/JAN20_pitch_deck.html)

Or locally:
    ```bash
# Clone and serve
git clone https://github.com/CaydenAuyang/Our-City-Health---Sentiment-Project.git
cd Our-City-Health---Sentiment-Project
    python3 -m http.server 8080

# Open http://localhost:8080/JAN20_pitch_deck.html
```

### Run the Full Stack

**1. Backend (FastAPI + Python)**
```bash
cd backend
pip install -r requirements.txt
./start_backend.sh
# API runs at http://localhost:8000
```

**2. Frontend (React + Vite)**
```bash
cd frontend
npm install
npm run dev
# UI runs at http://localhost:5173
```

### Run the Data Pipeline

**Fast Sample Run (20 cities, ~5 min):**
```bash
python3 conclusive_scaper_and_analysis_v3.py \
  --num_cities 20 \
  --per_source_limit 120 \
  --reddit_pages 3 \
  --reddit_comments 50 \
  --city_docs 200 \
  --out data/latest
```

**Full Run (100 cities, ~2 hours):**
```bash
python3 conclusive_scaper_and_analysis_v3.py \
  --cities_link "https://en.wikipedia.org/wiki/List_of_largest_cities" \
  --num_cities 100 \
  --per_source_limit 500 \
  --reddit_pages 10 \
  --reddit_comments 100 \
  --city_docs 500 \
  --out data/latest
```

---

## 📊 The 12-Dimension Taxonomy

Our proprietary scoring framework measures the holistic health of any city:

| Dimension | What It Measures |
|-----------|------------------|
| **Safety** | Crime perception, policing trust, emergency response |
| **Housing** | Affordability, availability, rental stress |
| **Economy** | Job market, business sentiment, economic optimism |
| **Governance** | Trust in local government, corruption perception |
| **Transport** | Public transit quality, traffic, infrastructure |
| **Environment** | Air quality, green spaces, sustainability |
| **Health** | Healthcare access, public health sentiment |
| **Culture** | Arts, entertainment, community vibrancy |
| **Education** | School quality, access, educational opportunities |
| **Technology** | Digital infrastructure, tech adoption, innovation |
| **Community** | Social cohesion, neighborhood trust, civic engagement |
| **Cost of Living** | Overall affordability, price stress |

Each dimension is individually selectable for deep-dive analysis.

---

## 💼 Product Suite

### 1. Corporate Dashboard (SaaS — HK$1,500/mo to HK$50K/yr)

**The Mission:** Predict, Don't React. The dashboard transforms you from reactive decision-maker to predictive strategist.

**Core Features:**
- **Portfolio Management:** Organize cities into logical groupings ("GBA Expansion Assets", "European Retail Pipeline")
- **12-Dimension Health Scores:** City and district-level granularity across all 12 civic dimensions
- **Intelligent Watchlists & Alerts:** "Notify me if Safety in Hong Kong drops below 50" or "Alert if any district in London sees Housing Affordability drop >10 points"
- **Predictive Analytics Engine:** 30/60/90-day sentiment projections, leading indicator detection, causal attribution
- **Multi-Location Comparison:** Side-by-side analysis across unlimited cities/districts with exportable reports
- **Historical Trend Lines:** 5 years of data per city to identify recovery patterns and predict future shifts

**Use Cases:**
- Pre-acquisition due diligence for real estate developers
- Store location shortlisting for retail expansion teams
- Portfolio risk monitoring for property investors
- Duty of care assessments for corporate travel/security

---

### 2. Custom Intelligence Reports (Enterprise — HK$50K+/yr)

**The Mission:** Forecast-First Intelligence. Custom Intelligence Reports aren't post-mortems — they're forecasts.

**Report Types:**

**A) Predictive Reports** (Future-focused)
- **Market Entry Forecasts:** 12-month trajectory predictions with confidence intervals for target cities
- **Comparative Advantage Analysis:** "Should we enter Jakarta or Manila first? Which will have better civic stability in 18 months?"
- **30/60/90-Day Projections:** Short-term sentiment trend forecasts for immediate decision support

**B) Analytical Reports** (Explanatory)
- **Crisis Root Cause Analysis:** "What caused Safety to drop 15 points in Lagos in Q3?"
- **Trajectory Benchmarking:** Which cities are accelerating vs. stalling? Peer city comparisons.
- **Issue Deep-Dives:** Custom analysis on specific dimensions (e.g., "Housing Affordability Trends in Top 20 APAC Cities")

**Delivery:**
- 20+ page PDF reports with full citations
- AI-assisted chatbot for scope definition and success criteria clarification
- Fast turnaround (3-5 business days)
- Full audit trail — every insight linked to source data

---

### 3. API Firehose & Data License (HK$100K+/yr)

**For:** Quantitative trading firms, alternative data funds, enterprise data teams

**Access:**
- Real-time JSON feed for 1,000+ cities
- 5-year historical data archive
- Unlimited API calls
- District-level granularity
- Raw sentiment scores + metadata
- Custom webhooks for real-time alerts

---

## 🏆 Competitive Positioning

### What Makes Us Different

| Dimension | Our Competitors | Our City Health |
|-----------|----------------|-----------------|
| **Architecture** | **Entity-Centric** (Brandwatch) or **Government-Focused** (Zencity) | **Geo-Centric** — Select a location, get *all* sentiment regardless of entity mentions |
| **Insight Level** | Event-level (Dataminr), Store-level (Placer.ai) | **District and City-level** — Granular enough for micro-market analysis |
| **Audit Trail** | Black box (no citations) or brand-focused | **Full transparency** — Every score links to source articles |
| **Time Horizon** | Real-time alerts only OR historical-only consultancy reports | **Real-time + Historical + Predictive** (30/60/90-day projections) |
| **Use Case** | Brand monitoring, government policy, event detection | **Private sector location risk** — Site selection, operational monitoring, community risk |

### The Economic Barrier We Solve

**The "Setup Tax":** Tools like Zencity and Brandwatch require complex boolean queries per city, per language. To track "Civic Stability" across 50 global assets, you need a ~HK$620K/year analyst just to maintain queries.

**Our Advantage:** Pre-built geo-centric architecture. You click "Hong Kong → Kowloon District" and immediately see all 12 dimensions. No query engineering required.

---

## 🎯 Target Customers — Focused Go-to-Market

**Our Strategic Approach:** We're launching with industries where "Community Sentiment" is a multi-million dollar blind spot and existing tools have clear gaps. This focused go-to-market strategy allows us to prove product-market fit before expanding to additional verticals.

**Our Sweet Spot:** Medium-sized enterprises and larger SMEs who need sophisticated location intelligence but can't afford to build massive in-house data teams or expensive "Setup Tax" tools like Zencity or Brandwatch.

### PRIMARY ANCHOR MARKETS (Year 1)

**1. Commercial Real Estate — Land Acquisition Teams**
- **Target:** VP of Development, Land Acquisition Managers
- **Pain Point:** Buy land in major city → community opposition → protests → lawsuits → 3-year delay → **lose 15-25% of project value annually** in carry costs
- **Our Value:** Quantify "Entitlement Risk" before bidding on land. Identify if neighborhood has low community cohesion, low governance trust, or active housing affordability campaigns.
- **Use Cases:** Pre-bid community screening, risk-adjusted underwriting, entitlement timeline forecasting

**2. Retail & QSR Site Selection**  
- **Target:** Site Selection Managers, Regional Expansion Teams
- **Pain Point:** Open store in trending-down neighborhood → significant lost sales → **joins 30-50% that fail within 3 years globally**
- **Our Value:** Overlay "Safety Sentiment & Cultural Vibrancy" scores on top of Placer.ai traffic data to explain trends and predict future performance
- **Use Cases:** Pre-lease due diligence, market entry sequencing, portfolio optimization

### TIER 2 — SCALE MARKETS (Year 2-3)

**3. P&C Insurance — Parametric Risk Modeling**
- **Pain Point:** If "Governance Trust" collapses in a region, riot risk goes up. Mid-sized domestic insurers need predictive civic signals but can't afford proprietary platforms.
- **Our Value:** Parametric triggers based on real-time sentiment scores to adjust reserves and pricing.

**4. Government & Smart City — Policy Impact Measurement**
- **Pain Point:** Real-time civic sentiment to understand policy effectiveness, identify emerging issues before escalation
- **Our Value:** Track trust and satisfaction scores across many dimensions in real-time. Continuous pulse checks vs. expensive annual surveys.

**5. Logistics & Corporate Security — Duty of Care**
- **Pain Point:** Static risk reports miss real-time labor unrest or anti-foreign sentiment. Existing government-backed tools only send emergency high-risk alerts, not the soft signals that predict escalation.
- **Our Value:** Live alerts for shipping hubs and travel destinations. Detect "soft signals" before hard disruptions.

### FUTURE HORIZON — POST-TRACTION

**6. Quantitative Trading (Hedge Funds)**
- **Target:** Mid-size macro funds ($100M-$500M AUM) that can't afford massive alternative data infrastructure
- **Our Value:** Municipal bonds, EM currencies, commodity trading based on civic stability trends

---

### 🇭🇰 Hong Kong & GBA as Launch Market

We're positioning Hong Kong as our beachhead market, leveraging the HKSTP ecosystem to target **local SMEs expanding overseas**.

**Why Hong Kong:**
- **Built-in Network:** Direct access to HK/GBA companies in HKSTP's portfolio
- **Expansion Focus:** Many HK companies are expanding to unfamiliar international markets where they lack local intelligence
- **Multi-Lingual Edge:** Our native Cantonese, Mandarin, and English processing is a competitive advantage
- **Proof of Concept:** Easier to validate product-market fit with local early adopters before global scale

**Target Profile:**
- HK-based SMEs and medium enterprises expanding to APAC, Europe, North America
- Companies entering markets where they lack "on-the-ground" intelligence
- Real estate developers, F&B chains, retail brands, insurers looking at overseas opportunities

---

## 🔧 Technical Architecture

### Data Pipeline
```
[380,000+ Sources] → [Ingestion] → [Predictive Intelligence Engine] → [Outputs]
     │                    │                    │                         │
     ├─ GDELT (Free)      ├─ NER              ├─ 12-Dim Scoring         ├─ API
     ├─ NewsAPI ($449/mo) ├─ Deduplication    ├─ Causal Analysis        ├─ Dashboard
     ├─ Reddit API        ├─ Translation      ├─ Trend Prediction       └─ Reports
     └─ Gov Open Data     └─ Fairness Norm    └─ 5-Year Archive
```

### Tech Stack
- **Backend:** Python 3.11+, FastAPI, SQLite, LangChain
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS
- **3D Visualization:** Three.js / WebGL
- **LLM:** GPT-4 / Claude for semantic analysis
- **Deployment:** GitHub Pages (pitch), Vercel/Railway (API)

### Data Infrastructure: Scalable & Compliant

Our data acquisition strategy prioritizes **legal, licensed sources** that scale to hundreds of thousands of feeds while maintaining full compliance.

| Tier | Source | Coverage | Cost (HKD) |
|------|--------|----------|------------|
| **Tier 1: News Intelligence** | GDELT Project | 300,000+ global news sources, 100+ languages | Free |
| **Tier 1: News Intelligence** | NewsAPI | 80,000+ sources with structured metadata | ~HK$3,500/mo |
| **Tier 1: News Intelligence** | Government Open Data | Municipal portals, policy documents | Free |
| **Tier 2: Social Intelligence** | Reddit Data API | Enterprise licensing for commercial use | ~HK$1.87/1K calls (~HK$7,800/mo at scale) |
| **Tier 2: Social Intelligence** | X/Twitter API | Basic to Pro tier access | HK$780-3,900/mo |
| **Tier 3: Regional Forums** | HKGolden, PTT, 2ch, etc. | Regional community forums | Partnerships (potentially) |
| **TOTAL** | **380,000+ sources** | **Legally licensed, globally compliant** | **HK$3,900-15,600/mo** |

---

## 📅 12-Month Execution Roadmap (2026)

### Q1 2026: Scale & Team
- ✅ Expand to **1,000+ cities**
- ✅ Scale to **380,000+ sources** via licensed APIs
- ✅ Develop **Predictive Engine v1**, solidify 12-dimensional proprietary scoring engine
- ✅ Hire BD Lead + Data Engineer
- ✅ Interviews for quantified insights
- **Goal:** Initial testing of predictive risk models

### Q2 2026: Product Development
- ✅ **Backtesting Validation** (5-year historical data)
- ✅ **Corporate Dashboard v1.0** with full watchlist, alerts, and comparison features
- ✅ Custom Report generation testing
- ✅ Solidify predictive analytics capabilities
- ✅ Basic pilot testing (2-3 regions and city cluster) and testing pilot success criteria
- **Goal:** Product-market fit validation

### Q3 2026: Beta Launch
- ✅ Launch **API + Dashboard Beta**
- ✅ Outreach to small organizations
- ✅ Early adopter feedback loop
- ✅ Pricing validation & iteration
- ✅ Pilot testing for **10 beta users** (startups, SMEs, NGOs)
- **Goal:** 10 beta users with active feedback loops

### Q4 2026: Commercial Launch
- ✅ **Full commercial availability**
- ✅ Enterprise sales outreach
- ✅ First paid contracts signed
- **Target:** **10+ enterprise customers, 15+ case studies**

---

## 📁 Key Files

| File | Description |
|------|-------------|
| `JAN20_pitch_deck.html` | Main investor pitch deck (HKSTP Ideation) |
| `conclusive_scaper_and_analysis_v3.py` | Production data pipeline |
| `modern_map.html` | Interactive 3D globe visualization |
| `city_health_dashboard_MASSIVE.html` | Full dashboard with all features |
| `backend/app/main.py` | FastAPI backend entry point |
| `frontend/src/App.tsx` | React frontend entry point |

---

## 🔗 Links

### GitHub Pages (Live Demos)
- **Project Showcase:** [Landing Page](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/)
- **Corporate Dashboard:** [Enterprise Intelligence Dashboard](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/corporate_dashboard.html)
- **3D Globe Map:** [Interactive Global Map](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/modern_map.html)
- **Pitch Deck:** [Investor Pitch](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/JAN20_pitch_deck.html)

### Documentation
- **API Documentation:** [README_API.md](README_API.md)

---

## 👥 Core Team

### Cayden Auyang — Founder & Chief Architect

**Background:**
- **Education:** Hunter College High School (Class of 2025), Gap Year dedicated to Our City Health (2025-2026), Incoming undergraduate (2026)
- **Technical Expertise:** AI/ML engineering, agentic AI workflows, full-stack development, LLM application architecture
- **Research:** Founded Civic AI Group — school-wide initiative (20+ students/advisors) leveraging AI to automate workflows for school faculty and nearby communities (serving 4 departments, 10+ cases)

**The "Super-Dev" Advantage:**
- Expert in modern AI development workflows (Cursor, Claude, GPT-4, LangChain) enabling 5x faster prototyping than traditional development
- Self-developed multiple AI + automation projects including macOS GUI automation agents and browser-based games (FPS to educational)
- Previously built deep analysis programs at Wisers, combining web scraping, LLM analysis, and API bridging for fashion brand market intelligence

**Commitment:** Dedicated gap year (2025-2026) to build Our City Health to commercial launch, then pursuing undergraduate studies while scaling the venture.

**Contact:**
- 📧 Email: caydenauyang@gmail.com
- 📱 Phone: +1 (646) 889-4501 (Primary) | +852 9260 9370 (HK)
- 🔗 LinkedIn: [Connect with Cayden](https://linkedin.com/in/cayden-auyang)
- 💻 GitHub: [@CaydenAuyang](https://github.com/CaydenAuyang)

### Key Advisor

**Alvin Mok** — Chief Information and Data Officer at Select Equity Group (USD $25B+ AUM)

**Background:**
- Former Global Head of Platform and Insights at Orbis Investments (9 years)
- Former Engagement Manager at McKinsey & Company (specialized in high tech, travel, infrastructure for Asia/China markets)
- Education: Harvard Business School (MBA, Top 5%, Baker Scholar), University of Toronto (BASc Computer Engineering, highest cumulative average in 2003)

**Advisory Role:** Strategic guidance on data infrastructure, alternative data acquisition, AI/ML product development, and institutional investor positioning.

---

## 🤝 Contributing & Collaboration

**We're Open To:**
- 🏢 **Early Adopter Partnerships:** Beta testers from real estate, retail, insurance, or corporate security
- 🎓 **Academic Collaborations:** Urban planning researchers, sentiment analysis experts, social sensing scholars
- 💼 **Strategic Advisors:** Industry veterans in PropTech, location intelligence, alternative data, or civic tech
- 💰 **Investors:** Pre-seed/seed stage VCs and angels interested in SaaS, alternative data, or civic technology

**Not Open Source (Yet):**  
While this repository is public for portfolio demonstration purposes, the core scoring algorithms and data pipelines are proprietary. We may open-source certain components (e.g., visualization tools) in the future after commercial launch.

---

## 📜 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 🎯 Project Status Summary

| Metric | Current State | Target (EOY 2026) |
|--------|---------------|-------------------|
| **Cities Covered** | 108 operational | 1,000+ |
| **Data Sources** | Hundreds (news + Reddit) | 380,000+ (licensed APIs) |
| **Scoring Engine** | Foundational (operational) | Production-grade with predictive models |
| **Dashboard** | Basic prototype | Full SaaS platform |
| **Customers** | 0 (pre-launch) | 10+ enterprise customers |
| **Team Size** | 1 founder + 1 advisor | 3-4 (founder + BD + engineer + contractor) |
| **Revenue** | $0 (pre-revenue) | First contracts signed |

**Last Updated:** January 28, 2026

---

**⭐ If you find this project interesting, please star the repository and share with colleagues in real estate, retail, or urban intelligence!**
