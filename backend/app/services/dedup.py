"""
CareerPilot AI — Deduplication Service
Removes duplicate jobs across sources using:
1. Exact match: (source, source_id) — handled in job_service._save_jobs
2. Title + Company fuzzy match — catches same job from different sources (instant)
3. Semantic similarity via embeddings — catches near-duplicates (slow, manual only)

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
    Two modes:
    - heuristic_dedup(): Fast, no API calls — used during search
    - dedup_jobs(): Full semantic dedup — used manually via API
    """

    def __init__(self):
        self.similarity_threshold = settings.job_dedup_similarity_threshold  # 0.85

    # ══════════════════════════════════════════════════════════════════════
    #  FAST: Heuristic dedup — no API calls, instant
    # ══════════════════════════════════════════════════════════════════════

    def heuristic_dedup(self, job: Job, db: Session) -> bool:
        """
        Fast heuristic-only dedup — NO embedding API calls.
        Checks title+company overlap. Runs in < 1ms.
        Returns True if job was marked as duplicate.
        Used automatically during search.
        """
        if not job.company_name:
            return False

        # Find jobs with same company
        potential_matches = db.query(Job).filter(
            Job.is_active == True,
            Job.id != job.id,
            Job.company_name.ilike(f"{job.company_name.strip()}"),
        ).limit(10).all()

        for match in potential_matches:
            title_sim = self._title_similarity(job.title, match.title)
            same_location = (job.location or "").lower() == (match.location or "").lower()

            # Strong match: same company + very similar title
            if title_sim >= 0.8:
                job.canonical_job_id = match.id
                job.is_active = False
                db.commit()
                return True

            # Same company + same location + moderately similar title
            if title_sim >= 0.6 and same_location:
                job.canonical_job_id = match.id
                job.is_active = False
                db.commit()
                return True

        return False

    # ══════════════════════════════════════════════════════════════════════
    #  SLOW: Semantic dedup — uses embeddings, for manual use only
    # ══════════════════════════════════════════════════════════════════════

    async def dedup_jobs(self, db: Session, limit: int = 100) -> dict:
        """
        Run full deduplication on active jobs — includes embedding similarity.
        SLOW — only use via manual POST /api/jobs/dedup.
        Returns stats about what was merged.
        """
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

            canonical = self._pick_canonical(group_jobs)

            for job in group_jobs:
                if job.id == canonical.id:
                    continue

                is_dup = await self._verify_duplicate(canonical, job)

                if is_dup:
                    job.canonical_job_id = canonical.id
                    job.is_active = False
                    stats["duplicates_found"] += 1

            if any(j.canonical_job_id == canonical.id for j in group_jobs):
                stats["groups_merged"] += 1

        db.commit()
        return stats

    async def dedup_new_job(self, new_job: Job, db: Session) -> Optional[int]:
        """
        Check if a newly saved job is a duplicate using embedding similarity.
        SLOW — only use for manual deep dedup.
        Returns the canonical job ID if duplicate, None otherwise.
        """
        if not new_job.company_name:
            return None

        potential_matches = db.query(Job).filter(
            Job.is_active == True,
            Job.id != new_job.id,
            Job.company_name.ilike(f"%{new_job.company_name or ''}%"),
        ).limit(20).all()

        for match in potential_matches:
            if self._title_similarity(new_job.title, match.title) < 0.6:
                continue

            is_dup = await self._verify_duplicate(match, new_job)
            if is_dup:
                return match.id

        return None

    # ─── Group Key Generation ────────────────────────────────────────────

    @staticmethod
    def _make_group_key(title: str, company: str) -> str:
        def normalize(text: str) -> str:
            text = (text or "").lower().strip()
            for word in ["senior", "sr", "junior", "jr", "lead", "principal",
                         "staff", "associate", "mid", "ii", "iii", "iv"]:
                text = re.sub(rf'\b{word}\b', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        t = normalize(title)
        c = normalize(company)
        return f"{t}||{c}"

    # ─── Title Similarity ────────────────────────────────────────────────

    @staticmethod
    def _title_similarity(title1: str, title2: str) -> float:
        if not title1 or not title2:
            return 0.0
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        stops = {"the", "a", "an", "and", "or", "in", "at", "for", "of", "to", "&", "-", "/"}
        words1 -= stops
        words2 -= stops
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    # ─── Pick Canonical Job ──────────────────────────────────────────────

    @staticmethod
    def _pick_canonical(jobs: list[Job]) -> Job:
        def score_job(job: Job) -> float:
            s = 0.0
            if job.salary_min or job.salary_max: s += 3.0
            if job.skills_required:
                try:
                    skills = json.loads(job.skills_required) if isinstance(job.skills_required, str) else job.skills_required
                    s += min(len(skills), 10) * 0.2
                except: pass
            if job.description: s += min(len(job.description), 5000) / 1000
            if job.source == "jsearch": s += 1.0
            if job.source_url: s += 0.5
            return s
        return max(jobs, key=score_job)

    # ─── Semantic Duplicate Verification ─────────────────────────────────

    async def _verify_duplicate(self, job1: Job, job2: Job) -> bool:
        """Uses embedding similarity. Falls back to heuristic if unavailable."""
        if (job1.source == job2.source and job1.source_id and
                job1.source_id == job2.source_id):
            return True

        try:
            text1 = f"{job1.title} at {job1.company_name}. {job1.description[:500] if job1.description else ''}"
            text2 = f"{job2.title} at {job2.company_name}. {job2.description[:500] if job2.description else ''}"

            similarity = await embedding_service.compute_similarity(text1, text2)

            if similarity >= self.similarity_threshold:
                return True
            if similarity >= 0.7:
                title_sim = self._title_similarity(job1.title, job2.title)
                return title_sim >= 0.7 and similarity >= 0.75
            return False
        except Exception as e:
            print(f"Embedding similarity failed, using heuristic: {e}")
            title_sim = self._title_similarity(job1.title, job2.title)
            same_company = (job1.company_name or "").lower() == (job2.company_name or "").lower()
            same_location = (job1.location or "").lower() == (job2.location or "").lower()
            if same_company and title_sim >= 0.7: return True
            if same_company and same_location and title_sim >= 0.5: return True
            return False


# Singleton
dedup_service = DedupService()
