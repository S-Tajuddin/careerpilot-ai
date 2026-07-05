"""
CareerPilot AI — Documents Router
Cover letter generation, resume tailoring, and file download endpoints.

Route order: specific paths BEFORE parameterized routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import CoverLetter, Job, Profile, Application
from app.schemas import (
    CoverLetterGenerate, CoverLetterResponse, MessageResponse,
)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# COVER LETTER ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: CoverLetterGenerate,
    db: Session = Depends(get_db),
):
    """
    Generate a cover letter for a specific job.
    Uses Gemini Flash for fast, high-quality output (~2-3s).
    Only references skills/experience from your profile — never fabricates.
    """
    from app.services.cover_letter import cover_letter_service

    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")

    profile = db.query(Profile).filter(Profile.id == 1).first()
    if not profile:
        raise HTTPException(status_code=400, detail="No profile found — create your profile first")

    try:
        cover_letter = await cover_letter_service.generate_cover_letter(
            job=job,
            profile=profile,
            db=db,
            tone=request.tone or "professional",
        )
        return CoverLetterResponse.model_validate(cover_letter)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {e}")


@router.get("/cover-letter/job/{job_id}", response_model=list[CoverLetterResponse])
def get_cover_letters_for_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get all cover letters generated for a specific job."""
    cover_letters = db.query(CoverLetter).filter(
        CoverLetter.job_id == job_id
    ).order_by(CoverLetter.created_at.desc()).all()

    return [CoverLetterResponse.model_validate(cl) for cl in cover_letters]


@router.get("/cover-letter/{cover_letter_id}", response_model=CoverLetterResponse)
def get_cover_letter(
    cover_letter_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific cover letter by ID."""
    cl = db.query(CoverLetter).filter(CoverLetter.id == cover_letter_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail=f"Cover letter {cover_letter_id} not found")
    return CoverLetterResponse.model_validate(cl)


# ══════════════════════════════════════════════════════════════════════════════
# RESUME TAILORING ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/tailor-resume")
async def tailor_resume(
    job_id: int = Query(..., description="Job ID to tailor resume for"),
    db: Session = Depends(get_db),
):
    """
    Generate a tailored version of your resume for a specific job.
    Reorganizes and emphasizes existing content — NEVER fabricates experience.
    Uses Gemini Flash for high-quality output.
    """
    from app.services.resume_tailor import resume_tailor_service

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    profile = db.query(Profile).filter(Profile.id == 1).first()
    if not profile:
        raise HTTPException(status_code=400, detail="No profile found — create your profile first")

    if not profile.resume_text:
        raise HTTPException(status_code=400, detail="No resume uploaded — upload your resume first in the Profile page")

    try:
        result = await resume_tailor_service.tailor_resume(
            job=job,
            profile=profile,
            db=db,
        )

        # Update application's resume_version if application exists
        app = db.query(Application).filter(Application.job_id == job_id).first()
        if app:
            app.resume_version = result["file_path"]
            db.commit()

        return {
            "message": f"Tailored resume generated for {job.title} at {job.company_name}",
            "file_path": result["file_path"],
            "content_length": result["content_length"],
            "model_used": result["model_used"],
            "job_id": job_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume tailoring failed: {e}")


@router.get("/tailored-resume/{job_id}")
def get_tailored_resume(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get the tailored resume for a specific job (if one was generated)."""
    from app.services.resume_tailor import resume_tailor_service

    result = resume_tailor_service.get_tailored_resume_for_job(job_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No tailored resume found for job {job_id}. Generate one first with POST /api/documents/tailor-resume",
        )

    return {
        "job_id": job_id,
        "file_path": result["file_path"],
        "content_length": result["content_length"],
        "has_content": True,
    }


# ══════════════════════════════════════════════════════════════════════════════
# FILE DOWNLOAD ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/download/cover-letter/{cover_letter_id}")
def download_cover_letter(
    cover_letter_id: int,
    db: Session = Depends(get_db),
):
    """Download a cover letter as a text file."""
    cl = db.query(CoverLetter).filter(CoverLetter.id == cover_letter_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail=f"Cover letter {cover_letter_id} not found")

    if not cl.file_path:
        # Generate file from content
        from pathlib import Path
        from app.config import COVER_LETTERS_DIR
        COVER_LETTERS_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"cover_letter_{cl.id}_job{cl.job_id}.txt"
        file_path = COVER_LETTERS_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(cl.content)
        cl.file_path = str(file_path)
        db.commit()

    from pathlib import Path
    path = Path(cl.file_path)
    if not path.exists():
        # Re-create the file
        with open(path, "w", encoding="utf-8") as f:
            f.write(cl.content)

    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type="text/plain",
    )


@router.get("/download/tailored-resume/{job_id}")
def download_tailored_resume(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Download a tailored resume as a text file."""
    from app.services.resume_tailor import resume_tailor_service
    from pathlib import Path

    result = resume_tailor_service.get_tailored_resume_for_job(job_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"No tailored resume found for job {job_id}")

    path = Path(result["file_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Tailored resume file not found on disk")

    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type="text/plain",
    )
