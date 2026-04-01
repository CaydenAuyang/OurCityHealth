#!/usr/bin/env python3
"""
Generate a comprehensive PowerPoint pitch deck for Our City Health
Includes 100% of the content from the HTML version
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

# Initialize presentation
prs = Presentation()
prs.slide_width = Inches(10)
prs.slide_height = Inches(7.5)

# Define colors
BG_DARK = RGBColor(10, 15, 20)  # #0a0f14
NEON_GREEN = RGBColor(74, 222, 128)  # #4ade80
WHITE = RGBColor(255, 255, 255)
GRAY_LIGHT = RGBColor(156, 163, 175)  # gray-400
GRAY_MED = RGBColor(107, 114, 128)  # gray-500

def add_title_slide(title, subtitle, tagline=""):
    """Add a title slide"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG_DARK
    
    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(9), Inches(1))
    title_frame = title_box.text_frame
    title_frame.text = title
    title_frame.paragraphs[0].font.size = Pt(60)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = WHITE
    title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # Subtitle
    subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.7), Inches(9), Inches(0.6))
    subtitle_frame = subtitle_box.text_frame
    subtitle_frame.text = subtitle
    subtitle_frame.paragraphs[0].font.size = Pt(24)
    subtitle_frame.paragraphs[0].font.color.rgb = GRAY_LIGHT
    subtitle_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # Tagline
    if tagline:
        tagline_box = slide.shapes.add_textbox(Inches(0.5), Inches(4.5), Inches(9), Inches(0.5))
        tagline_frame = tagline_box.text_frame
        tagline_frame.text = tagline
        tagline_frame.paragraphs[0].font.size = Pt(18)
        tagline_frame.paragraphs[0].font.color.rgb = NEON_GREEN
        tagline_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

def add_content_slide(section_label, title, content_blocks):
    """Add a content slide with multiple text blocks"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG_DARK
    
    # Section label
    label_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(9), Inches(0.3))
    label_frame = label_box.text_frame
    label_frame.text = section_label.upper()
    label_frame.paragraphs[0].font.size = Pt(11)
    label_frame.paragraphs[0].font.bold = True
    label_frame.paragraphs[0].font.color.rgb = NEON_GREEN
    
    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.8), Inches(9), Inches(0.6))
    title_frame = title_box.text_frame
    title_frame.text = title
    title_frame.paragraphs[0].font.size = Pt(32)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = WHITE
    
    # Content blocks
    y_pos = 1.6
    for block in content_blocks:
        text_box = slide.shapes.add_textbox(Inches(0.5), Inches(y_pos), Inches(9), Inches(0.8))
        text_frame = text_box.text_frame
        text_frame.word_wrap = True
        text_frame.text = block
        for paragraph in text_frame.paragraphs:
            paragraph.font.size = Pt(14)
            paragraph.font.color.rgb = GRAY_LIGHT
            paragraph.space_before = Pt(6)
        y_pos += 0.85

def add_bullet_slide(section_label, title, subtitle, bullets):
    """Add a slide with bullet points"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG_DARK
    
    # Section label
    label_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(9), Inches(0.3))
    label_frame = label_box.text_frame
    label_frame.text = section_label.upper()
    label_frame.paragraphs[0].font.size = Pt(11)
    label_frame.paragraphs[0].font.bold = True
    label_frame.paragraphs[0].font.color.rgb = NEON_GREEN
    
    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.8), Inches(9), Inches(0.5))
    title_frame = title_box.text_frame
    title_frame.text = title
    title_frame.paragraphs[0].font.size = Pt(32)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = WHITE
    
    # Subtitle
    if subtitle:
        subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(9), Inches(0.3))
        subtitle_frame = subtitle_box.text_frame
        subtitle_frame.text = subtitle
        subtitle_frame.paragraphs[0].font.size = Pt(13)
        subtitle_frame.paragraphs[0].font.color.rgb = GRAY_MED
    
    # Bullets
    y_start = 1.9 if subtitle else 1.5
    bullet_box = slide.shapes.add_textbox(Inches(0.8), Inches(y_start), Inches(8.4), Inches(5))
    text_frame = bullet_box.text_frame
    text_frame.word_wrap = True
    
    for i, bullet in enumerate(bullets):
        if i > 0:
            text_frame.add_paragraph()
        p = text_frame.paragraphs[i]
        p.text = bullet
        p.level = 0
        p.font.size = Pt(14)
        p.font.color.rgb = GRAY_LIGHT
        p.space_after = Pt(12)


# Slide 1: Title
add_title_slide(
    "Our City Health",
    "Geo-Centric Location Intelligence for Capital Allocation Decisions",
    "1,000+ cities. 380,000+ sources. 12 dimensions. One platform."
)

# Slide 2: Key Summary
add_content_slide(
    "Key Summary",
    "The Missing Context Layer",
    [
        "Real estate developers and retail site selection teams have mastered the Financial Stack and the Physical Stack. But the Social Stack remains largely unmeasured.",
        "They assess community sentiment by manual scouting of the district, like attending town hall meetings — a '1990s workflow' for billion-dollar decisions.",
        "PITCH LINE: 'Dataminr tells you when the riot starts. We tell you which neighborhood is ready to reach a tipping point 3 months in advance.'",
        "Great tools exist for Marketing (Brandwatch) and Government (Zencity). But their architecture doesn't fit private sector location risk. Brandwatch is Entity-Centric (tracks keywords). We are Geo-Centric (track locations). We fill this gap with a geo-centric, pre-built 'Civic Health Index' — giving developers and operators the ugly truth about a location before they invest."
    ]
)

# Slide 3: The Problem - Entitlement Cliff
add_bullet_slide(
    "Problem",
    "The Entitlement Cliff",
    "70% of housing projects face community opposition delays costing HK$6-8M per year",
    [
        "THE HARD STAT: Real estate developers conduct exhaustive physical due diligence (soil tests, traffic studies, architectural feasibility) but systematically miss the 'Social Layer' — community sentiment, political risk, and local opposition. Research shows 70% of housing projects face entitlement delays due to community opposition, costing $6-8M per year of delay.",
        "CURRENT SOLUTION: Developers use CoStar and Esri for demographics and foot traffic. Brandwatch tracks brand mentions (entity-centric). But to assess community sentiment, teams rely on manual scouting — attending town hall meetings, talking to local officials. It's a 1990s workflow for billion-dollar decisions.",
        "OUR SOLUTION: Run a 'Civic Health Check' across 12 dimensions for the specific city or district to quantify Entitlement Risk before bidding on the land. With 5 years of historical data, identify patterns that predict community resistance. Know if a community will fight your project before you buy the land."
    ]
)

# Slide 4: The Data Freshness Gap
add_bullet_slide(
    "Problem",
    "The Data Freshness & Context Gap",
    "Organizations manage billions using data that is broken in three ways: Latency, Context, and Trust",
    [
        "LATENCY TAX: Organizations rely on quarterly reports or census data (24+ months lag). By the time they react, the market has shifted. Result: Bad data costs organizations $12.9M annually (Gartner).",
        "CONTEXT GAP: Tools like Placer.ai show 'foot traffic is down 10%' but cannot explain why. Is it crime? Economy? Weather? Without the 'why,' executives cannot act. LLM Chatbots generate fresh text but lack semantic grounding, hallucinate facts, and have no audit trail.",
        "OUR SOLUTION: Real-time + 5-year historical data with semantic AI ingestion. We don't just track 'what' (alerts) or 'where' (traffic). We explain 'why' with district-level granularity across 12 civic health dimensions, with full audit trails linking every score to specific sources."
    ]
)

# Slide 5: 3-Stack Gap Analysis
add_bullet_slide(
    "Problem",
    "The Developer/Retailer Tech Stack — And What's Broken",
    "Great civic intelligence tools exist — but their architecture doesn't fit private sector location risk",
    [
        "PHYSICAL STACK (Placer.ai, CoStar, Esri): Tracks foot traffic, demographics, property data. → Gap: Tells you 'traffic is down' but not why. Quantitative only.",
        "FINANCIAL STACK (Bloomberg, Refinitiv): Credit ratings, economic indicators, municipal bonds. → Gap: City-level only. No district granularity. No sentiment.",
        "SOCIAL LAYER (Brandwatch, Zencity): Brandwatch tracks entity-centric brand mentions. Zencity tracks government policy sentiment. → Gap: Architecture mismatch — not built for geo-centric location risk.",
        "OUR CITY HEALTH: We fill the Social Stack gap with geo-centric, district-level civic health intelligence. Pre-built 12-dimension taxonomy. No setup tax. Built for capital allocation decisions."
    ]
)

# Slide 6: Proposed Solution - Architecture
add_bullet_slide(
    "Proposed Solution",
    "Standardized Engine for Civic Intelligence",
    "From 380,000+ sources → 12-dimension scores → Actionable intelligence",
    [
        "INGESTION LAYER (380,000+ Sources): Global News (Reuters, AP, AFP, regional papers), Social Platforms (Reddit, X, local forums), Government Portals & Municipal Data, Review Sites (Google, Yelp), Blogs, Newsletters, Telegram Channels.",
        "THE ENGINE (Proprietary v3 Pipeline): 1) Named Entity Recognition (City/District tagging), 2) Fairness Normalization (balanced sampling per city), 3) Semantic Ingestion (LLM-powered scoring across 12 dimensions), 4) Audit Trail (full source citations).",
        "OUTPUT: JSON API (raw data for quants), Corporate Dashboard (real-time scores, alerts, comparisons), Custom Intelligence Reports (20+ page PDFs with predictive analytics).",
        "SEMANTIC EDGE: Traditional tools use rigid keyword filters ('crime,' 'safety'). We use semantic AI to catch implicit sentiment, sarcasm, local slang, complaints without obvious keywords, AND leverage geo-centric architecture — select coordinates, capture ALL sentiment about that location."
    ]
)

# Slide 7: 12-Dimension Taxonomy
add_bullet_slide(
    "Proposed Solution",
    "12-Dimension Civic Health Taxonomy",
    "Holistic assessment at city AND district level — no tool measures Community Cohesion or Cultural Vibrancy for private sector",
    [
        "ESSENTIALS: Safety (crime, violence, policing), Housing (affordability, availability, stability), Economy (jobs, business climate, sentiment), Governance (trust, corruption, transparency), Transport (infrastructure, congestion, reliability), Environment (air quality, climate resilience).",
        "LIFESTYLE: Healthcare (access, quality, satisfaction), Culture (arts, vibrancy, events, identity), Education (schools, universities, access), Technology (digital infrastructure, innovation), Community (cohesion, trust, engagement), Cost of Living (affordability index).",
        "UNIQUENESS: No commercial tool tracks 'Cultural Vibrancy' or 'Community Cohesion' for private sector capital allocation. We are 'ZenCity for Private Enterprise' — standardized civic health intelligence across all 12 dimensions, with district-level granularity for hyper-local insights."
    ]
)

# Slide 8: Corporate Dashboard
add_bullet_slide(
    "Proposed Solution",
    "Corporate Dashboard — Real-Time Intelligence HQ",
    "Track unlimited cities and districts. Predict risks before they materialize.",
    [
        "PORTFOLIO MANAGEMENT: Organize assets by geography ('GBA Portfolio,' 'European Expansion'). Each portfolio displays aggregate health scores and trending dimensions at city/district level.",
        "INTELLIGENT WATCHLISTS & ALERTS: Set custom thresholds ('Alert if Housing Stability < 50 in District X'). Email/Dashboard/Report notifications when scores cross thresholds or anomalies detected.",
        "MULTI-LOCATION COMPARISON: Compare multiple cities and districts side-by-side across all 12 dimensions. Identify which location offers the best risk-adjusted opportunity.",
        "PREDICTIVE ANALYTICS ENGINE: With 5 years of historical data per city/district, identify patterns that predict future shifts. Connect to Custom Intelligence Reports for deeper analysis. Example: 'What leading indicators preceded the last 3 economic sentiment drops in Kuala Lumpur? Will District Y face similar trajectory?'"
    ]
)

# Slide 9: Custom Intelligence Reports
add_bullet_slide(
    "Proposed Solution",
    "Custom Intelligence Reports — Deep-Dive Analysis",
    "Two report types: Predictive + Analytical. 20+ pages. Full citations. 5-7 day turnaround.",
    [
        "PREDICTIVE REPORTS: 1) Market Entry Forecast (assess city/district readiness for new project), 2) Trajectory Benchmarking (compare recovery timelines across peer cities/districts). Use Case: 'Should we enter District X in Jakarta? Compare against similar markets.'",
        "ANALYTICAL REPORTS: Crisis/Event Analysis (what happened and why sentiment shifted), Recovery Timeline Mapping (how long until city/district recovers to baseline). Use Case: 'Tokyo had protests last quarter. What dimensions degraded? When will it recover?'",
        "DELIVERY: AI Chatbot-guided scope definition → Our team conducts analysis → 20+ page PDF report with full citations, historical trends, peer comparisons, and actionable recommendations. 5-7 day turnaround.",
        "AUDITABILITY: Every claim in the report links back to specific sources. No hallucinations. No 'black box.' Full transparency for audit-ready decision-making."
    ]
)

# Slide 10: Current Progress
add_bullet_slide(
    "Proposed Solution",
    "Current Progress — Proof of Concept",
    "Prototype demonstrates select elements. Architecture validated. Ready to scale.",
    [
        "INTERACTIVE 3D GLOBE INTERFACE: Visualize 100+ cities with live data ingestion network. Goal: Enable zooming into district level, displaying scores for all 12 dimensions at district-level granularity.",
        "CORPORATE INTELLIGENCE DASHBOARD: Sample interface demonstrating custom portfolios, alerts, and basic multi-city comparisons. Goal: Add district-level tracking, predictive analytics, and full multi-location comparison with PDF exports.",
        "UNIVERSAL SCRAPING ENGINE: Prototype scraping hundreds of news outlets and Reddit. Goal: Scale to 380,000+ sources (news APIs, social platforms, regional forums, government portals) with semantic ingestion and fairness normalization.",
        "STATUS: This is a prototype demonstrating POC for select elements. Scaling to 1,000+ cities with 380,000+ sources and full predictive analytics capabilities will require compute resources, architectural refinements, and team expansion."
    ]
)

# Slide 11: Market Opportunity
add_content_slide(
    "Market Opportunity",
    "Commercial Risk Intelligence",
    [
        "TAM (Total Addressable Market): $34 Billion — Global Real Estate & Retail Analytics Market (Grand View Research, 2025).",
        "SAM (Serviceable Addressable Market): $8.2 Billion — APAC & North America Site Selection Tools & Location Intelligence Platforms.",
        "SOM (Serviceable Obtainable Market): $120 Million — Year 3 Target. Focus: Mid-size developers (overseas expansion), regional F&B chains, domestic P&C insurers, government smart city initiatives.",
        "BEACHHEAD: Real Estate (Land Acquisition Teams) + Retail (Site Selection Committees). These customers have the highest pain (multi-million dollar mistakes) and the budget to pay for solutions."
    ]
)

# Slide 12: Target Customers - Primary
add_bullet_slide(
    "Market Opportunity",
    "Target Customers — Prioritized",
    "Starting with Physical Asset Owners, expanding to Insurance, Government, and future Financial Markets",
    [
        "TIER 1 — PRIMARY ANCHOR: Commercial Real Estate (Land Acquisition Teams). Pain: Entitlement Risk & NIMBY Opposition. 70% of housing projects face delays costing $6-8M/year. Current Solution: CoStar/Esri (demographics only), Brandwatch (brand-focused, not location-focused), manual town hall meetings. Our Value: Run a 'civic health check' across 12 dimensions for the specific city or district to quantify Entitlement Risk before bidding.",
        "TIER 1 — GROWTH MARKET: Retail & QSR Site Selection (Regional F&B Chains, CPG International Expansion). Pain: Site Selection Failure. Retailers lose $209,317/month from a bad store location. 41% of retail businesses fail within first 5 years, often due to poor site selection. Current Solution: Placer.ai (foot traffic only), Brandwatch (brand mentions, not location sentiment), manual 'site walks.' Our Value: Run a 'civic health check' across 12 dimensions for the specific city or district. Explain why foot traffic trends change. Predict which districts will outperform."
    ]
)

# Slide 13: Target Customers - Scale Markets
add_bullet_slide(
    "Market Opportunity",
    "Target Customers — Scale Markets",
    "Insurance, Logistics/Corporate Security, and Government expand addressable market",
    [
        "TIER 2 — SCALE MARKET: P&C Insurance (Domestic Mid-Sized Property & Casualty Insurers). Pain: Parametric Risk Modeling. Insurers need real-time civic health data to adjust premiums dynamically (e.g., if Governance Trust collapses, riot risk increases). Our Value: Live Civic Health Scores for property risk pricing. Track which districts are degrading across Safety, Governance, Environment dimensions.",
        "TIER 2 — SCALE MARKET: Logistics & Corporate Security (CSOs, Supply Chain Directors). Pain: Static risk reports miss real-time labor unrest or anti-foreign sentiment. Our Value: Live risk monitoring for shipping hubs and executive travel destinations. Alert when civic health dimensions (Safety, Governance, Economy) cross thresholds.",
        "TIER 2 — SCALE MARKET: Government & Smart City (Policy Teams, Urban Planners). Pain: Policy impact measurement & benchmarking. Our Value: Measure policy effectiveness in real-time. Identify emerging issues before escalation, and benchmark against peer cities or districts. (Validates product legitimacy for private sector.)",
        "PHASE 2 — FUTURE HORIZON: Quantitative Trading (Hedge Funds, Macro Funds). Pain: Need leading indicators for municipal bonds, currencies, commodities. Our Value: Standardized Civic Health Index as tradeable data feed. Target: Mid-size funds ($100-500M AUM) that cannot afford to build large proprietary datasets."
    ]
)

# Slide 14: Hong Kong Launch Market
add_bullet_slide(
    "Market Opportunity",
    "Hong Kong & GBA as Launch Market",
    "Local SMEs expanding overseas — leveraging HKSTP ecosystem for warm access",
    [
        "THE OPPORTUNITY: Hong Kong and GBA-based small-to-medium enterprises (SMEs) are expanding globally. They need location intelligence for new markets where they lack local knowledge.",
        "OUR ADVANTAGE: These companies are already in the HKSTP ecosystem — providing immediate, warm access to first customers. They trust the HKSTP brand and are actively seeking tools to de-risk international expansion.",
        "USE CASES: HK-based F&B chain expanding to Southeast Asia → Need civic health insights for site selection in Bangkok, Manila, Jakarta. GBA manufacturer evaluating logistics hubs in emerging markets → Need real-time risk monitoring for supply chain stability. Mid-size HK developer exploring overseas land acquisition → Need Entitlement Risk assessment for new cities.",
        "GOVERNMENT ANGLE: Hong Kong government (Innovation and Technology Bureau, Trade and Development Council) seeks tools to support local SMEs' global expansion. Our City Health aligns with 'Smart City Blueprint' and 'Greater Bay Area Development' strategic priorities."
    ]
)

# Slide 15: Competitive Analysis - Table
add_bullet_slide(
    "Competitive Analysis",
    "We Don't Replace — We Complete",
    "Great civic intelligence tools exist, but their architecture doesn't fit private sector location risk",
    [
        "COMPARISON TABLE: Our City Health vs. Alert Platforms (Dataminir, Placer.ai) vs. Civic/Marketing Platforms (Zencity, Brandwatch, Meltwater) vs. GenAI Wrappers (Custom GPTs, Claude Projects) vs. Consultancies (McKinsey, Deloitte).",
        "OUTPUT TYPE: We provide Structured Database + Alerts + PDF Reports. Competitors provide only one output type.",
        "TIME HORIZON: We provide Real-time + 5-year history. Alert platforms are real-time only. Consultancies lag 6-12 months. GenAI has no memory.",
        "GRANULARITY: We provide City + District level. Alert platforms are incident/store level. Civic/Marketing platforms are entity-centric (track keywords, not locations).",
        "INSIGHT LEVEL: We provide 'Why' (explanatory) + Predictions. Alert platforms provide 'What/Where' (reactive). Civic/Marketing platforms provide 'What' sentiment (but wrong architecture). GenAI is creative but unreliable. Consultancies provide 'Why' but lagging.",
        "AUDIT READY: We provide full citations. Alert platforms provide partial. GenAI hallucinates. Consultancies provide citations but outdated."
    ]
)

# Slide 16: Competitive Analysis - Why Their Architecture Doesn't Fit
add_bullet_slide(
    "Competitive Analysis",
    "Why Their Architecture Doesn't Fit Private Sector Location Risk",
    "Three fundamental mismatches: Entity vs. Geo-Centric, Setup Tax, Government vs. Developer Tool",
    [
        "ENTITY-CENTRIC VS. GEO-CENTRIC: Brandwatch is Entity-Centric — you give it a keyword ('Starbucks'), it tracks mentions. Problem: Misses environmental risks unrelated to the brand. Our City Health is Geo-Centric — you select coordinates (latitude/longitude), we capture ALL sentiment about that location (crime, housing, governance, economy) across 12 dimensions. Use Case: Developer assessing a plot of land doesn't care about 'Starbucks' mentions. They care about whether the district itself is hostile to new development.",
        "THE SETUP TAX: Brandwatch requires manual query setup (define keywords, Boolean logic, filters) for each new location. Cost: Days of analyst time per city. Our City Health has a pre-built taxonomy. No setup. Instant insights for 1,000+ cities and districts. Cost: Zero setup time.",
        "GOVERNMENT TOOL ≠ DEVELOPER TOOL: Zencity measures policy sentiment for governments (e.g., 'Are residents satisfied with the new bus route?'). Problem: Governments need to understand policy approval. Developers need to assess Entitlement Risk. Our City Health quantifies community opposition likelihood, historical resistance patterns, and predictive indicators for project delays. Built for capital allocation decisions, not policy feedback."
    ]
)

# Slide 17: What Each Tool Can Answer
add_bullet_slide(
    "Competitive Analysis",
    "What Each Tool Can Answer — Feature Comparison",
    "We provide the full stack: Detection + Quantification + Explanation + Prediction",
    [
        "'How many people are here?' → Placer.ai ✓ | Dataminr ✗ | Zencity ✗ | Brandwatch ✗ | Our City Health ✓",
        "'Did a disaster just happen?' → Placer.ai ✗ | Dataminr ✓ | Zencity Partial | Brandwatch Partial | Our City Health ✓",
        "'Is this location economically stable?' → Placer.ai ✗ | Dataminir ✗ | Zencity Partial | Brandwatch ✗ | Our City Health ✓",
        "'Why are people avoiding this district?' → Placer.ai ✗ | Dataminr ✗ | Zencity ✗ | Brandwatch ✗ | Our City Health ✓",
        "'Will this community oppose my project?' → Placer.ai ✗ | Dataminir ✗ | Zencity ✗ | Brandwatch ✗ | Our City Health ✓",
        "KEY INSIGHT: Alert Platforms detect events. Civic/Marketing Platforms track sentiment (wrong architecture). We provide geo-centric, district-level civic health intelligence with predictive analytics built for capital allocation decisions. There are great tools for brand monitoring (Brandwatch) and great tools for government policy (Zencity). But if you're a Developer wondering if you should buy a $50M plot of land, their architecture doesn't fit. Brandwatch tracks keywords. We track coordinates. That's the difference."
    ]
)

# Slide 18: Business Model
add_bullet_slide(
    "Business Model & Milestones",
    "Scalable DaaS (Data-as-a-Service) Engine",
    "All prices in Hong Kong Dollars (HKD)",
    [
        "FREE TIER (Explorer): 100 cities (city-level only), Basic portfolios, Basic multi-city comparison, No custom reports, No alerts, Community support.",
        "HK$1,500/month (Professional): Unlimited cities, 5 cities with district-level scores, Email alerts for 5 selected cities/districts, Basic custom multi-city comparison, Basic predictive analytics (dashboard only, no PDF reports), Priority support.",
        "HK$50,000/year (Enterprise): Unlimited cities, Unlimited district-level scores, Custom Intelligence Reports (20+ pages, predictive + analytical), Full dashboard features (portfolios, alerts, comparisons, predictions), Limited API usage (rate-limited), Dedicated Customer Success Manager.",
        "HK$100,000/year (Data License): Everything in Enterprise + Full API firehose (unlimited calls), All cities and districts, White-label option, Dedicated CSM, Priority feature requests."
    ]
)

# Slide 19: Roadmap & Operational Costs
add_bullet_slide(
    "Business Model & Milestones",
    "12-Month Execution Roadmap",
    "Q1: Scale infrastructure. Q2: Solidify product. Q3: Beta launch. Q4: Commercial availability.",
    [
        "Q1 — INFRASTRUCTURE & SCALE: Expand to 1,000 cities. Scale data ingestion to 380,000+ sources (GDELT, NewsAPI, Reddit API, X API, government portals). Develop predictive analytics model. Migrate to cloud cluster (GPU inference). Target: Prototype → Production-ready pipeline.",
        "Q2 — DATA DEPTH & VALIDATION: Launch Corporate Dashboard v1.0 with district-level tracking, portfolios, alerts, and comparisons. Test Custom Intelligence Reports with 2 pilot clients. Solidify predictive analytics capabilities. Target: Product-market fit validation.",
        "Q3 — COMMERCIAL BETA: Launch API + Dashboard Beta. Outreach to 20 organizations (developers, retailers, insurers). Refine product based on feedback. Target: 10 active beta users.",
        "Q4 — FULL COMMERCIAL AVAILABILITY: Public launch. Sign 5+ paid pilot contracts (Target: Real Estate, Retail, Insurance). Revenue generation begins. Target: $120K ARR by end of Q4.",
        "OPERATIONAL COSTS: Data Infrastructure: GDELT ($0, open), NewsAPI (~HK$3,500/mo), Reddit API ($4,680/mo), X API ($33,540/mo), Gov't Data ($0, open). Compute/LLM: OpenAI API (~$1,560-$3,900/mo for scoring 1,000 cities daily), AWS/GCP GPU ($3,900-$7,800/mo). Total: ~HK$47K-$53K/month at scale. Pricing justified by ROI: Single avoided project delay saves $6-8M."
    ]
)

# Slide 20: Core Team
add_bullet_slide(
    "Core Team",
    "AI-Native Founder with High Technical Velocity",
    "",
    [
        "CAYDEN AUYANG — Architect & Founder. Expert in Agentic AI Workflows (Cursor + Google Antigravity) — capable of executing engineering tasks at 5x the speed of traditional developers, keeping burn rate near zero. Dedicated Gap Year (2026-2027): 100% full-time commitment to scaling the venture post-graduation. Developed the core 12-dimension taxonomy at the Civic AI Group, validating the framework with academic rigor.",
        "ALVIN MOK — Key Advisor. Chief Information and Data Officer at Select Equity Group (2025-Present). Previously: Head of Global Platform & Insights at Orbis Investments ($25B+ AUM), led proprietary insights group conducting primary research and alternative data analysis (web data mining, transactional email databases) to inform investment decisions. McKinsey & Company Engagement Manager (Asia, High Tech, Travel, Infrastructure). Harvard MBA (Baker Scholar — Top 5% of graduating class). University of Toronto Computer Engineering (Highest cumulative average in all of UofT, 2003)."
    ]
)

# Slide 21: Why HKSTP
add_bullet_slide(
    "Why HKSTP",
    "Strategic Alignment & Landing Plan",
    "Four critical reasons: Compute, Ecosystem, Compliance, Data Partnerships",
    [
        "COMPUTE INFRASTRUCTURE: Scoring 1,000+ cities daily at city and district level (12 dimensions × 1,000 cities × district subdivisions = massive GPU inference workload). We need HKSTP's supercomputing support to scale cost-effectively.",
        "ECOSYSTEM SANDBOX: HKSTP hosts our exact target clients (Real Estate developers, Retail operators, Logistics firms, Government innovation teams). It is the ideal environment for B2B pilots and warm customer introductions.",
        "COMPLIANCE GUIDANCE: We require mentorship on navigating Cross-Border Data Transfer regulations (PIPL/GDPR) as we expand to the GBA and globally. HKSTP's legal/regulatory support is critical for scaling responsibly.",
        "DATA PARTNERSHIPS: Licensed API access (GDELT, NewsAPI, Reddit API, X/Twitter API, Government Open Data) — we need capital to scale data infrastructure to 380,000+ sources. HKSTP funding enables this expansion.",
        "LANDING PLAN: Immediate: Incorporate Hong Kong entity upon acceptance. 6 months: Hire 1 Business Development Lead + 1 Data Engineer using grant funds. 12 months: First revenue (5+ pilot contracts from HKSTP ecosystem)."
    ]
)

# Slide 22: Closing
slide = prs.slides.add_slide(prs.slide_layouts[6])
slide.background.fill.solid()
slide.background.fill.fore_color.rgb = BG_DARK

# Title
title_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(9), Inches(1.2))
title_frame = title_box.text_frame
title_frame.text = "Ready to Build the Global Standard."
title_frame.paragraphs[0].font.size = Pt(48)
title_frame.paragraphs[0].font.bold = True
title_frame.paragraphs[0].font.color.rgb = WHITE
title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

# Subtitle
subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.8), Inches(9), Inches(0.5))
subtitle_frame = subtitle_box.text_frame
subtitle_frame.text = "Geo-centric location intelligence for capital allocation decisions."
subtitle_frame.paragraphs[0].font.size = Pt(20)
subtitle_frame.paragraphs[0].font.color.rgb = GRAY_LIGHT
subtitle_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

# Stats
stats_box = slide.shapes.add_textbox(Inches(0.5), Inches(4.5), Inches(9), Inches(0.5))
stats_frame = stats_box.text_frame
stats_frame.text = "1,000+ cities. 380,000+ sources. 12 dimensions. One platform."
stats_frame.paragraphs[0].font.size = Pt(18)
stats_frame.paragraphs[0].font.color.rgb = NEON_GREEN
stats_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

# Contact
contact_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(9), Inches(0.5))
contact_frame = contact_box.text_frame
contact_frame.text = "Contact: caydenauyang@gmail.com"
contact_frame.paragraphs[0].font.size = Pt(16)
contact_frame.paragraphs[0].font.bold = True
contact_frame.paragraphs[0].font.color.rgb = WHITE
contact_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

# Save presentation
prs.save('JAN20_pitch_deck.pptx')
print("✅ PowerPoint generated: JAN20_pitch_deck.pptx")
print(f"📊 Total slides: {len(prs.slides)}")
