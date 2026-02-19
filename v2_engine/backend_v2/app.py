"""
V2 FastAPI Application

Mounts all V2 routers and runs startup/shutdown lifecycle hooks.

Start with:
    cd v2_engine
    uvicorn backend_v2.app:app --reload --port 8001
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # loads v2_engine/.env

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
    allow_origins=["*"],
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
