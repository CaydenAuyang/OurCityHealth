import os
import json
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from backend.app.models import JobRequest, JobStatus
from backend.app.jobs.manager import submit_job
from backend.app.jobs.db import get_job
from backend.app.chat.agent import chat_agent, ChatRequest, ChatResponse

app = FastAPI(
    title="Our City Health - Corporate Intelligence API",
    description="Backend for the Corporate Deep-Scrape Dashboard",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "*" # For development convenience
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "version": "1.0.0"
    }

@app.post("/api/jobs")
async def create_job_endpoint(request: JobRequest, background_tasks: BackgroundTasks):
    job_id = submit_job(request, background_tasks)
    return {"job_id": job_id}

@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
        
    path = f"data/jobs/{job_id}/results.json"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Results file not found")
        
    with open(path, "r") as f:
        return json.load(f)

@app.get("/api/jobs/{job_id}/events")
async def job_events(job_id: str):
    async def event_generator():
        last_progress = -1
        last_status = ""
        while True:
            job = get_job(job_id)
            if not job:
                yield f"event: error\ndata: Job not found\n\n"
                break
            
            # Send status update if changed
            if job.progress != last_progress or job.status != last_status:
                data = json.dumps({
                    "status": job.status,
                    "progress": job.progress,
                    "message": job.message
                })
                yield f"data: {data}\n\n"
                last_progress = job.progress
                last_status = job.status
            else:
                yield ": keep-alive\n\n"
            
            if job.status in ("completed", "failed"):
                break
                
            await asyncio.sleep(0.5)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    return chat_agent(req)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
