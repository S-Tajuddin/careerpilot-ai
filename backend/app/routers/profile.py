"""
CareerPilot AI — Profile Router
CRUD for the single-user profile (id=1).
Resume upload, parsing, and resume-based job search.
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Profile, Job
from app.schemas import ProfileResponse, ProfileUpdate, MessageResponse
from app.services.resume_parser import resume_parser

router = APIRouter()


def _profile_to_response(p: Profile) -> ProfileResponse:
    """Convert ORM Profile to response schema with JSON fields parsed."""
    skills = []
    if p.skills:
        try:
            skills = json.loads(p.skills) if isinstance(p.skills, str) else p.skills
        except (json.JSONDecodeError, TypeError):
            skills = []

    preferred_locations = []
    if p.preferred_locations:
        try:
            preferred_locations = (
                json.loads(p.preferred_locations)
                if isinstance(p.preferred_locations, str)
                else p.preferred_locations
            )
        except (json.JSONDecodeError, TypeError):
            preferred_locations = []

    return ProfileResponse(
        id=p.id,
        full_name=p.full_name,
        email=p.email,
        phone=p.phone,
        location=p.location,
        summary=p.summary,
        skills=skills,
        experience_years=p.experience_years,
        current_role=p.current_role,
        target_role=p.target_role,
        expected_salary_min=p.expected_salary_min,
        expected_salary_max=p.expected_salary_max,
        preferred_locations=preferred_locations,
        remote_preference=p.remote_preference,
        notice_period=p.notice_period,
        resume_text=p.resume_text,
        resume_file_path=p.resume_file_path,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _ensure_profile(db: Session) -> Profile:
    """Get or create the single profile row (id=1)."""
    profile = db.query(Profile).filter(Profile.id == 1).first()
    if not profile:
        profile = Profile(id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    """Get your profile."""
    profile = _ensure_profile(db)
    return _profile_to_response(profile)


@router.put("/", response_model=ProfileResponse)
def update_profile(updates: ProfileUpdate, db: Session = Depends(get_db)):
    """Update your profile (partial update supported)."""
    profile = _ensure_profile(db)

    update_data = updates.model_dump(exclude_unset=True)

    # Handle JSON fields — convert lists to JSON strings
    if "skills" in update_data and isinstance(update_data["skills"], list):
        update_data["skills"] = json.dumps(update_data["skills"])
    if "preferred_locations" in update_data and isinstance(update_data["preferred_locations"], list):
        update_data["preferred_locations"] = json.dumps(update_data["preferred_locations"])

    for key, value in update_data.items():
        if hasattr(profile, key):
            setattr(profile, key, value)

    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)

    return _profile_to_response(profile)


@router.post("/resume-upload")
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    db: Session = Depends(get_db),
):
    """
    Upload and parse a resume file.
    Supports PDF, DOCX, and TXT formats.
    The resume is parsed with Gemini Flash to extract skills, experience, etc.
    Profile is auto-updated and all existing jobs are re-scored.
    """
    profile = _ensure_profile(db)

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "docx", "doc", "txt"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: .{ext}. Please upload PDF, DOCX, or TXT.",
        )

    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    # Validate file size (max 10MB)
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    if len(file_content) < 100:
        raise HTTPException(status_code=400, detail="File appears empty or too small.")

    # Process resume
    try:
        result = await resume_parser.process_resume_upload(
            file_content=file_content,
            filename=file.filename,
            profile=profile,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {e}")

    return {
        "message": "Resume uploaded and parsed successfully!",
        "details": result,
        "profile": _profile_to_response(profile),
    }


@router.get("/resume-status")
def get_resume_status(db: Session = Depends(get_db)):
    """Get resume upload status."""
    profile = _ensure_profile(db)
    return resume_parser.get_resume_status(profile)


@router.get("/resume-search-queries")
def get_resume_search_queries(db: Session = Depends(get_db)):
    """
    Generate smart search queries based on the uploaded resume.
    Returns a list of {query, location, label} dicts.
    """
    profile = _ensure_profile(db)

    if not profile.resume_text:
        return {
            "has_resume": False,
            "queries": [],
            "message": "Upload your resume first to generate personalized search queries.",
        }

    queries = resume_parser.generate_search_queries_from_resume(profile)

    return {
        "has_resume": True,
        "queries": queries,
        "skills_used": profile.skills_list if hasattr(profile, 'skills_list') else [],
        "target_role": profile.target_role,
        "experience_years": profile.experience_years,
    }


@router.post("/resume-text", response_model=MessageResponse)
def update_resume_text(resume_text: str, db: Session = Depends(get_db)):
    """Update the parsed resume text (used for AI matching and tailoring)."""
    profile = _ensure_profile(db)
    profile.resume_text = resume_text
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    return MessageResponse(message="Resume text updated")


@router.delete("/resume")
def delete_resume(db: Session = Depends(get_db)):
    """Remove uploaded resume and reset resume-related profile fields."""
    profile = _ensure_profile(db)

    # Delete file if exists
    if profile.resume_file_path:
        from pathlib import Path
        try:
            Path(profile.resume_file_path).unlink(missing_ok=True)
        except Exception:
            pass

    profile.resume_text = None
    profile.resume_file_path = None
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Resume removed. Profile fields preserved."}


@router.get("/salary-calculator")
def salary_calculator(
    ctc: float = 0,
    db: Session = Depends(get_db),
):
    """
    India CTC → In-hand salary calculator.
    Given CTC in LPA, calculate approximate monthly in-hand.
    """
    if ctc <= 0:
        return {"error": "Provide CTC in LPA, e.g. ctc=25"}

    ctc_inr = ctc * 100000  # Convert LPA to INR/year

    # Standard India deductions
    basic = ctc_inr * 0.40           # 40% of CTC as basic
    hra = basic * 0.50               # 50% of basic (metro)
    pf_employee = basic * 0.12       # 12% PF employee
    pf_employer = basic * 0.12       # 12% PF employer (part of CTC)
    professional_tax = 2500           # ~₹200/month

    # Simplified tax calculation (old regime approximation)
    taxable = ctc_inr - 50000         # Standard deduction
    tax = 0
    if taxable > 1000000:
        tax = (taxable - 1000000) * 0.30 + 112500
    elif taxable > 500000:
        tax = (taxable - 500000) * 0.20 + 12500
    elif taxable > 250000:
        tax = (taxable - 250000) * 0.05
    else:
        tax = 0

    # 4% cess
    tax = tax * 1.04 if tax > 0 else 0

    annual_in_hand = ctc_inr - pf_employee - professional_tax - tax
    monthly_in_hand = annual_in_hand / 12

    return {
        "ctc_lpa": ctc,
        "ctc_inr_yearly": ctc_inr,
        "breakdown": {
            "basic_salary": basic,
            "hra": hra,
            "pf_employee": pf_employee,
            "pf_employer": pf_employer,
            "professional_tax_yearly": professional_tax,
            "income_tax_yearly": round(tax),
        },
        "monthly_in_hand": round(monthly_in_hand),
        "annual_in_hand": round(annual_in_hand),
        "note": "Approximate calculation using old tax regime. Actual may vary based on investments, deductions, and company structure.",
    }
