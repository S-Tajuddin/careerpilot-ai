"""
CareerPilot AI — SQLAlchemy ORM Models
Mirrors the SQLite schema from alembic/schema.sql.
One user — profile is a single-row table.
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Integer, Float, String, Text,
    ForeignKey, Index, UniqueConstraint, event,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ─── Helper: JSON column accessor ───────────────────────────────────────────

class JsonColumn:
    """Mixin to auto-serialize/deserialize JSON text columns."""
    # Subclasses define: _json_field = "column_name"
    _json_field: str = ""

    def _get_json(self) -> list:
        raw = getattr(self, self._json_field, None)
        if raw is None:
            return []
        if isinstance(raw, list):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    def _set_json(self, value: list) -> None:
        if isinstance(value, str):
            # Already a JSON string — store as-is
            setattr(self, self._json_field, value)
        else:
            setattr(self, self._json_field, json.dumps(value) if value else "[]")


# ─── Profile ────────────────────────────────────────────────────────────────

class Profile(Base, JsonColumn):
    """Your profile — single row (id=1)."""
    __tablename__ = "profile"
    _json_field = "skills"

    id = Column(Integer, primary_key=True, default=1)
    full_name = Column(String(200))
    email = Column(String(200))
    phone = Column(String(50))
    location = Column(String(200), default="Hyderabad, India")
    summary = Column(Text)
    skills = Column(Text)                       # JSON array
    experience_years = Column(Float, default=8.0)
    current_role = Column(String(200), default="AEM Developer")
    target_role = Column(String(200), default="AEM Architect")
    expected_salary_min = Column(Integer, default=2_000_000)   # 20 LPA
    expected_salary_max = Column(Integer, default=3_500_000)   # 35 LPA
    preferred_locations = Column(Text)           # JSON array
    remote_preference = Column(String(50), default="any")  # remote/hybrid/onsite/any
    notice_period = Column(String(50), default="60_days")
    resume_text = Column(Text)
    resume_file_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def skills_list(self) -> list[str]:
        return self._get_json()

    @skills_list.setter
    def skills_list(self, value: list[str]) -> None:
        self._set_json(value)

    @property
    def preferred_locations_list(self) -> list[str]:
        raw = self.preferred_locations
        if not raw:
            return []
        if isinstance(raw, list):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    @preferred_locations_list.setter
    def preferred_locations_list(self, value: list[str]) -> None:
        if isinstance(value, str):
            self.preferred_locations = value
        else:
            self.preferred_locations = json.dumps(value) if value else "[]"


# ─── Companies ──────────────────────────────────────────────────────────────

class Company(Base):
    """Companies — seeded with 20 known AEM hiring companies."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    website = Column(String(500))
    industry = Column(String(200))
    size = Column(String(50))                   # startup/mid/large/enterprise
    location = Column(String(200))
    description = Column(Text)
    research_notes = Column(Text)               # AI-generated
    is_aem_hirer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("Job", back_populates="company")


# ─── Jobs ───────────────────────────────────────────────────────────────────

class Job(Base, JsonColumn):
    """Jobs from all sources, deduplicated."""
    __tablename__ = "jobs"
    _json_field = "skills_required"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)     # jsearch/adzuna/greenhouse/lever/manual
    source_id = Column(String(200))
    source_url = Column(String(1000))
    title = Column(String(500), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    company_name = Column(String(200), nullable=False)
    location = Column(String(300))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(String(10), default="INR")
    salary_period = Column(String(20), default="yearly")
    job_type = Column(String(50))                   # full_time/part_time/contract
    is_remote = Column(Boolean, default=False)
    description = Column(Text)
    requirements = Column(Text)
    skills_required = Column(Text)                   # JSON array
    experience_required = Column(String(200))
    posted_date = Column(DateTime)
    expiry_date = Column(DateTime)
    match_score = Column(Float)                      # 0-100
    match_strengths = Column(Text)                   # JSON array
    match_weaknesses = Column(Text)                  # JSON array
    match_recommendations = Column(Text)              # JSON array
    embedding_id = Column(String(200))               # ChromaDB doc ID
    is_active = Column(Boolean, default=True)
    canonical_job_id = Column(Integer)               # Links duplicate jobs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="jobs")
    application = relationship("Application", back_populates="job", uselist=False)
    cover_letters = relationship("CoverLetter", back_populates="job")
    interview_preps = relationship("InterviewPrep", back_populates="job")

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_job_source_id"),
        Index("idx_jobs_source", "source"),
        Index("idx_jobs_company", "company_name"),
        Index("idx_jobs_active", "is_active"),
        Index("idx_jobs_score", "match_score"),
        Index("idx_jobs_posted", "posted_date"),
        Index("idx_jobs_remote", "is_remote"),
        Index("idx_jobs_canonical", "canonical_job_id"),
    )

    @property
    def skills_required_list(self) -> list[str]:
        return self._get_json()

    @skills_required_list.setter
    def skills_required_list(self, value: list[str]) -> None:
        self._set_json(value)

    @property
    def match_strengths_list(self) -> list[str]:
        raw = self.match_strengths
        if not raw:
            return []
        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return []

    @match_strengths_list.setter
    def match_strengths_list(self, value: list[str]) -> None:
        self.match_strengths = json.dumps(value) if value else "[]"

    @property
    def match_weaknesses_list(self) -> list[str]:
        raw = self.match_weaknesses
        if not raw:
            return []
        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return []

    @match_weaknesses_list.setter
    def match_weaknesses_list(self, value: list[str]) -> None:
        self.match_weaknesses = json.dumps(value) if value else "[]"

    @property
    def match_recommendations_list(self) -> list[str]:
        raw = self.match_recommendations
        if not raw:
            return []
        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return []

    @match_recommendations_list.setter
    def match_recommendations_list(self, value: list[str]) -> None:
        self.match_recommendations = json.dumps(value) if value else "[]"

    def salary_display(self) -> str:
        """Human-readable salary string."""
        if not self.salary_min and not self.salary_max:
            return "Not disclosed"
        curr = "₹" if self.salary_currency == "INR" else "$"
        if self.salary_min and self.salary_max:
            if self.salary_currency == "INR":
                min_l = self.salary_min / 100000
                max_l = self.salary_max / 100000
                return f"₹{min_l:.0f}-{max_l:.0f} LPA"
            else:
                min_k = self.salary_min / 1000
                max_k = self.salary_max / 1000
                return f"${min_k:.0f}K-${max_k:.0f}K"
        if self.salary_min:
            if self.salary_currency == "INR":
                return f"₹{self.salary_min/100000:.0f}+ LPA"
            return f"${self.salary_min/1000:.0f}K+"
        return "Not disclosed"


# ─── Applications ───────────────────────────────────────────────────────────

class Application(Base):
    """Application tracking — one row per job."""
    __tablename__ = "applications"

    # Status enum values
    STATUS_NOT_APPLIED = "not_applied"
    STATUS_SAVED = "saved"
    STATUS_APPLYING = "applying"
    STATUS_APPLIED = "applied"
    STATUS_INTERVIEW_SCHEDULED = "interview_scheduled"
    STATUS_INTERVIEW_DONE = "interview_done"
    STATUS_OFFER = "offer"
    STATUS_REJECTED = "rejected"
    STATUS_WITHDRAWN = "withdrawn"
    STATUS_EXPIRED = "expired"

    ALL_STATUSES = [
        STATUS_NOT_APPLIED, STATUS_SAVED, STATUS_APPLYING, STATUS_APPLIED,
        STATUS_INTERVIEW_SCHEDULED, STATUS_INTERVIEW_DONE,
        STATUS_OFFER, STATUS_REJECTED, STATUS_WITHDRAWN, STATUS_EXPIRED,
    ]

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), unique=True)
    status = Column(String(50), default=STATUS_NOT_APPLIED)
    applied_at = Column(DateTime)
    resume_version = Column(String(200))
    cover_letter_path = Column(String(500))
    notes = Column(Text)
    rating = Column(Integer)                       # 1-5
    next_followup = Column(DateTime)
    followup_count = Column(Integer, default=0)
    response_notes = Column(Text)
    response_type = Column(String(50))             # auto_reply/recruiter_email/interview_invite/rejection/offer
    response_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("Job", back_populates="application")

    __table_args__ = (
        Index("idx_applications_status", "status"),
        Index("idx_applications_followup", "next_followup"),
    )


# ─── Cover Letters ──────────────────────────────────────────────────────────

class CoverLetter(Base):
    """Generated cover letters."""
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    file_path = Column(String(500))
    model_used = Column(String(100))               # ollama:qwen3:8b or gemini:flash
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="cover_letters")


# ─── Interview Prep ─────────────────────────────────────────────────────────

class InterviewPrep(Base):
    """AI-generated interview preparation material."""
    __tablename__ = "interview_prep"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    questions = Column(Text, nullable=False)        # JSON array
    tips = Column(Text)                             # JSON
    salary_negotiation_tips = Column(Text)
    model_used = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="interview_preps")
    company = relationship("Company")


# ─── Search History ─────────────────────────────────────────────────────────

class SearchHistory(Base):
    """Log of job searches performed."""
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(500), nullable=False)
    filters = Column(Text)                          # JSON
    results_count = Column(Integer)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Activity Log ───────────────────────────────────────────────────────────

class ActivityLog(Base):
    """Audit trail of all actions."""
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(100), nullable=False)    # job_found, job_scored, application_sent, etc.
    entity_type = Column(String(50))                # job, application, resume, cover_letter
    entity_id = Column(Integer)
    details = Column(Text)                          # JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_activity_action", "action"),
        Index("idx_activity_created", "created_at"),
    )


# ─── Settings ───────────────────────────────────────────────────────────────

class Settings(Base, JsonColumn):
    """App settings — single row (id=1)."""
    __tablename__ = "settings"
    _json_field = "default_search_queries"

    id = Column(Integer, primary_key=True, default=1)
    telegram_chat_id = Column(String(200))
    telegram_bot_token = Column(String(200))
    default_search_queries = Column(Text)           # JSON array
    default_location = Column(String(200), default="Hyderabad, India")
    min_salary = Column(Integer, default=2_000_000)
    remote_only = Column(Boolean, default=False)
    job_alerts_enabled = Column(Boolean, default=True)
    alert_frequency = Column(String(20), default="daily")
    auto_score_jobs = Column(Boolean, default=True)
    llm_provider = Column(String(20), default="ollama")
    google_sheets_sync = Column(Boolean, default=False)
    google_sheets_spreadsheet_id = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def default_search_queries_list(self) -> list[str]:
        return self._get_json()

    @default_search_queries_list.setter
    def default_search_queries_list(self, value: list[str]) -> None:
        self._set_json(value)
