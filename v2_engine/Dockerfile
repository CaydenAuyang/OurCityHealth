# === RAILWAY DEPLOYMENT INSTRUCTIONS ===
#
# 1. Go to https://railway.app and sign in with GitHub
# 2. Click "New Project" → "Deploy from GitHub repo"
# 3. Select "Our-City-Health---Sentiment-Project"
# 4. Set the root directory to "v2_engine"
# 5. Railway will detect the Dockerfile automatically
#
# 6. Add a PostgreSQL plugin:
#    - Click "+ New" → "Database" → "PostgreSQL"
#    - Railway auto-sets DATABASE_URL
#
# 7. Add a Redis plugin:
#    - Click "+ New" → "Database" → "Redis"
#    - Railway auto-sets REDIS_URL
#
# 8. Set environment variables in the service settings:
#    - OPENAI_API_KEY = your OpenAI key
#    - GCP_PROJECT_ID = ourcityhealth (or your project ID)
#    - GOOGLE_APPLICATION_CREDENTIALS_JSON = (paste entire gcp_credentials.json)
#
# 9. After deploy, run the DB init:
#    railway run python3 scripts/init_railway_db.py
#
# 10. Copy your Railway URL (e.g. https://ourcityhealth-production.up.railway.app)
#     Set it as VITE_API_BASE secret in GitHub repo settings
#     Push to main to trigger frontend deploy
# ===

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend_v2/ backend_v2/
COPY scripts/ scripts/

EXPOSE 8001

CMD ["uvicorn", "backend_v2.app:app", "--host", "0.0.0.0", "--port", "8001"]
