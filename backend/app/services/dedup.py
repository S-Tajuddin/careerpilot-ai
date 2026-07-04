"""
CareerPilot AI — Deduplication Service
Removes duplicate jobs across sources using:
1. Exact match: (source, source_id) — handled in job_service._save_jobs
2. Title + Company fuzzy match — catches same job from different sources
3. Semantic similarity via embeddings — catches near-duplicates

When a duplicate is found:
- The job with more data (salary, description, skills) becomes the "canonical"
- Other duplicates link to it via canonical_job_id
- Only the canonical job is shown in results
"""

import json
import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Job
from app.services.embeddings import embedding_service


class DedupService:
    """
    Deduplicates jobs across and within sources.
    Three-tier approach: exact → fuzzy → semantic.
    """

    def __init__(self):
        self.similarity_threshold = settings.job_dedup_similarity_threshold  # 0.85

    async def dedup_jobs(self, db: Session, limit: int = 100) -> dict:
        """
        Run deduplication on all active jobs without canonical_job_id set.
        Returns stats about what was merged.
        """
        # Get jobs that haven't been deduped yet
        jobs = db.query(Job).filter(
            Job.is_active == True,
            Job.canonical_job_id.is_(None),
        ).order_by(Job.created_at.desc()).limit(limit).all()

        stats = {
            "total_checked": len(jobs),
            "duplicates_found": 0,
            "groups_merged": 0,
        }

        # Group jobs by normalized (title, company) for fuzzy matching
        groups: dict[str, list[Job]] = {}
        for job in jobs:
            key = self._make_group_key(job.title, job.company_name)
            if key not in groups:
                groups[key] = []
            groups[key].append(job)

        # Process each group
        for key, group_jobs in groups.items():
            if len(group_jobs) <= 1:
                continue

            # Find the best canonical job (most data)
            canonical = self._pick_canonical(group_jobs)

            # Link duplicates to canonical
            for job in group_jobs:
                if job.id == canonical.id:
                    continue

                # Verify with semantic similarity (if embeddings available)
                is_dup = await self._verify_duplicate(canonical, job)

                if is_dup:
                    job.canonical_job_id = canonical.id
                    job.is_active = False  # Hide duplicate from results
                    stats["duplicates_found"] += 1

            if any(j.canonical_job_id == canonical.id for j in group_jobs):
                stats["groups_merged"] += 1

        db.commit()
        return stats

    async def dedup_new_job(self, new_job: Job, db: Session) -> Optional[int]:
        """
        Check if a newly saved job is a duplicate of an existing one.
        Returns the canonical job ID if duplicate, None otherwise.
        """
        # 1. Check by (title, company) group
        key = self._make_group_key(new_job.title, new_job.company_name)

        # Find potential matches in DB
        potential_matches = db.query(Job).filter(
            Job.is_active == True,
            Job.id != new_job.id,
            Job.company_name.ilike(f"%{new_job.company_name or ''}%"),
        ).limit(20).all()

        for match in potential_matches:
            # Quick title similarity check
            if self._title_similarity(new_job.title, match.title) < 0.6:
                continue

            # Verify with semantic similarity
            is_dup = await self._verify_duplicate(match, new_job)
            if is_dup:
                return match.id  # This is the canonical job

        return None

    # ─── Group Key Generation ────────────────────────────────────────────

    @staticmethod
    def _make_group_key(title: str, company: str) -> str:
        """
        Create a normalized group key from title + company.
        Removes seniority, spacing, and case differences.
        """
        def normalize(text: str) -> str:
            text = (text or "").lower().strip()
            # Remove seniority modifiers
            for word in ["senior", "sr", "junior", "jr", "lead", "principal",
                         "staff", "associate", "mid", "ii", "iii", "iv"]:
                text = re.sub(rf'\b{word}\b', '', text)
            # Remove extra spaces
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        t = normalize(title)
        c = normalize(company)
        return f"{t}||{c}"

    # ─── Title Similarity ────────────────────────────────────────────────

    @staticmethod
    def _title_similarity(title1: str, title2: str) -> float:
        """
        Simple word-overlap similarity between two titles.
        Returns 0.0 - 1.0
        """
        if not title1 or not title2:
            return 0.0

        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())

        # Remove common stop words
        stops = {"the", "a", "an", "and", "or", "in", "at", "for", "of", "to", "&", "-", "/"}
        words1 -= stops
        words2 -= stops

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)  # Jaccard similarity

    # ─── Pick Canonical Job ──────────────────────────────────────────────

    @staticmethod
    def _pick_canonical(jobs: list[Job]) -> Job:
        """
        Pick the best job to be the canonical (primary) version.
        Prefer jobs with: salary info, skills, longer description, from primary source.
        """
        def score_job(job: Job) -> float:
            s = 0.0
            if job.salary_min or job.salary_max:
                s += 3.0
            if job.skills_required:
                try:
                    skills = json.loads(job.skills_required) if isinstance(job.skills_required, str) else job.skills_required
                    s += min(len(skills), 10) * 0.2
                except:
                    pass
            if job.description:
                s += min(len(job.description), 5000) / 1000
            if job.source == "jsearch":
                s += 1.0  # Primary source bonus
            if job.source_url:
                s += 0.5
            return s

        return max(jobs, key=score_job)

    # ─── Semantic Duplicate Verification ─────────────────────────────────

    async def _verify_duplicate(self, job1: Job, job2: Job) -> bool:
        """
        Verify if two jobs are duplicates using embedding similarity.
        Falls back to title+company match if embeddings unavailable.
        """
        # Quick check: if same source + source_id, definitely duplicate
        if (job1.source == job2.source and job1.source_id and
                job1.source_id == job2.source_id):
            return True

        # Try embedding similarity
        try:
            text1 = f"{job1.title} at {job1.company_name}. {job1.description[:500] if job1.description else ''}"
            text2 = f"{job2.title} at {job2.company_name}. {job2.description[:500] if job2.description else ''}"

            similarity = await embedding_service.compute_similarity(text1, text2)

            if similarity >= self.similarity_threshold:
                return True
            if similarity >= 0.7:
                # Borderline — check title similarity too
                title_sim = self._title_similarity(job1.title, job2.title)
                return title_sim >= 0.7 and similarity >= 0.75
            return False
        except Exception as e:
            # Embedding service unavailable — use heuristic
            print(f"Embedding similarity failed, using heuristic: {e}")

            # Heuristic: same company + similar title + same location
            title_sim = self._title_similarity(job1.title, job2.title)
            same_company = (job1.company_name or "").lower() == (job2.company_name or "").lower()
            same_location = (job1.location or "").lower() == (job2.location or "").lower()

            if same_company and title_sim >= 0.7:
                return True
            if same_company and same_location and title_sim >= 0.5:
                return True
            return False


# Singleton
dedup_service = DedupService()
