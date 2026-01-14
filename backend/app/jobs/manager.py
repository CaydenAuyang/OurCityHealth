import uuid
from fastapi import BackgroundTasks
from backend.app.models import JobRequest
from backend.app.jobs.db import create_job, init_db
from backend.app.jobs.pipeline import run_job

def submit_job(request: JobRequest, background_tasks: BackgroundTasks) -> str:
    job_id = str(uuid.uuid4())
    
    # Ensure DB exists
    init_db()
    
    # Create record
    create_job(job_id, request)
    
    # Launch background task
    background_tasks.add_task(run_job, job_id)
    
    return job_id
