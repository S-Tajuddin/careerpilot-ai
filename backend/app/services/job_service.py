"""
CareerPilot AI — Job Service
Orchestrates job search across multiple connectors,
saves results to database, scores them, and deduplicates.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Job, Company, Profile, ActivityLog, SearchHistory
from app.connectors.base import NormalizedJob
from app.connectors.jsearch import JSearchConnector
from app.connectors.adzuna import AdzunaConnector


class JobService:
    """
    Orchestrates multi-source job search, scoring, and persistence.
    Deduplicates by (source, source_id) and optionally by semantic similarity.
    Auto-scores new jobs if auto_score_jobs is enabled.
    """

    def __init__(self):
        self.connectors = {
            "jsearch": JSearchConnector(),
            "adzuna": AdzunaConnector(),
        }

    async def search_all_sources(
        self,
        query: str,
        location: Optional[str] = None,
        country: str = "in",
        remote_only: bool = False,
        date_posted: Optional[str] = None,
        max_results: int = 20,
        sources: Optional[list[str]] = None,
        db: Session = None,
    ) -> list[NormalizedJob]:
        """
        Search all configured connectors and merge results.
        Saves results to database, auto-scores, and deduplicates.
        """
        if not sources:
            sources = list(self.connectors.keys())

        all_jobs: list[NormalizedJob] = []

        for source_name in sources:
            connector = self.connectors.get(source_name)
            if not connector:
                continue

            try:
                jobs = await connector.search_jobs(
                    query=query,
                    location=location or settings.default_location,
                    country=country,
                    remote_only=remote_only,
                    date_posted=date_posted,
                    max_results=max_results,
                )
                all_jobs.extend(jobs)
                print(f"  {source_name}: {len(jobs)} jobs found")
            except Exception as e:
                print(f"  {source_name}: error — {e}")
                continue

        # Save to database if session provided
        if db:
            saved_ids = self._save_jobs(all_jobs, db)
            print(f"  Saved {len(saved_ids)} new jobs to database")

            # Log search
            self._log_search(db, query, location, len(all_jobs), ",".join(sources))

            # Auto-score new jobs
            await self._auto_score_jobs(saved_ids, db)

            # Dedup
            await self._auto_dedup(saved_ids, db)

        return all_jobs

    def _save_jobs(self, jobs: list[NormalizedJob], db: Session) -> list[int]:
        """Save normalized jobs to database. Returns list of NEW job IDs."""
        saved_ids = []

        for norm_job in jobs:
            # Check for existing job by (source, source_id)
            existing = db.query(Job).filter(
                Job.source == norm_job.source,
                Job.source_id == norm_job.source_id,
            ).first()

            if existing:
                # Update existing job if needed
                existing.is_active = True
                existing.updated_at = datetime.now(timezone.utc)
                # Update salary if not previously set
                if not existing.salary_min and norm_job.salary_min:
                    existing.salary_min = norm_job.salary_min
                if not existing.salary_max and norm_job.salary_max:
                    existing.salary_max = norm_job.salary_max
                # Update skills if job has more data
                if norm_job.skills_required and not existing.skills_required:
                    existing.skills_required = json.dumps(norm_job.skills_required)
                if norm_job.description and (not existing.description or len(norm_job.description) > len(existing.description or "")):
                    existing.description = norm_job.description
                continue

            # Find or create company
            company_id = self._find_or_create_company(norm_job.company_name, db)

            # Create new job
            job = Job(
                source=norm_job.source,
                source_id=norm_job.source_id,
                source_url=norm_job.source_url,
                title=norm_job.title,
                company_id=company_id,
                company_name=norm_job.company_name,
                location=norm_job.location,
                salary_min=norm_job.salary_min,
                salary_max=norm_job.salary_max,
                salary_currency=norm_job.salary_currency,
                salary_period=norm_job.salary_period,
                job_type=norm_job.job_type,
                is_remote=norm_job.is_remote,
                description=norm_job.description,
                requirements=norm_job.requirements,
                skills_required=json.dumps(norm_job.skills_required) if norm_job.skills_required else None,
                experience_required=norm_job.experience_required,
                posted_date=self._parse_date(norm_job.posted_date),
                is_active=True,
            )

            db.add(job)
            db.flush()  # Get the ID
            saved_ids.append(job.id)

            # Log activity
            self._log_activity(db, "job_found", "job", job.id, {
                "title": norm_job.title,
                "company": norm_job.company_name,
                "source": norm_job.source,
            })

        db.commit()
        return saved_ids

    async def _auto_score_jobs(self, job_ids: list[int], db: Session):
        """Quick-score newly saved jobs — INSTANT, no LLM calls."""
        if not job_ids:
            return

        try:
            from app.services.scoring import scoring_service

            profile = db.query(Profile).filter(Profile.id == 1).first()
            if not profile:
                profile = Profile(
                    id=1, experience_years=8, current_role="AEM Developer",
                    target_role="AEM Architect", expected_salary_min=2_000_000,
                    expected_salary_max=3_500_000, location="Hyderabad, India",
                    remote_preference="any",
                )

            scored = 0
            for job_id in job_ids:
                job = db.query(Job).filter(Job.id == job_id).first()
                if not job:
                    continue
                try:
                    result = scoring_service.quick_score(job, profile, db)
                    job.match_score = result["overall_score"]
                    job.match_strengths_list = result["strengths"]
                    job.match_weaknesses_list = result["weaknesses"]
                    job.match_recommendations_list = result["recommendations"]
                    job.updated_at = datetime.now(timezone.utc)
                    scored += 1
                except Exception as e:
                    print(f"  Quick-score error for job {job_id}: {e}")

            db.commit()
            if scored:
                print(f"  ⚡ Quick-scored {scored}/{len(job_ids)} new jobs")

        except ImportError:
            print("  Scoring service not available — skipping")
        except Exception as e:
            print(f"  Auto-score error: {e}")

    async def _auto_dedup(self, job_ids: list[int], db: Session):
        """Run deduplication on newly saved jobs."""
        if not job_ids:
            return

        try:
            from app.services.dedup import dedup_service

            for job_id in job_ids:
                job = db.query(Job).filter(Job.id == job_id).first()
                if not job:
                    continue

                canonical_id = await dedup_service.dedup_new_job(job, db)
                if canonical_id:
                    job.canonical_job_id = canonical_id
                    job.is_active = False
                    db.commit()
                    print(f"  🔄 Duplicate: {job.title} → canonical #{canonical_id}")

        except ImportError:
            print("  Dedup service not available — skipping")
        except Exception as e:
            print(f"  Dedup error: {e}")

    def _find_or_create_company(self, company_name: str, db: Session) -> Optional[int]:
        """Find existing company or create a new one. Returns company ID."""
        if not company_name:
            return None

        # Try exact match first
        company = db.query(Company).filter(
            Company.name.ilike(company_name.strip())
        ).first()

        if company:
            return company.id

        # Create new company
        company = Company(
            name=company_name.strip(),
            is_aem_hirer=False,
        )
        db.add(company)
        db.flush()  # Get the ID without committing
        return company.id

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            pass
        return None

    @staticmethod
    def _log_search(db: Session, query: str, location: str, count: int, source: str):
        """Log search to history."""
        entry = SearchHistory(
            query=query,
            filters=json.dumps({"location": location}),
            results_count=count,
            source=source,
        )
        db.add(entry)
        db.commit()

    @staticmethod
    def _log_activity(db: Session, action: str, entity_type: str, entity_id: int, details: dict = None):
        """Log activity."""
        entry = ActivityLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details) if details else None,
        )
        db.add(entry)
        db.commit()


# Singleton
job_service = JobService()
