"""
CareerPilot AI — Pydantic Schemas
API request/response models. Kept simple — personal tool, no pagination wrappers needed.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ─── Profile ────────────────────────────────────────────────────────────────

class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = "Hyderabad, India"
    summary: Optional[str] = None
    skills: Optional[list[str]] = Field(default_factory=lambda: [
        "AEM", "Adobe Experience Manager", "EDS", "Edge Delivery Services",
        "Java", "Sling", "OSGi", "HTL", "AEM as Cloud Service", "Maven", "CI/CD",
    ])
    experience_years: Optional[float] = 8.0
    current_role: Optional[str] = "AEM Developer"
    target_role: Optional[str] = "AEM Architect"
    expected_salary_min: Optional[int] = 2_000_000
    expected_salary_max: Optional[int] = 3_500_000
    preferred_locations: Optional[list[str]] = Field(
        default_factory=lambda: ["Hyderabad", "Remote", "Bangalore", "Pune"]
    )
    remote_preference: Optional[str] = "any"  # remote/hybrid/onsite/any
    notice_period: Optional[str] = "60_days"


class ProfileUpdate(ProfileBase):
    """All fields optional for partial update."""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[list[str]] = None
    experience_years: Optional[float] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    preferred_locations: Optional[list[str]] = None
    remote_preference: Optional[str] = None
    notice_period: Optional[str] = None
    resume_text: Optional[str] = None


class ProfileResponse(ProfileBase):
    id: int
    resume_text: Optional[str] = None
    resume_file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    """Response after resume upload and parsing."""
    message: str
    updated_fields: list[str] = []
    skills_count: int = 0
    experience_years: Optional[float] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    resume_text_length: int = 0
    file_saved: Optional[str] = None


class ResumeSearchQueriesResponse(BaseModel):
    """Response with search queries generated from resume."""
    has_resume: bool
    queries: list[dict] = []
    skills_used: list[str] = []
    target_role: Optional[str] = None
    experience_years: Optional[float] = None


# ─── Company ────────────────────────────────────────────────────────────────

class CompanyResponse(BaseModel):
    id: int
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    research_notes: Optional[str] = None
    is_aem_hirer: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Job ────────────────────────────────────────────────────────────────────

class JobSearchRequest(BaseModel):
    """Request body for searching jobs."""
    query: str = Field(..., min_length=2, max_length=500, description="Search query, e.g. 'AEM developer'")
    location: Optional[str] = "Hyderabad, India"
    country: Optional[str] = "in"
    remote_only: bool = False
    date_posted: Optional[str] = None  # today/week/month/any
    max_results: int = Field(default=20, ge=1, le=50)


class JobResponse(BaseModel):
    id: int
    source: str
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    title: str
    company_id: Optional[int] = None
    company_name: str
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = "INR"
    salary_period: Optional[str] = "yearly"
    job_type: Optional[str] = None
    is_remote: bool = False
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills_required: Optional[list[str]] = None
    experience_required: Optional[str] = None
    posted_date: Optional[datetime] = None
    match_score: Optional[float] = None
    match_strengths: Optional[list[str]] = None
    match_weaknesses: Optional[list[str]] = None
    match_recommendations: Optional[list[str]] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    salary_display: Optional[str] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Paginated job list."""
    total: int
    jobs: list[JobResponse]
    page: int = 1
    per_page: int = 20


class JobScoreRequest(BaseModel):
    """Request to score a specific job."""
    job_id: int
    force_rescore: bool = False  # Re-score even if already scored


# ─── Application ────────────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    job_id: int
    status: str = "saved"
    notes: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    next_followup: Optional[datetime] = None
    response_notes: Optional[str] = None
    response_type: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = {
                "not_applied", "saved", "applying", "applied",
                "interview_scheduled", "interview_done",
                "offer", "rejected", "withdrawn", "expired",
            }
            if v not in valid:
                raise ValueError(f"Invalid status: {v}. Must be one of {valid}")
        return v


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    status: str
    applied_at: Optional[datetime] = None
    resume_version: Optional[str] = None
    cover_letter_path: Optional[str] = None
    notes: Optional[str] = None
    rating: Optional[int] = None
    next_followup: Optional[datetime] = None
    followup_count: int = 0
    response_notes: Optional[str] = None
    response_type: Optional[str] = None
    response_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Joined data
    job: Optional[JobResponse] = None

    model_config = {"from_attributes": True}


# ─── Cover Letter ───────────────────────────────────────────────────────────

class CoverLetterGenerate(BaseModel):
    job_id: int
    tone: Optional[str] = "professional"  # professional/casual/enthusiastic


class CoverLetterResponse(BaseModel):
    id: int
    job_id: int
    content: str
    file_path: Optional[str] = None
    model_used: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Interview Prep ─────────────────────────────────────────────────────────

class InterviewPrepRequest(BaseModel):
    job_id: int
    focus_areas: Optional[list[str]] = None  # e.g. ["AEM architecture", "system design"]


class InterviewPrepResponse(BaseModel):
    id: int
    job_id: int
    company_id: Optional[int] = None
    questions: str          # JSON array
    tips: Optional[str] = None
    salary_negotiation_tips: Optional[str] = None
    model_used: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Search History ─────────────────────────────────────────────────────────

class SearchHistoryResponse(BaseModel):
    id: int
    query: str
    filters: Optional[str] = None
    results_count: Optional[int] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Activity Log ───────────────────────────────────────────────────────────

class ActivityLogResponse(BaseModel):
    id: int
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Settings ───────────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    telegram_chat_id: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    default_search_queries: Optional[list[str]] = None
    default_location: Optional[str] = None
    min_salary: Optional[int] = None
    remote_only: Optional[bool] = None
    job_alerts_enabled: Optional[bool] = None
    alert_frequency: Optional[str] = None
    auto_score_jobs: Optional[bool] = None
    llm_provider: Optional[str] = None
    google_sheets_sync: Optional[bool] = None
    google_sheets_spreadsheet_id: Optional[str] = None


class SettingsResponse(BaseModel):
    id: int
    telegram_chat_id: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    default_search_queries: Optional[list[str]] = None
    default_location: Optional[str] = None
    min_salary: Optional[int] = None
    remote_only: bool = False
    job_alerts_enabled: bool = True
    alert_frequency: Optional[str] = "daily"
    auto_score_jobs: bool = True
    llm_provider: Optional[str] = "ollama"
    google_sheets_sync: bool = False
    google_sheets_spreadsheet_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Health Check ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    database: str = "connected"
    ollama: str = "unknown"
    gemini: str = "unknown"


# ─── Generic Message ────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
