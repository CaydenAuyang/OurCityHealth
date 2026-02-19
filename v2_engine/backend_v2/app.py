"""
V2 FastAPI Application

Mounts all V2 routers and runs startup/shutdown lifecycle hooks.

Start with:
    cd v2_engine
    uvicorn backend_v2.app:app --reload --port 8001
"""

from __future__ import annotations

import json
import logging
import os
import tempfile

from dotenv import load_dotenv

load_dotenv()  # loads v2_engine/.env

# Railway: materialise GCP credentials from env var (no file mount on PaaS)
_creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if _creds_json and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    _creds_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False,
    )
    _creds_file.write(_creds_json)
    _creds_file.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _creds_file.name

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_v2.db.session import init_db
from backend_v2.api.routes.scoring import router as scoring_router
from backend_v2.api.routes.cities import router as cities_router  # Phase 4
from backend_v2.api.routes.events import router as events_router  # V2.1
from backend_v2.api.routes.coverage import router as coverage_router  # V2.1 timeline
from backend_v2.api.routes.districts import router as districts_router  # V2.1 geo
from backend_v2.api.routes.sources import router as sources_router  # V2.2

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Our City Health — V2 API",
    description=(
        "Geospatial Intelligence Platform.  "
        "Financial-grade civic health scores powered by GDELT + LLM."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://caydenauyang.github.io",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("V2 API starting up — initialising database…")
    await init_db()
    logger.info("V2 API ready.")


app.include_router(scoring_router)
app.include_router(cities_router)  # Phase 4
app.include_router(events_router)  # V2.1
app.include_router(coverage_router)  # V2.1 timeline
app.include_router(districts_router)  # V2.1 geo
app.include_router(sources_router)  # V2.2


@app.get("/healthz", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "version": "2.0.0"}
