# Our City Health — The Civic Operating System

> **High-Definition Intelligence for Global Cities.**
> We aim to build the world's first standardized civic health index, solving the resolution crisis in urban data.

---

## 🌍 Project Vision

**Our City Health** is a massive-scale civic intelligence engine designed to provide real-time, granular, and comparable data on the health of 100+ global cities.

Decision-makers today are navigating 2026 problems using 2024 maps. Traditional data sources (Census, Government Reports) are:
1.  **Slow (Latency):** Often 12-24 months out of date.
2.  **Coarse (Granularity):** City-wide averages hide critical district-level trends.
3.  **Siloed (Comparability):** Data formats differ by city, making global portfolio risk management impossible.

We solve this by building a **Universal Resolution Engine** that scrapes unstructured data (News, Social, Forums), standardizes it using Large Language Models (LLMs), and produces a normalized "Civic Health Score" (0-100) for dimensions like Housing, Safety, and Transport.

---

## 📂 Core Products & Mechanisms

### 1. The Public Layer: Global 3D Map (`modern_map.html`)
The public-facing portal designed to build brand authority and validate our data models through transparency.

*   **Mechanism:**
    *   **WebGL Core:** Powered by a high-performance **Three.js** rendering engine (`canvas` context) to visualize 100+ cities on an interactive 3D globe.
    *   **Data Visualization:** Uses glowing particle markers and arc-connections to represent real-time sentiment flows and connectivity between global economic hubs.
    *   **Glassmorphism UI:** A custom-built User Interface layer (`.ui-layer`) that floats above the canvas. It utilizes CSS `backdrop-filter: blur(12px)` and rgba layers to create a "Minority Report" style HUD that functions smoothly without obstructing the data view.
    *   **Interaction:** Features a responsive search & filter system that allows users to drill down from a global view to specific city metrics instantly.

### 2. The B2B Layer: Corporate Intelligence Dashboard (`corporate_dashboard.html`)
 The specialized tool for high-value Enterprise clients (Property Developers, Hedge Funds, Risk Managers).

*   **Mechanism:**
    *   **Portfolio Management Logic:** Unlike the public map (exploratory), this dashboard is built for *monitoring*. It features a sidebar-driven layout (`.sidebar` + `.main-content`) optimized for rapid switching between different asset portfolios.
    *   **Deep-Dive Analytics:** Designed to render complex historical trend lines and comparative bar charts, allowing analysts to compare "Safety Scores" of London vs. Hong Kong over a 5-year timeline.
    *   **Custom Filtering Components:** Implements custom-built dropdowns (`.select-custom`) and multi-select forms, bypassing default browser controls to allow for sophisticated filtering (e.g., "Show me cities with >80 Housing Stress AND <50 Safety").
    *   **Watchlist Architecture:** Optimized to track specific "At-Risk" assets, alerting users when sentiment shifts in specific districts.

### 3. The Pitch (`REAL_pitch_deck.html`)
The official pitch deck for the **HKSTP Ideation Programme**.
*   **Style:** Modern PowerPoint / Keynote aesthetic (Clean, Professional).
*   **Tech:** Pure HTML/CSS with smooth CSS transitions and staggered animations.

---

## 🛠️ Combined Technical Stack

*   **Frontend Architecture:**
    *   **Core:** HTML5, CSS3 (Custom Properties for theming), Vanilla JavaScript (ES6+).
    *   **3D Rendering:** Three.js / WebGL.
    *   **UI System:** Custom "Glassmorphism" Design System (Dark Mode optimized).
*   **Backend / Data Engine (`conclusive_scaper_and_analysis_v3.py`):**
    *   **Pipeline:** Python-based orchestration.
    *   **LLM Integration:** Semantic analysis for standardizing unstructured text.
    *   **Scrapers:** Targeted ingestion of News APIs and social threads.

---

## 🚀 How to Run

To view the full suite locally:

1.  **Start a local server** (Python 3):
    ```bash
    python3 -m http.server 8080
    ```

2.  **Open in your browser:**
    *   **Pitch Deck:** [http://localhost:8080/REAL_pitch_deck.html](http://localhost:8080/REAL_pitch_deck.html)
    *   **Global Map:** [http://localhost:8080/modern_map.html](http://localhost:8080/modern_map.html)
    *   **Corporate Dashboard:** [http://localhost:8080/corporate_dashboard.html](http://localhost:8080/corporate_dashboard.html)

---

## 📅 Roadmap (12 Months)

*   **Q1 (Architecture):** Refactor v3 Pipeline for 100-city concurrency.
*   **Q2 (Data Expansion):** Integrate high-volume noise sources (Forums/Telegram).
*   **Q3 (API Launch):** Open the "Civic Firehose API" for developers.
*   **Q4 (Enterprise):** Secure 3 major enterprise contracts.

---

**Contact:** Cayden Auyang (Founder & Architect)
