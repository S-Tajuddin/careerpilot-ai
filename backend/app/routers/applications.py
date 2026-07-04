"""
CareerPilot AI — Applications Router
Track job applications, status updates, follow-ups.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application, Job
from app.routers.jobs import _job_to_response
from app.schemas import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse, MessageResponse,
)

router = APIRouter()


def _application_to_response(app: Application, include_job: bool = True) -> ApplicationResponse:
    """Convert ORM Application to response schema."""
    job_resp = None
    if include_job and app.job:
        job_resp = _job_to_response(app.job)

    return ApplicationResponse(
        id=app.id,
        job_id=app.job_id,
        status=app.status,
        applied_at=app.applied_at,
        resume_version=app.resume_version,
        cover_letter_path=app.cover_letter_path,
        notes=app.notes,
        rating=app.rating,
        next_followup=app.next_followup,
        followup_count=app.followup_count,
        response_notes=app.response_notes,
        response_type=app.response_type,
        response_at=app.response_at,
        created_at=app.created_at,
        updated_at=app.updated_at,
        job=job_resp,
    )


@router.get("/", response_model=list[ApplicationResponse])
def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all applications with optional status filter."""
    query = db.query(Application)

    if status:
        query = query.filter(Application.status == status)

    apps = query.order_by(desc(Application.updated_at)).offset(offset).limit(limit).all()
    return [_application_to_response(a) for a in apps]


@router.post("/", response_model=ApplicationResponse, status_code=201)
def create_application(data: ApplicationCreate, db: Session = Depends(get_db)):
    """Create a new application for a job."""
    # Check job exists
    job = db.query(Job).filter(Job.id == data.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {data.job_id} not found")

    # Check if application already exists
    existing = db.query(Application).filter(Application.job_id == data.job_id).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Application already exists for job {data.job_id} (status: {existing.status})",
        )

    app = Application(
        job_id=data.job_id,
        status=data.status,
        notes=data.notes,
        rating=data.rating,
    )

    if data.status == "applied":
        app.applied_at = datetime.now(timezone.utc)

    db.add(app)
    db.commit()
    db.refresh(app)

    return _application_to_response(app)


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: int, db: Session = Depends(get_db)):
    """Get a single application by ID."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
    return _application_to_response(app)


@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    updates: ApplicationUpdate,
    db: Session = Depends(get_db),
):
    """Update an application (status, notes, rating, etc.)."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")

    update_data = updates.model_dump(exclude_unset=True)

    # If status is changing to "applied" and no applied_at, set it
    if "status" in update_data and update_data["status"] == "applied" and not app.applied_at:
        app.applied_at = datetime.now(timezone.utc)

    # If status is changing to "interview_scheduled", set follow-up
    if "status" in update_data and update_data["status"] == "interview_scheduled":
        from datetime import timedelta
        if not app.next_followup:
            app.next_followup = datetime.now(timezone.utc) + timedelta(days=1)

    for key, value in update_data.items():
        if hasattr(app, key):
            setattr(app, key, value)

    app.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(app)

    return _application_to_response(app)


@router.delete("/{application_id}", response_model=MessageResponse)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    """Delete an application."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")

    db.delete(app)
    db.commit()
    return MessageResponse(message=f"Application {application_id} deleted")


@router.get("/followups/upcoming")
def upcoming_followups(
    days: int = Query(7, ge=1, le=30, description="Days to look ahead"),
    db: Session = Depends(get_db),
):
    """Get applications with upcoming follow-ups."""
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) + timedelta(days=days)

    apps = db.query(Application).filter(
        Application.next_followup.isnot(None),
        Application.next_followup <= cutoff,
        Application.status.in_(["applied", "interview_scheduled", "interview_done"]),
    ).order_by(Application.next_followup).all()

    return {
        "count": len(apps),
        "followups": [_application_to_response(a) for a in apps],
    }


@router.get("/stats/summary")
def application_stats(db: Session = Depends(get_db)):
    """Get application statistics for the dashboard."""
    from sqlalchemy import func

    total = db.query(func.count(Application.id)).scalar() or 0

    by_status = db.query(
        Application.status, func.count(Application.id)
    ).group_by(Application.status).all()

    # Response rate (how many got any response)
    responded = db.query(func.count(Application.id)).filter(
        Application.response_type.isnot(None)
    ).scalar() or 0

    # Interview rate
    interviews = db.query(func.count(Application.id)).filter(
        Application.status.in_(["interview_scheduled", "interview_done", "offer"])
    ).scalar() or 0

    # Offers
    offers = db.query(func.count(Application.id)).filter(
        Application.status == "offer"
    ).scalar() or 0

    return {
        "total_applications": total,
        "by_status": {status: count for status, count in by_status},
        "response_rate": round(responded / total * 100, 1) if total > 0 else 0,
        "interview_rate": round(interviews / total * 100, 1) if total > 0 else 0,
        "offers": offers,
    }
