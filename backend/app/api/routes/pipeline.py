from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.engine import get_db
from app.database.repositories import JobRepository
from app.database.schemas import PipelineJobResponse
from app.services.pipeline_service import pipeline_service

router = APIRouter(prefix="/pipeline", tags=["Pipeline & Background Jobs"])

@router.post("/ingest")
def trigger_news_ingestion(db: Session = Depends(get_db)):
    """Triggers background financial news RSS ingestion and stock mapping"""
    job_id = pipeline_service.start_ingestion_job(db)
    return {
        "job_id": job_id,
        "message": "Financial news ingestion job queued.",
        "status": "queued",
    }

@router.post("/analyze-sentiment")
def trigger_sentiment_analysis(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Triggers background local FinBERT inference for pending articles"""
    job_id = pipeline_service.start_sentiment_job(db, limit=limit)
    return {
        "job_id": job_id,
        "message": f"FinBERT sentiment analysis job queued for up to {limit} articles.",
        "status": "queued",
    }

@router.get("/jobs/{job_id}", response_model=PipelineJobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job_repo = JobRepository(db)
    job = job_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job

@router.get("/jobs", response_model=List[PipelineJobResponse])
def list_jobs(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    job_repo = JobRepository(db)
    return job_repo.get_recent_jobs(limit=limit)
