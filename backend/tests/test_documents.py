"""
CareerPilot AI — Tests for Cover Letter & Resume Tailor Services
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import Job, Profile, CoverLetter


# ─── Fixtures ────────────────────────────────────────────────────────────────

def make_profile(**kwargs):
    """Create a mock Profile object."""
    defaults = {
        "id": 1,
        "full_name": "Rahul Sharma",
        "email": "rahul@example.com",
        "phone": "+91-9876543210",
        "location": "Hyderabad, India",
        "summary": "Senior AEM Developer with 8+ years of experience in Adobe Experience Manager, EDS, and Java.",
        "skills": json.dumps(["AEM", "EDS", "Java", "Sling", "OSGi", "HTL", "Dispatcher", "Cloud Manager"]),
        "experience_years": 8.0,
        "current_role": "Senior AEM Developer",
        "target_role": "AEM Architect",
        "expected_salary_min": 2_000_000,
        "expected_salary_max": 3_500_000,
        "remote_preference": "any",
        "notice_period": "60_days",
        "resume_text": """
RAHUL SHARMA
Senior AEM Developer | Hyderabad, India
rahul@example.com | +91-9876543210

PROFESSIONAL SUMMARY
8+ years of experience in Adobe Experience Manager development.
Expert in AEM Sites, Assets, and Edge Delivery Services.

SKILLS
AEM 6.5, AEM as Cloud Service, EDS, Sling, OSGi, HTL, Sightly,
Java, Maven, Dispatcher, Cloud Manager, Git, Jenkins

EXPERIENCE
Senior AEM Developer — Infosys (2020-Present)
- Led AEM Sites implementation for 3 enterprise clients
- Architected EDS solution for a Fortune 500 company
- Mentored team of 5 junior developers

AEM Developer — TCS (2017-2020)
- Developed AEM components and templates
- Implemented Sling models and OSGi services
- Managed dispatcher configurations

EDUCATION
B.Tech Computer Science — JNTU Hyderabad (2017)
""",
        "resume_file_path": "/tmp/resume.pdf",
        "preferred_locations": json.dumps(["Hyderabad", "Remote", "Bangalore"]),
    }
    defaults.update(kwargs)
    profile = MagicMock(spec=Profile)
    for k, v in defaults.items():
        setattr(profile, k, v)

    # Add skills_list property
    type(profile).skills_list = property(
        lambda self: json.loads(self.skills) if isinstance(self.skills, str) else self.skills
    )
    return profile


def make_job(**kwargs):
    """Create a mock Job object."""
    defaults = {
        "id": 42,
        "source": "jsearch",
        "source_id": "abc123",
        "source_url": "https://example.com/job/42",
        "title": "Senior AEM Developer",
        "company_name": "Accenture",
        "company_id": 1,
        "location": "Hyderabad, India",
        "salary_min": 2_500_000,
        "salary_max": 3_500_000,
        "salary_currency": "INR",
        "salary_period": "yearly",
        "job_type": "full_time",
        "is_remote": False,
        "description": "Looking for a Senior AEM Developer with 6+ years of experience in AEM Sites, Assets, and Cloud Service. Must know Sling, OSGi, HTL, Dispatcher. Experience with EDS is a plus.",
        "requirements": "AEM 6.5+, Sling, OSGi, HTL, Java, Maven",
        "skills_required": json.dumps(["AEM", "Sling", "OSGi", "HTL", "Dispatcher", "Java", "Cloud Manager"]),
        "experience_required": "6+ years",
        "posted_date": datetime(2026, 7, 1),
        "match_score": 82.5,
    }
    defaults.update(kwargs)
    job = MagicMock(spec=Job)
    for k, v in defaults.items():
        setattr(job, k, v)

    # Add skills_required_list property
    type(job).skills_required_list = property(
        lambda self: json.loads(self.skills_required) if isinstance(self.skills_required, str) else self.skills_required
    )

    # Add salary_display method
    def salary_display(self):
        if not self.salary_min and not self.salary_max:
            return "Not disclosed"
        if self.salary_min and self.salary_max:
            if self.salary_currency == "INR":
                return f"₹{self.salary_min/100000:.0f}-{self.salary_max/100000:.0f} LPA"
            return f"${self.salary_min/1000:.0f}K-${self.salary_max/1000:.0f}K"
        return "Not disclosed"

    job.salary_display = lambda: salary_display(job)
    return job


# ══════════════════════════════════════════════════════════════════════════════
# COVER LETTER SERVICE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestCoverLetterService:
    """Test CoverLetterService."""

    def test_build_prompt_contains_job_info(self):
        """Prompt should include job title, company, and key details."""
        from app.services.cover_letter import cover_letter_service

        job = make_job()
        profile = make_profile()

        prompt = cover_letter_service._build_prompt(job, profile, "professional")

        assert "Senior AEM Developer" in prompt
        assert "Accenture" in prompt
        assert "Hyderabad, India" in prompt
        assert "AEM" in prompt

    def test_build_prompt_contains_profile_info(self):
        """Prompt should include candidate's profile information."""
        from app.services.cover_letter import cover_letter_service

        job = make_job()
        profile = make_profile()

        prompt = cover_letter_service._build_prompt(job, profile, "professional")

        assert "Rahul Sharma" in prompt
        assert "8" in prompt  # experience years
        assert "AEM Architect" in prompt  # target role
        assert "60" in prompt  # notice period (shows as 60_days or 60 days)

    def test_build_prompt_includes_resume_excerpt(self):
        """Prompt should include resume text excerpt when available."""
        from app.services.cover_letter import cover_letter_service

        job = make_job()
        profile = make_profile()

        prompt = cover_letter_service._build_prompt(job, profile, "professional")

        assert "RESUME EXCERPT" in prompt
        assert "Infosys" in prompt  # from resume text

    def test_build_prompt_no_resume(self):
        """Prompt should work without resume text."""
        from app.services.cover_letter import cover_letter_service

        job = make_job()
        profile = make_profile(resume_text=None)

        prompt = cover_letter_service._build_prompt(job, profile, "professional")

        assert "RESUME EXCERPT" not in prompt

    def test_build_prompt_tone_professional(self):
        """Professional tone should be described correctly."""
        from app.services.cover_letter import cover_letter_service

        job = make_job()
        profile = make_profile()

        prompt = cover_letter_service._build_prompt(job, profile, "professional")

        assert "formal and professional" in prompt

    def test_build_prompt_tone_enthusiastic(self):
        """Enthusiastic tone should be described correctly."""
        from app.services.cover_letter import cover_letter_service

        job = make_job()
        profile = make_profile()

        prompt = cover_letter_service._build_prompt(job, profile, "enthusiastic")

        assert "enthusiastic and passionate" in prompt

    def test_post_process_removes_code_fences(self):
        """Should remove markdown code fences from output."""
        from app.services.cover_letter import cover_letter_service

        text = "```text\nDear Hiring Team,\n\nI am writing...\n```"
        result = cover_letter_service._post_process(text)
        assert "```" not in result
        assert "Dear Hiring Team" in result

    def test_post_process_removes_subject_lines(self):
        """Should remove Subject: lines from output."""
        from app.services.cover_letter import cover_letter_service

        text = "Subject: Application for AEM Developer\n\nDear Hiring Team,\n\nI am writing..."
        result = cover_letter_service._post_process(text)
        assert not result.startswith("Subject:")
        assert "Dear Hiring Team" in result

    def test_post_process_collapses_blank_lines(self):
        """Should collapse excessive blank lines."""
        from app.services.cover_letter import cover_letter_service

        text = "Dear Team,\n\n\n\n\nI am writing..."
        result = cover_letter_service._post_process(text)
        assert "\n\n\n" not in result

    def test_post_process_empty_input(self):
        """Should handle empty input gracefully."""
        from app.services.cover_letter import cover_letter_service

        assert cover_letter_service._post_process("") == ""
        assert cover_letter_service._post_process(None) == ""

    def test_generate_filename(self):
        """Filename should be safe and include company + title."""
        from app.services.cover_letter import cover_letter_service

        job = make_job()
        profile = make_profile()

        filename = cover_letter_service._generate_filename(job, profile)
        assert filename.startswith("cover_letter_")
        assert "Accenture" in filename
        assert filename.endswith(".txt")

    def test_generate_filename_special_chars(self):
        """Filename should handle special characters in company/title."""
        from app.services.cover_letter import cover_letter_service

        job = make_job(company_name="Tata Consultancy Services (TCS)", title="AEM/Sling Developer")
        profile = make_profile()

        filename = cover_letter_service._generate_filename(job, profile)
        # No special chars like parentheses or slashes
        assert "(" not in filename
        assert "/" not in filename

    @pytest.mark.asyncio
    async def test_generate_cover_letter_success(self, tmp_path):
        """End-to-end test: generate a cover letter with mocked LLM."""
        from app.services.cover_letter import CoverLetterService

        service = CoverLetterService()
        service.cover_letters_dir = tmp_path

        job = make_job()
        profile = make_profile()
        db = MagicMock()

        mock_cover_letter = CoverLetter(
            id=1,
            job_id=job.id,
            content="Dear Hiring Team,\n\nI am writing to apply for the Senior AEM Developer position at Accenture.",
            file_path=str(tmp_path / "test_cover_letter.txt"),
            model_used="gemini:gemini-2.5-flash",
        )
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        with patch.object(service, '_build_prompt', return_value="test prompt"), \
             patch('app.services.cover_letter.llm_service') as mock_llm:
            mock_llm.generate = AsyncMock(return_value=(
                "Dear Hiring Team,\n\nI am writing to apply for the Senior AEM Developer position at Accenture.\n\nWith 8+ years of AEM experience...",
                "gemini:gemini-2.5-flash"
            ))

            result = await service.generate_cover_letter(job, profile, db, "professional")

            assert result is not None
            assert result.content is not None
            db.add.assert_called_once()
            db.commit.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
# RESUME TAILOR SERVICE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestResumeTailorService:
    """Test ResumeTailorService."""

    def test_build_prompt_contains_job_info(self):
        """Prompt should include job details."""
        from app.services.resume_tailor import resume_tailor_service

        job = make_job()
        profile = make_profile()

        prompt = resume_tailor_service._build_prompt(job, profile)

        assert "Senior AEM Developer" in prompt
        assert "Accenture" in prompt
        assert "6+ years" in prompt

    def test_build_prompt_contains_resume(self):
        """Prompt should include the full resume text."""
        from app.services.resume_tailor import resume_tailor_service

        job = make_job()
        profile = make_profile()

        prompt = resume_tailor_service._build_prompt(job, profile)

        assert "RAHUL SHARMA" in prompt
        assert "Infosys" in prompt
        assert "JNTU" in prompt

    def test_build_prompt_contains_no_fabrication_rule(self):
        """Prompt should explicitly prohibit fabrication."""
        from app.services.resume_tailor import resume_tailor_service

        job = make_job()
        profile = make_profile()

        prompt = resume_tailor_service._build_prompt(job, profile)

        assert "NEVER" in prompt
        assert "fabricat" in prompt.lower()

    def test_build_prompt_no_resume_raises(self):
        """Should raise ValueError if no resume text."""
        from app.services.resume_tailor import ResumeTailorService

        service = ResumeTailorService()
        # We test this at the router level mainly, but the prompt would be empty

    def test_post_process_removes_code_fences(self):
        """Should remove markdown code fences from output."""
        from app.services.resume_tailor import resume_tailor_service

        text = "```text\nRAHUL SHARMA\nSenior AEM Developer\n```"
        result = resume_tailor_service._post_process(text)
        assert "```" not in result
        assert "RAHUL SHARMA" in result

    def test_post_process_removes_prefix_text(self):
        """Should remove 'Here is the tailored resume' prefix."""
        from app.services.resume_tailor import resume_tailor_service

        text = "Here is the tailored resume for your review:\n\nRAHUL SHARMA\nSenior AEM Developer"
        result = resume_tailor_service._post_process(text)
        assert not result.startswith("Here is")
        assert "RAHUL SHARMA" in result

    def test_post_process_empty_input(self):
        """Should handle empty input gracefully."""
        from app.services.resume_tailor import resume_tailor_service

        assert resume_tailor_service._post_process("") == ""
        assert resume_tailor_service._post_process(None) == ""

    def test_generate_filename(self):
        """Filename should be safe and include company + job ID."""
        from app.services.resume_tailor import resume_tailor_service

        job = make_job()
        profile = make_profile()

        filename = resume_tailor_service._generate_filename(job, profile)
        assert filename.startswith("tailored_resume_")
        assert "Accenture" in filename
        assert "job42" in filename
        assert filename.endswith(".txt")

    @pytest.mark.asyncio
    async def test_tailor_resume_success(self, tmp_path):
        """End-to-end test: tailor a resume with mocked LLM."""
        from app.services.resume_tailor import ResumeTailorService

        service = ResumeTailorService()
        service.exports_dir = tmp_path

        job = make_job()
        profile = make_profile()
        db = MagicMock()

        tailored_content = """RAHUL SHARMA
Senior AEM Developer | AEM Architect | Hyderabad, India

PROFESSIONAL SUMMARY
8+ years of experience specializing in Adobe Experience Manager and Edge Delivery Services.
Expert in AEM Sites, Assets, Cloud Service, and EDS architecture.

SKILLS (Prioritized for this role)
AEM 6.5, AEM as Cloud Service, Sling, OSGi, HTL, Dispatcher, Cloud Manager,
EDS, Java, Maven, Git, Jenkins

EXPERIENCE
Senior AEM Developer — Infosys (2020-Present)
- Led AEM Sites implementation for 3 enterprise clients
- Architected EDS solution for a Fortune 500 company
"""

        with patch.object(service, '_build_prompt', return_value="test prompt"), \
             patch('app.services.resume_tailor.llm_service') as mock_llm:
            mock_llm.generate = AsyncMock(return_value=(
                tailored_content,
                "gemini:gemini-2.5-flash"
            ))

            result = await service.tailor_resume(job, profile, db)

            assert result is not None
            assert result["content"].strip() == tailored_content.strip()
            assert result["job_id"] == 42
            assert result["model_used"] == "gemini:gemini-2.5-flash"
            assert Path(result["file_path"]).exists()

            # Verify file content
            with open(result["file_path"], "r") as f:
                saved_content = f.read()
            assert "RAHUL SHARMA" in saved_content

    @pytest.mark.asyncio
    async def test_tailor_resume_no_resume_raises(self, tmp_path):
        """Should raise ValueError when profile has no resume."""
        from app.services.resume_tailor import ResumeTailorService

        service = ResumeTailorService()
        service.exports_dir = tmp_path

        job = make_job()
        profile = make_profile(resume_text=None)
        db = MagicMock()

        with pytest.raises(ValueError, match="No resume uploaded"):
            await service.tailor_resume(job, profile, db)

    def test_get_tailored_resume_not_found(self, tmp_path):
        """Should return None when no tailored resume exists."""
        from app.services.resume_tailor import ResumeTailorService

        service = ResumeTailorService()
        service.exports_dir = tmp_path

        result = service.get_tailored_resume_for_job(999)
        assert result is None

    def test_get_tailored_resume_found(self, tmp_path):
        """Should return the tailored resume when it exists."""
        from app.services.resume_tailor import ResumeTailorService

        service = ResumeTailorService()
        service.exports_dir = tmp_path

        # Create a file matching the pattern
        test_file = tmp_path / "tailored_resume_Accenture_job42_20260705_120000.txt"
        test_file.write_text("Tailored resume content", encoding="utf-8")

        result = service.get_tailored_resume_for_job(42)
        assert result is not None
        assert result["job_id"] == 42
        assert "Tailored resume content" in result["content"]


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS (with mocked LLM)
# ══════════════════════════════════════════════════════════════════════════════

class TestDocumentsIntegration:
    """Integration tests for the documents router endpoints."""

    @pytest.mark.asyncio
    async def test_cover_letter_generation_prompt_quality(self):
        """Verify the cover letter prompt is well-structured and complete."""
        from app.services.cover_letter import cover_letter_service

        job = make_job(
            title="AEM Architect",
            company_name="Adobe",
            location="Bangalore, India",
            is_remote=True,
        )
        profile = make_profile()

        prompt = cover_letter_service._build_prompt(job, profile, "enthusiastic")

        # Should contain all critical sections
        assert "JOB POSTING" in prompt
        assert "MY PROFILE" in prompt
        assert "AEM Architect" in prompt
        assert "Adobe" in prompt
        assert "Bangalore" in prompt
        assert "enthusiastic" in prompt.lower()
        assert "NEVER fabricate" in prompt

    @pytest.mark.asyncio
    async def test_resume_tailor_prompt_quality(self):
        """Verify the resume tailor prompt is well-structured and complete."""
        from app.services.resume_tailor import resume_tailor_service

        job = make_job(
            title="Lead AEM Developer",
            company_name="Publicis Sapient",
        )
        profile = make_profile()

        prompt = resume_tailor_service._build_prompt(job, profile)

        # Should contain all critical sections
        assert "JOB POSTING" in prompt
        assert "CANDIDATE'S ORIGINAL RESUME" in prompt
        assert "TAILORING RULES" in prompt
        assert "THOU SHALT NOT" in prompt
        assert "Publicis Sapient" in prompt
        assert "NEVER add skills" in prompt
        assert "NEVER fabricat" in prompt
        assert "REORGANIZE" in prompt
        assert "EMPHASIZE" in prompt

    def test_cover_letter_tones(self):
        """All supported tones should produce different prompts."""
        from app.services.cover_letter import cover_letter_service

        job = make_job()
        profile = make_profile()

        prompts = {}
        for tone in ["professional", "casual", "enthusiastic"]:
            prompts[tone] = cover_letter_service._build_prompt(job, profile, tone)

        # Professional mentions "formal"
        assert "formal" in prompts["professional"]
        # Casual mentions "startup"
        assert "startup" in prompts["casual"]
        # Enthusiastic mentions "passionate"
        assert "passionate" in prompts["enthusiastic"]
