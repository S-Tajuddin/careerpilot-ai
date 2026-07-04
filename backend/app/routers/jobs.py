"""
CareerPilot AI — Jobs Router
Job listing, search, scoring, and management endpoints.

Route order matters! Specific paths MUST come before /{job_id} parameterized routes.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, Application, SearchHistory, ActivityLog
from app.schemas import (
    JobResponse, JobListResponse, JobSearchRequest, JobScoreRequest,
    MessageResponse, SearchHistoryResponse,
)

router = APIRouter()


def _job_to_response(job: Job) -> JobResponse:
    """Convert ORM Job to response schema."""
    skills = []
    if job.skills_required:
        try:
            skills = json.loads(job.skills_required) if isinstance(job.skills_required, str) else job.skills_required
        except (json.JSONDecodeError, TypeError):
            skills = []

    strengths = []
    if job.match_strengths:
        try:
            strengths = json.loads(job.match_strengths) if isinstance(job.match_strengths, str) else job.match_strengths
        except (json.JSONDecodeError, TypeError):
            strengths = []

    weaknesses = []
    if job.match_weaknesses:
        try:
            weaknesses = json.loads(job.match_weaknesses) if isinstance(job.match_weaknesses, str) else job.match_weaknesses
        except (json.JSONDecodeError, TypeError):
            weaknesses = []

    recommendations = []
    if job.match_recommendations:
        try:
            recommendations = json.loads(job.match_recommendations) if isinstance(job.match_recommendations, str) else job.match_recommendations
        except (json.JSONDecodeError, TypeError):
            recommendations = []

    return JobResponse(
        id=job.id,
        source=job.source,
        source_id=job.source_id,
        source_url=job.source_url,
        title=job.title,
        company_id=job.company_id,
        company_name=job.company_name,
        location=job.location,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_period=job.salary_period,
        job_type=job.job_type,
        is_remote=job.is_remote,
        description=job.description,
        requirements=job.requirements,
        skills_required=skills,
        experience_required=job.experience_required,
        posted_date=job.posted_date,
        match_score=job.match_score,
        match_strengths=strengths,
        match_weaknesses=weaknesses,
        match_recommendations=recommendations,
        is_active=job.is_active,
        created_at=job.created_at,
        salary_display=job.salary_display(),
    )


# ══════════════════════════════════════════════════════════════════════════════
# SPECIFIC ROUTES — must come BEFORE /{job_id}
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("match_score", description="Sort field: match_score, posted_date, created_at"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    min_score: Optional[float] = Query(None, description="Minimum match score filter"),
    source: Optional[str] = Query(None, description="Filter by source: jsearch, adzuna, greenhouse, lever"),
    is_remote: Optional[bool] = Query(None, description="Filter remote jobs"),
    is_active: bool = Query(True, description="Show only active jobs"),
    search: Optional[str] = Query(None, description="Full-text search in title, company, description"),
    db: Session = Depends(get_db),
):
    """List jobs with filters and sorting."""
    query = db.query(Job).filter(Job.is_active == is_active)

    if min_score is not None:
        query = query.filter(Job.match_score >= min_score)
    if source:
        query = query.filter(Job.source == source)
    if is_remote is not None:
        query = query.filter(Job.is_remote == is_remote)

    # Full-text search using FTS5
    if search:
        fts_results = db.execute(
            __import__("sqlalchemy").text(
                "SELECT rowid FROM jobs_fts WHERE jobs_fts MATCH :query"
            ),
            {"query": search},
        ).fetchall()
        fts_ids = [r[0] for r in fts_results]
        if fts_ids:
            query = query.filter(Job.id.in_(fts_ids))
        else:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Job.title.ilike(search_term),
                    Job.company_name.ilike(search_term),
                    Job.description.ilike(search_term),
                )
            )

    # Sorting
    sort_column = getattr(Job, sort_by, Job.match_score)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc().nulls_last())

    total = query.count()
    jobs = query.offset((page - 1) * per_page).limit(per_page).all()

    return JobListResponse(
        total=total,
        jobs=[_job_to_response(j) for j in jobs],
        page=page,
        per_page=per_page,
    )


@router.get("/search", response_model=JobListResponse)
async def search_jobs_get(
    query: str = Query(..., description="Job search query, e.g. 'AEM developer'"),
    location: Optional[str] = Query(None, description="Location, e.g. 'Hyderabad, India'"),
    country: str = Query("in", description="Country code: in, us, gb, etc."),
    remote_only: bool = Query(False, description="Remote jobs only"),
    date_posted: Optional[str] = Query(None, description="Filter: today, 3days, week, month"),
    max_results: int = Query(20, ge=1, le=100, description="Max results"),
    db: Session = Depends(get_db),
):
    """
    Search for jobs using external APIs (JSearch, Adzuna, etc.).
    Browser-friendly GET version — results are saved to DB and returned.
    """
    from app.services.job_service import job_service

    normalized_jobs = await job_service.search_all_sources(
        query=query,
        location=location,
        country=country,
        remote_only=remote_only,
        date_posted=date_posted,
        max_results=max_results,
        db=db,
    )

    # Fetch the newly saved jobs from DB
    search_term = f"%{query}%"
    db_jobs = db.query(Job).filter(
        Job.is_active == True,
        (Job.title.ilike(search_term) | Job.description.ilike(search_term)),
    ).order_by(Job.created_at.desc()).limit(max_results).all()

    return JobListResponse(
        total=len(db_jobs),
        jobs=[_job_to_response(j) for j in db_jobs],
        page=1,
        per_page=max_results,
    )


@router.post("/search", response_model=JobListResponse)
async def search_jobs_post(request: JobSearchRequest, db: Session = Depends(get_db)):
    """
    Search for jobs using external APIs (JSearch, Adzuna, etc.).
    POST version for programmatic use with JobSearchRequest body.
    """
    from app.services.job_service import job_service

    normalized_jobs = await job_service.search_all_sources(
        query=request.query,
        location=request.location,
        country=request.country,
        remote_only=request.remote_only,
        date_posted=request.date_posted,
        max_results=request.max_results,
        db=db,
    )

    search_term = f"%{request.query}%"
    db_jobs = db.query(Job).filter(
        Job.is_active == True,
        (Job.title.ilike(search_term) | Job.description.ilike(search_term)),
    ).order_by(Job.created_at.desc()).limit(request.max_results).all()

    return JobListResponse(
        total=len(db_jobs),
        jobs=[_job_to_response(j) for j in db_jobs],
        page=1,
        per_page=request.max_results,
    )


@router.post("/score", response_model=JobResponse)
def score_job(request: JobScoreRequest, db: Session = Depends(get_db)):
    """
    Score a job against the user profile using AI.
    Uses Ollama (background) or Gemini (interactive).
    """
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")

    if job.match_score is not None and not request.force_rescore:
        return _job_to_response(job)

    # Scoring will be implemented in Phase 2 (AI Matching pipeline)
    raise HTTPException(
        status_code=501,
        detail="AI scoring not yet implemented — coming in Phase 2",
    )


@router.get("/stats/summary")
def jobs_stats(db: Session = Depends(get_db)):
    """Get job statistics summary for the dashboard."""
    total_active = db.query(func.count(Job.id)).filter(Job.is_active == True).scalar() or 0
    total_scored = db.query(func.count(Job.id)).filter(
        Job.is_active == True, Job.match_score.isnot(None)
    ).scalar() or 0
    avg_score = db.query(func.avg(Job.match_score)).filter(
        Job.is_active == True, Job.match_score.isnot(None)
    ).scalar() or 0

    by_source = db.query(
        Job.source, func.count(Job.id)
    ).filter(Job.is_active == True).group_by(Job.source).all()

    by_company = db.query(
        Job.company_name, func.count(Job.id)
    ).filter(Job.is_active == True).group_by(Job.company_name).order_by(
        desc(func.count(Job.id))
    ).limit(10).all()

    remote_count = db.query(func.count(Job.id)).filter(
        Job.is_active == True, Job.is_remote == True
    ).scalar() or 0

    applied_count = db.query(func.count(Application.id)).filter(
        Application.status.in_(["applied", "interview_scheduled", "interview_done", "offer"])
    ).scalar() or 0

    return {
        "total_active_jobs": total_active,
        "total_scored": total_scored,
        "avg_match_score": round(avg_score, 1),
        "remote_jobs": remote_count,
        "onsite_jobs": total_active - remote_count,
        "applications_count": applied_count,
        "by_source": {source: count for source, count in by_source},
        "top_companies": [{"company": name, "count": count} for name, count in by_company],
    }


@router.get("/history/searches", response_model=list[SearchHistoryResponse])
def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get recent search history."""
    searches = db.query(SearchHistory).order_by(
        desc(SearchHistory.created_at)
    ).limit(limit).all()

    return [
        SearchHistoryResponse(
            id=s.id,
            query=s.query,
            filters=s.filters,
            results_count=s.results_count,
            source=s.source,
            created_at=s.created_at,
        )
        for s in searches
    ]


# ══════════════════════════════════════════════════════════════════════════════
# PARAMETERIZED ROUTES — must come LAST
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a single job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return _job_to_response(job)


@router.delete("/{job_id}", response_model=MessageResponse)
def deactivate_job(job_id: int, db: Session = Depends(get_db)):
    """Soft-delete a job (mark as inactive)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job.is_active = False
    job.updated_at = datetime.now(timezone.utc)
    db.commit()

    _log_activity(db, "job_deactivated", "job", job_id, {"title": job.title})
    return MessageResponse(message=f"Job '{job.title}' deactivated")


# ─── Helper Functions ────────────────────────────────────────────────────────


def _log_search(db: Session, query: str, location: str, count: int, source: str):
    """Log a search to history."""
    entry = SearchHistory(
        query=query,
        filters=json.dumps({"location": location}),
        results_count=count,
        source=source,
    )
    db.add(entry)
    db.commit()


def _log_activity(db: Session, action: str, entity_type: str, entity_id: int, details: dict = None):
    """Log an activity."""
    entry = ActivityLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=json.dumps(details) if details else None,
    )
    db.add(entry)
    db.commit()
