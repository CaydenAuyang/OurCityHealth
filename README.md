# Our City Health
**Interactive civic wellbeing dashboard — [ourcityhealth.com](https://ourcityhealth.com)**

We turn a continuously updated corpus of public articles and community discussions into a comparable **Civic Health Pulse** for cities worldwide. Using AI and city-tuned sentiment analysis, we score how communities feel about core signals (affordability, services, safety, opportunity, culture), with clickable sources and transparent methods.

---

## Key Features
- **Multi-source ingestion**: NYT/SCMP via Newspaper3k; Reddit via old.reddit.com + BeautifulSoup (or PRAW).
- **City tagging**: Geotag + normalize to city/neighborhood; filter by locality & recency.
- **NLP pipeline**: Entity linking + multilingual sentiment (transformer embeddings; VADER/TextBlob baselines).
- **Topic clustering**: Bucket related phrases into clear, report-ready signals.
- **Civic Health Pulse**: Weighted by recency, locality, and source quality; traceable and privacy-safe.
- **Export-first**: CSV/JSONL for analysis; optional Google Sheets export.

---

## Project Structure
