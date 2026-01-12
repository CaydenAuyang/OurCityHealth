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

## 📂 Key Components

### 1. The Presentations (HKSTP Ideation)
We have developed a set of pitch decks for the HKSTP Ideation Programme application.

*   **`REAL_pitch_deck.html` (Use This One):**
    *   The **official** pitch deck for the application.
    *   **Style:** Modern PowerPoint / Keynote aesthetic (Clean, Professional, Apple-style).
    *   **Tech:** HTML/CSS with smooth CSS transitions and staggered animations.
    *   **Content:** Covers the full narrative from the "Resolution Crisis" to the 12-Month Roadmap and Business Model.

*   **`OLD_pitchdeck.html` (Deprecated):**
    *   An alternative "Minority Report" / "Cyberpunk" styled deck.
    *   Kept for archival purposes to demonstrate design versatility.
    *   **Style:** Dark Mode, Neon Green/Blue accents, Scanlines, Monospace fonts.

### 2. The Visualizations (Frontend)
These files demonstrate the "Front-End" of our Intelligence Platform.

*   **`modern_map.html` (The Public Layer):**
    *   A high-performance 3D Globe visualization powered by **Three.js**.
    *   Features glowing city markers, arc connections, and a futuristic UI.
    *   Designed as a free public tool to build brand authority and validate data models.

*   **`corporate_dashboard.html` (The B2B Platform):**
    *   A professional dashboard for Enterprise clients (Property Developers, Hedge Funds).
    *   Provides deep-dive analytics, trend comparisons, and "Watchlists" for portfolio management.
    *   Demonstrates the commercial application of our data.

### 3. The Engine (Backend)
The core logic that powers the system.

*   **`conclusive_scaper_and_analysis_v3.py`:**
    *   The **Production Pipeline (v3)**.
    *   **Function:** Orchestrates the scraping of data, cleaning via LLM, sentiment analysis, and scoring.
    *   **Status:** Validated Proof of Concept (POC) capable of handling concurrent city data streams.

---

## 🛠️ Technical Stack

*   **Frontend:**
    *   **HTML5 / CSS3:** Uses modern features (Flexbox, Grid, CSS Variables, Backdrop Filters).
    *   **JavaScript:** Vanilla JS for lightweight performance + Three.js for 3D visualization.
    *   **Design System:** Custom "Glassmorphism" UI with standardized design tokens.
*   **Backend / Data:**
    *   **Python:** Core scripting language.
    *   **LLMs:** Used for semantic analysis, entity extraction, and sentiment scoring.
    *   **Data Sources:** News APIs, Social Media Scrapers (Reddit, etc.).

---

## 🚀 How to Run

To view the dashboards and pitch decks locally:

1.  **Start a local server** (Python 3):
    ```bash
    python3 -m http.server 8080
    ```

2.  **Open in your browser:**
    *   **Pitch Deck:** [http://localhost:8080/REAL_pitch_deck.html](http://localhost:8080/REAL_pitch_deck.html)
    *   **Public Map:** [http://localhost:8080/modern_map.html](http://localhost:8080/modern_map.html)
    *   **Corporate Dashboard:** [http://localhost:8080/corporate_dashboard.html](http://localhost:8080/corporate_dashboard.html)

---

## 📅 Roadmap (12 Months)

*   **Q1 (Architecture):** Refactor v3 Pipeline for 100-city concurrency.
*   **Q2 (Data Expansion):** Integrate high-volume noise sources (Forums/Telegram).
*   **Q3 (API Launch):** Open the "Civic Firehose API" for developers.
*   **Q4 (Enterprise):** Secure 3 major enterprise contracts.

---

**Contact:** Cayden Auyang (Founder & Architect)
