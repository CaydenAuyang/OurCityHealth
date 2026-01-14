from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Entry(BaseModel):
    source: str                 # 'News', 'RedditPost', 'RedditComment'
    source_site: str            # Domain or subreddit
    url: str
    title: str
    date: Optional[str] = None
    text: str
    cities: List[str] = []
    permalink: Optional[str] = None

class Topic(BaseModel):
    name: str
    description: str
    signals: List[str]
    representative_phrases: List[str]

class DimensionScore(BaseModel):
    score: int
    rationale: str

class Issue(BaseModel):
    name: str
    why_it_matters: str

class CityResult(BaseModel):
    city_name: str
    overall_health: int
    category_scores: Dict[str, DimensionScore]
    top_issues: List[Issue]
    citations: List[str] = [] # URLs used
    reddit_posts: List[str] = [] # Reddit post URLs

class JobRequest(BaseModel):
    cities: List[str]
    dimensions: List[str]
    depth: str = "standard"  # "standard" or "deep"

class JobStatus(BaseModel):
    job_id: str
    status: str # "pending", "running", "completed", "failed"
    progress: int # 0-100
    message: str = ""
    created_at: float
