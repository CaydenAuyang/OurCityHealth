import sqlite3
import json
import time
import os
from typing import Optional, Dict, Any, List
from backend.app.models import JobStatus, JobRequest

DB_PATH = "data/jobs.sqlite"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT,
            progress INTEGER,
            message TEXT,
            created_at REAL,
            request_json TEXT
        )
    """)
    conn.commit()
    conn.close()

def create_job(job_id: str, request: JobRequest):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO jobs (job_id, status, progress, message, created_at, request_json) VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, "pending", 0, "Job created", time.time(), request.model_dump_json())
    )
    conn.commit()
    conn.close()

def update_job(job_id: str, status: Optional[str] = None, progress: Optional[int] = None, message: Optional[str] = None):
    conn = sqlite3.connect(DB_PATH)
    updates = []
    params = []
    if status:
        updates.append("status = ?")
        params.append(status)
    if progress is not None:
        updates.append("progress = ?")
        params.append(progress)
    if message:
        updates.append("message = ?")
        params.append(message)
    
    if updates:
        params.append(job_id)
        conn.execute(f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?", params)
        conn.commit()
    conn.close()

def get_job(job_id: str) -> Optional[JobStatus]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT job_id, status, progress, message, created_at FROM jobs WHERE job_id = ?", (job_id,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        return JobStatus(
            job_id=row[0],
            status=row[1],
            progress=row[2],
            message=row[3],
            created_at=row[4]
        )
    return None

def get_job_request(job_id: str) -> Optional[JobRequest]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT request_json FROM jobs WHERE job_id = ?", (job_id,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        return JobRequest.model_validate_json(row[0])
    return None
