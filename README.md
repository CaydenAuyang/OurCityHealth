# Our City Health
**Interactive civic wellbeing dashboard — [ourcityhealth.com](https://ourcityhealth.com)**


We transform massive, continuously updated datasets of public articles and community discussions into a comparable Civic Health Pulse for cities worldwide. Using advanced AI analysis and city-tuned sentiment scoring, we provide transparent, trustworthy insights into how communities feel about core civic dimensions.

## 🌟 Key Features

### **Massive Data Collection**
- **3,331+ news articles** from 29 international sources (NYT, SCMP, BBC, Reuters, Guardian, CNN, Al Jazeera, Economist, Japan Times, Korea Herald, Channel News Asia, Straits Times, The Hindu, Times of India, Bangkok Post, Jakarta Post, Rappler, Dawn, ABC Australia, SMH, The Age, NZ Herald, DW, Euronews)
- **502+ Reddit posts** and **1,823+ Reddit comments** from 30+ city subreddits
- **29 global cities** analyzed with comprehensive coverage
- **500 articles per source** for maximum data density and accuracy

### **Advanced AI Analysis**
- **OpenAI GPT-4 integration** for intelligent topic modeling and city health scoring
- **spaCy NLP pipeline** with Named Entity Recognition for city detection
- **12 civic dimensions** scored: Affordability, Services, Safety, Opportunity, Culture, Environment, Transportation, Governance, Housing, Economy, Education, Health
- **Machine learning clustering** using AgglomerativeClustering for topic grouping
- **Comprehensive citations** with source URLs and timestamps for full transparency

### **Modern Interactive Dashboard**
- **Green-themed minimalist design** with smooth animations and responsive layout
- **Dynamic data loading** from structured JSON with real-time updates
- **Clickable city cards** with detailed modal views showing per-category scores
- **Trustworthy metrics** with explanations, rationale, and source citations
- **All 29 cities** displayed with comprehensive health scoring

### **Automated Daily Updates**
- **Incremental scraping** to avoid duplicate content and maximize efficiency
- **Smart deduplication** using URL hashing and content fingerprinting
- **Automated scheduling** with cron jobs for daily data collection
- **Persistent state management** with SQLite database for tracking processed content
- **Rolling analysis windows** combining new data with historical context

## 🏗️ Architecture

### **Data Pipeline**
1. **Multi-source ingestion**: News sites via requests + BeautifulSoup, Reddit via JSON API
2. **City detection**: spaCy NER + custom city synonyms mapping
3. **Content processing**: Text extraction, cleaning, and normalization
4. **AI analysis**: OpenAI API for topic modeling and health scoring
5. **Data persistence**: SQLite database with daily snapshots
6. **Dashboard updates**: Dynamic JSON loading with latest results

### **Technology Stack**
- **Backend**: Python 3.8+ with asyncio for concurrent processing
- **NLP**: spaCy, scikit-learn, transformers
- **AI**: OpenAI GPT-4 API for advanced analysis
- **Database**: SQLite with planned PostgreSQL migration
- **Frontend**: Vanilla JavaScript with modern CSS animations
- **Deployment**: Local cron scheduling with cloud hosting options

## �� Current Results

### **Top Performing Cities (Health Scores)**
1. **Singapore** - 75/100 (Safety: 90, Transport: 85, Services: 85)
2. **Paris** - 75/100 (Culture: 90, Transport: 85, Services: 80)
3. **Tokyo** - 75/100 (Safety: 90, Transport: 90, Services: 85)
4. **Dubai** - 75/100 (Safety: 85, Economy: 85, Services: 80)
5. **Barcelona** - 75/100 (Culture: 85, Transport: 80, Health: 80)

### **Data Sources Coverage**
- **News Articles**: 3,331 analyzed across 29 international sources
- **Social Media**: 502 Reddit posts + 1,823 comments from city subreddits
- **Geographic Coverage**: 29 cities across 6 continents
- **Temporal Range**: Daily updates with rolling 30-day analysis windows

## 🚀 Quick Start

### **Prerequisites**
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key-here"
```

### **Run Analysis**
```bash
# Full analysis (first run)
python3 conclusive_scraper_and_analysis.py

# Incremental daily update
python3 conclusive_scraper_and_analysis.py --mode incremental --since 24h

# View dashboard
open city_health_dashboard_MASSIVE.html
```

### **Automated Daily Updates**
```bash
# Set up cron job (runs daily at 3:15 AM)
crontab -e
# Add: 15 3 * * * cd "/path/to/Automation-Project" && ./run_daily.sh

# Manual daily run
./run_daily.sh
```

## �� Project Structure

```
Automation-Project/
├── conclusive_scraper_and_analysis.py    # Main analysis pipeline
├── city_health_dashboard_MASSIVE.html    # Interactive dashboard
├── full_results_MASSIVE.json            # Structured analysis results
├── full_analysis_MASSIVE.txt            # Detailed text report
├── data/
│   ├── latest/                          # Current results
│   └── YYYY-MM-DD/                      # Daily snapshots
├── run_daily.sh                         # Daily automation script
└── requirements.txt                     # Python dependencies
```

## 🔧 Configuration

### **Data Collection Limits**
- **Articles per source**: 500 (configurable)
- **Reddit pages per city**: 10
- **Comments per post**: 100
- **Analysis sample size**: 200 titles for global topics
- **Keyword phrase limit**: 1,000 for topic modeling

### **AI Analysis Settings**
- **City documents per model call**: 100
- **Global sample titles**: 200
- **Civic dimensions**: 12 comprehensive categories
- **Health score range**: 0-100 with detailed explanations

## �� Deployment Options

### **Local Development**
- Run analysis locally with cron scheduling
- Serve dashboard via simple HTTP server
- SQLite database for state management

### **Cloud Deployment**
- **AWS**: EC2 + S3 + CloudFront for global distribution
- **Google Cloud**: Compute Engine + Cloud Storage
- **Azure**: Virtual Machine + Blob Storage
- **Vercel/Netlify**: Static hosting with API integration

## 📈 Future Enhancements

- **Real-time streaming**: WebSocket updates for live data
- **Mobile app**: React Native dashboard
- **API endpoints**: RESTful API for third-party integration
- **Advanced ML**: Custom transformer models for city-specific analysis
- **Geographic expansion**: 100+ cities worldwide
- **Multi-language support**: Analysis in local languages

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for:
- Code style and standards
- Testing requirements
- Documentation updates
- Feature proposals

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 API access and advanced analysis capabilities
- **spaCy** for robust natural language processing
- **Reddit** for community discussion data access
- **News sources** for providing comprehensive coverage
- **Global cities** for the rich data that makes this analysis possible

---

**My City Health** - Making civic wellbeing transparent, trustworthy, and actionable through data-driven insights.
