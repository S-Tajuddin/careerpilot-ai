"""
CareerPilot AI — Cover Letter Generation Service
Uses Gemini Flash to generate personalized cover letters
tailored to specific job postings.

Design Principles:
  - Gemini Flash for fast, high-quality output (~2-3s)
  - Uses profile + job context for personalization
  - Never fabricates experience — only highlights what's in the resume/profile
  - Professional tone, AEM/EDS industry-aware
  - India-first: CTC references, notice period awareness
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings, COVER_LETTERS_DIR
from app.models import CoverLetter, Job, Profile
from app.services.llm import llm_service


class CoverLetterService:
    """
    Generate cover letters using Gemini Flash.
    Each cover letter is tailored to a specific job posting.
    """

    def __init__(self):
        self.cover_letters_dir = COVER_LETTERS_DIR
        self.cover_letters_dir.mkdir(parents=True, exist_ok=True)

    async def generate_cover_letter(
        self,
        job: Job,
        profile: Profile,
        db: Session,
        tone: str = "professional",
    ) -> CoverLetter:
        """
        Generate a cover letter for a specific job.
        Returns a CoverLetter ORM object (saved to DB + file).

        Args:
            job: The Job to generate a cover letter for
            profile: User's profile (source of truth for experience/skills)
            db: Database session
            tone: professional/casual/enthusiastic
        """
        # Build the prompt with job + profile context
        prompt = self._build_prompt(job, profile, tone)

        # Generate using Gemini Flash (interactive task)
        response, model_used = await llm_service.generate(
            prompt=prompt,
            system=self._system_prompt(tone),
            task_type="interactive",
            temperature=0.4,
            max_tokens=3000,
        )

        # Post-process the response
        content = self._post_process(response)

        if not content:
            raise ValueError("LLM returned empty cover letter — try again")

        # Save to file
        filename = self._generate_filename(job, profile)
        file_path = self.cover_letters_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Save to DB
        cover_letter = CoverLetter(
            job_id=job.id,
            content=content,
            file_path=str(file_path),
            model_used=model_used,
            created_at=datetime.now(timezone.utc),
        )
        db.add(cover_letter)
        db.commit()
        db.refresh(cover_letter)

        return cover_letter

    def get_cover_letters_for_job(self, job_id: int, db: Session) -> list[CoverLetter]:
        """Get all cover letters generated for a specific job."""
        return db.query(CoverLetter).filter(
            CoverLetter.job_id == job_id
        ).order_by(CoverLetter.created_at.desc()).all()

    def get_cover_letter_by_id(self, cover_letter_id: int, db: Session) -> Optional[CoverLetter]:
        """Get a specific cover letter by ID."""
        return db.query(CoverLetter).filter(
            CoverLetter.id == cover_letter_id
        ).first()

    def _build_prompt(self, job: Job, profile: Profile, tone: str) -> str:
        """Build the cover letter generation prompt."""

        skills_list = profile.skills_list if hasattr(profile, 'skills_list') else []
        job_skills = job.skills_required_list if hasattr(job, 'skills_required_list') else []

        # Extract relevant experience from resume text
        resume_excerpt = ""
        if profile.resume_text:
            # Take first 3000 chars of resume for context
            resume_excerpt = profile.resume_text[:3000]

        salary_display = job.salary_display() if hasattr(job, 'salary_display') else "Not disclosed"

        tone_descriptions = {
            "professional": "formal and professional — suitable for enterprise companies like Accenture, Infosys, Adobe",
            "casual": "warm but professional — suitable for startups and mid-size companies",
            "enthusiastic": "highly enthusiastic and passionate — shows strong motivation for this specific role",
        }
        tone_desc = tone_descriptions.get(tone, tone_descriptions["professional"])

        prompt = f"""Generate a personalized cover letter for this job application.

═══ JOB POSTING ═══
Title: {job.title}
Company: {job.company_name}
Location: {job.location or 'Not specified'}
Remote: {'Yes' if job.is_remote else 'No'}
Salary: {salary_display}
Job Type: {job.job_type or 'Full-time'}
Key Skills Required: {', '.join(job_skills[:15]) or 'Not specified'}
Experience Required: {job.experience_required or 'Not specified'}

Job Description:
{job.description[:2000] if job.description else 'No description available'}

═══ MY PROFILE ═══
Name: {profile.full_name or 'Candidate'}
Current Role: {profile.current_role or 'AEM Developer'}
Target Role: {profile.target_role or 'AEM Architect'}
Experience: {profile.experience_years or 8} years
Key Skills: {', '.join(skills_list[:20])}
Location: {profile.location or 'Hyderabad, India'}
Remote Preference: {profile.remote_preference or 'any'}
Notice Period: {profile.notice_period or '60 days' if profile.notice_period else '60 days'}

{f'''═══ MY RESUME EXCERPT ═══
{resume_excerpt}
''' if resume_excerpt else ''}

═══ INSTRUCTIONS ═══
1. Write a cover letter that is {tone_desc}.
2. ONLY reference skills, experience, and projects that are ACTUALLY in my profile/resume above.
3. NEVER fabricate or invent experience, projects, or skills I don't have.
4. Highlight how my AEM/EDS experience specifically matches the job requirements.
5. If the job mentions specific technologies I know, emphasize those.
6. Keep it concise — 3-4 paragraphs, under 400 words.
7. For Indian companies: mention notice period ({profile.notice_period or '60 days'}) naturally.
8. For remote roles: express enthusiasm for remote/hybrid work.
9. Start with a strong opening that references the specific role and company.
10. Close with a call to action for an interview.

Output ONLY the cover letter text. No headers, no subject line, no "Dear Hiring Manager" prefix — start directly with the greeting. Use "Dear Hiring Team" or "Dear [Company Name] Team" for the greeting."""

        return prompt

    def _system_prompt(self, tone: str) -> str:
        """System prompt for cover letter generation."""
        return f"""You are an expert AEM/EDS career advisor and cover letter writer.
You write cover letters for Adobe Experience Manager and Edge Delivery Services professionals.
You NEVER fabricate experience or skills — you only work with what the candidate actually has.
You are concise, impactful, and industry-specific.
Tone: {tone}.
Output plain text only — no markdown, no HTML, no formatting codes."""

    def _post_process(self, text: str) -> str:
        """Clean up the LLM response."""
        if not text:
            return ""

        # Remove markdown code fences if present
        text = re.sub(r'^```(?:text|markdown)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)

        # Remove any "Subject:" or "Re:" lines at the top
        text = re.sub(r'^(Subject|Re|Title):\s*.*\n?', '', text, flags=re.IGNORECASE)

        # Remove excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _generate_filename(self, job: Job, profile: Profile) -> str:
        """Generate a safe filename for the cover letter."""
        company = re.sub(r'[^\w\s-]', '', job.company_name or 'unknown').strip().replace(' ', '_')[:30]
        title = re.sub(r'[^\w\s-]', '', job.title or 'role').strip().replace(' ', '_')[:30]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"cover_letter_{company}_{title}_{timestamp}.txt"


# Singleton
cover_letter_service = CoverLetterService()
