# Our City Health — The Missing Context Layer for Civic Intelligence

> **Predictive Urban Intelligence for Global Decision-Makers**  
> We don't just show you what happened — we explain *why* it happened and predict *what's coming next*.

[![GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-brightgreen)](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/JAN20_pitch_deck.html)

---

## 🎯 What We Do

**Our City Health** is a predictive civic intelligence platform that transforms unstructured global data into a standardized "Civic Health Index" for 1,000+ cities worldwide.

**The Problem:**  
Enterprises already pay millions for alerts (Dataminr), foot traffic (Placer.ai), and financial data (Bloomberg). But they have **zero data on how people feel about the neighborhood**. That "Sentiment Gap" is why stores fail in trending-down districts and why travel advisories come too late.

**Our Solution:**  
We don't replace existing tools — we **complete them**. By scoring 12 dimensions of civic health (Safety, Housing, Economy, Governance, Transport, etc.) from tens of thousands of sources, we provide:

- **Causal "Why" Analysis** — Not just "Safety dropped 8 points" but *why* (340% increase in housing protest coverage)
- **Trend Prediction Models** — 30/60/90-day projections based on 5 years of historical patterns
- **Leading Indicators** — Know which neighborhoods are ready to deteriorate 3-6 months in advance

### The Killer Pitch

> *"Dataminr tells you when the riot starts. We tell you which neighborhood is ready to explode 3 months in advance."*

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

## 💼 Products

### 1. Corporate Dashboard (B2B SaaS)
- **Portfolio Management:** Organize cities into logical groupings (APAC Retail, European Logistics)
- **Predictive Analytics:** Causal attribution, trend forecasting, leading indicators
- **Intelligent Alerts:** "Notify me if Safety in Lagos drops below 60"
- **Multi-City Comparison:** Side-by-side analysis with exportable reports

### 2. Custom Intelligence Reports (Enterprise)
- **Market Entry Forecasts:** 12-month trajectory predictions with confidence intervals
- **Crisis Prediction & Recovery:** Causal chain analysis + recovery timeline forecasts
- **Trajectory Benchmarking:** Which cities are accelerating vs. stalling?

### 3. API Firehose (Data License)
- Real-time JSON feed for all 1,000+ cities
- 5-year historical data access
- Unlimited API calls

---

## 🎯 Target Customers

**Our sweet spot:** Medium-sized enterprises and larger SMEs who need sophisticated intelligence but can't afford to build massive in-house data teams.

| Vertical | Target Segment | Example Companies |
|----------|----------------|-------------------|
| **Mid-Size Macro Funds** | $100M-$500M AUM | EM funds, municipal bond specialists, family offices |
| **FMCG & Food** | Regional expansion | Vitasoy, Maxim's, Café de Coral, Lee Kum Kee |
| **Mid-Size P&C Insurers** | Domestic/regional | FWD, regional P&C carriers, specialty insurers |
| **Corporate Security** | Duty of Care | HR/mobility teams, travel management, executive protection |

### 🇭🇰 Hong Kong Launch Market

We're targeting Hong Kong companies first — they're already in HKSTP's ecosystem:
- **HK Asset Managers:** Value Partners, CSOP, Hang Seng Investment
- **HK F&B/FMCG:** Vitasoy, Maxim's, Dairy Farm, Lee Kum Kee
- **HK Insurers:** FWD, AIA (HK ops), HSBC Insurance
- **HK Corporates:** Swire, Jardines, Li & Fung, CK Hutchison

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

### Data Infrastructure Costs
| Tier | Source | Cost |
|------|--------|------|
| Tier 1 | GDELT (300K+ sources) | Free |
| Tier 1 | NewsAPI (80K+ sources) | $449/mo |
| Tier 1 | Government Open Data | Free |
| Tier 2 | Reddit API | ~$0.24/1K calls |
| Tier 2 | X/Twitter API | $100-500/mo |
| **Total** | **380,000+ sources** | **$500-2,000/mo** |

---

## 📅 Roadmap (2026)

| Quarter | Focus | Key Milestones |
|---------|-------|----------------|
| **Q1** | Scale & Team | 1,000+ cities, 10,000+ sources, hire BD + Data Engineer |
| **Q2** | Product Dev | Dashboard v1.0, Custom Report generation, partner validation |
| **Q3** | Commercial Beta | API Beta launch, 10 developer users |
| **Q4** | Revenue | 3 paid enterprise pilots, full commercial availability |

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

- **Live Pitch Deck:** [GitHub Pages](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/JAN20_pitch_deck.html)
- **3D Globe Demo:** [modern_map.html](https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/modern_map.html)
- **API Documentation:** [README_API.md](README_API.md)

---

## 👤 Contact

**Cayden Auyang** — Founder & Architect  
Building the missing context layer for civic intelligence.

---

## 📜 License

MIT License — See [LICENSE](LICENSE) for details.
