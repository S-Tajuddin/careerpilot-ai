"""
CareerPilot AI — Resume Tailoring Service
Uses Gemini Flash to tailor the user's resume for a specific job posting.

CRITICAL DESIGN PRINCIPLE:
  Resume tailoring = REORGANIZING + EMPHASIZING existing content.
  NEVER fabricate experience, skills, or projects the user doesn't have.
  The tailor can:
    - Reorder skills to match job requirements
    - Emphasize relevant experience in the summary
    - Highlight matching projects at the top
    - Adjust wording to use job-specific terminology
    - Strengthen action verbs
  The tailor CANNOT:
    - Add skills not in the original resume
    - Invent projects or companies
    - Fabricate years of experience
    - Create certifications the user doesn't have
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings, EXPORTS_DIR, RESUMES_DIR
from app.models import Job, Profile
from app.services.llm import llm_service


class ResumeTailorService:
    """
    Tailor the user's resume for a specific job posting.
    Reorganizes and emphasizes existing content — never fabricates.
    """

    def __init__(self):
        self.exports_dir = EXPORTS_DIR
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    async def tailor_resume(
        self,
        job: Job,
        profile: Profile,
        db: Session,
    ) -> dict:
        """
        Generate a tailored version of the user's resume for a specific job.

        Args:
            job: The Job to tailor the resume for
            profile: User's profile (source of truth)
            db: Database session

        Returns:
            dict with: file_path, content, job_id, model_used
        """
        if not profile.resume_text:
            raise ValueError("No resume uploaded — upload your resume first")

        # Build the tailoring prompt
        prompt = self._build_prompt(job, profile)

        # Generate using Gemini Flash (interactive task — needs quality)
        response, model_used = await llm_service.generate(
            prompt=prompt,
            system=self._system_prompt(),
            task_type="interactive",
            temperature=0.3,
            max_tokens=5000,
        )

        # Post-process
        content = self._post_process(response)

        if not content:
            raise ValueError("LLM returned empty tailored resume — try again")

        # Save to file
        filename = self._generate_filename(job, profile)
        file_path = self.exports_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "file_path": str(file_path),
            "content": content,
            "job_id": job.id,
            "job_title": job.title,
            "company_name": job.company_name,
            "model_used": model_used,
            "content_length": len(content),
        }

    def get_tailored_resume_for_job(self, job_id: int) -> Optional[dict]:
        """
        Check if a tailored resume exists for a job.
        Searches the exports directory for matching files.
        """
        # Look for files matching the job ID pattern
        for f in self.exports_dir.glob(f"tailored_resume_*_job{job_id}_*.txt"):
            try:
                content = f.read_text(encoding="utf-8")
                return {
                    "file_path": str(f),
                    "content": content,
                    "job_id": job_id,
                    "content_length": len(content),
                }
            except Exception:
                continue
        return None

    def _build_prompt(self, job: Job, profile: Profile) -> str:
        """Build the resume tailoring prompt."""

        skills_list = profile.skills_list if hasattr(profile, 'skills_list') else []
        job_skills = job.skills_required_list if hasattr(job, 'skills_required_list') else []
        salary_display = job.salary_display() if hasattr(job, 'salary_display') else "Not disclosed"

        prompt = f"""You are tailoring a candidate's resume for a specific job. Your job is to REORGANIZE and REEMPHASIZE their existing resume content to better match this job posting.

═══ JOB POSTING ═══
Title: {job.title}
Company: {job.company_name}
Location: {job.location or 'Not specified'}
Remote: {'Yes' if job.is_remote else 'No'}
Salary: {salary_display}
Key Skills Required: {', '.join(job_skills[:15]) or 'Not specified'}
Experience Required: {job.experience_required or 'Not specified'}

Job Description:
{job.description[:3000] if job.description else 'No description available'}

═══ CANDIDATE'S ORIGINAL RESUME ═══
{profile.resume_text[:8000]}

═══ CANDIDATE'S SKILLS ═══
{', '.join(skills_list[:25])}

═══ TAILORING RULES (CRITICAL) ═══
1. REORGANIZE: Reorder skills, projects, and experience sections to put the MOST RELEVANT items first, matching the job requirements.
2. EMPHASIZE: Strengthen descriptions of relevant experience. Use stronger action verbs for relevant projects.
3. KEYWORD ALIGNMENT: If the job uses different terminology for the same concept (e.g., "AEM Sites" vs "AEM Sites & Assets"), adjust wording to match — but ONLY if the candidate actually has that experience.
4. SUMMARY: Rewrite the professional summary to directly address this specific role and company.
5. REORDER SKILLS: Put skills that match the job requirements at the TOP of the skills list.
6. HIGHLIGHT MATCHING PROJECTS: If the candidate has projects that use technologies mentioned in the job, move those projects to the top and expand their descriptions slightly.

═══ THOU SHALT NOT ═══
- NEVER add skills the candidate doesn't have
- NEVER invent projects, companies, or experience
- NEVER fabricate certifications or education
- NEVER change dates of employment
- NEVER add technologies not mentioned in the original resume
- NEVER inflate years of experience

═══ OUTPUT FORMAT ═══
Output the complete tailored resume as plain text, formatted for readability:
- Use clear section headers (PROFESSIONAL SUMMARY, SKILLS, EXPERIENCE, EDUCATION, CERTIFICATIONS)
- Keep the same structure as the original resume
- Only the ORDER and EMPHASIS should change, not the facts

Output ONLY the tailored resume text. No markdown, no HTML, no commentary."""

        return prompt

    def _system_prompt(self) -> str:
        """System prompt for resume tailoring."""
        return """You are an expert resume writer specializing in AEM/EDS/Adobe technology careers.
You help candidates tailor their resumes for specific job postings.
Your #1 rule: NEVER fabricate experience or skills. Only reorganize and reemphasize what exists.
You are concise, professional, and effective.
Output plain text only — no markdown, no HTML, no formatting codes."""

    def _post_process(self, text: str) -> str:
        """Clean up the LLM response."""
        if not text:
            return ""

        # Remove markdown code fences
        text = re.sub(r'^```(?:text|markdown)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)

        # Remove any "Here is the tailored resume:" or similar prefixes
        text = re.sub(r'^.*?[Hh]ere\s+(is|are)\s+(the\s+)?(tailored|customized|updated)\s+resume[:.]?\s*\n*', '', text, flags=re.IGNORECASE)

        # Remove excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _generate_filename(self, job: Job, profile: Profile) -> str:
        """Generate a safe filename for the tailored resume."""
        company = re.sub(r'[^\w\s-]', '', job.company_name or 'unknown').strip().replace(' ', '_')[:30]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"tailored_resume_{company}_job{job.id}_{timestamp}.txt"


# Singleton
resume_tailor_service = ResumeTailorService()
