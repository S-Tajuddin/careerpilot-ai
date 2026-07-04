"""
CareerPilot AI — Job Service
Orchestrates job search across multiple connectors,
saves results to database, and logs activity.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Job, Company, ActivityLog, SearchHistory
from app.connectors.base import NormalizedJob
from app.connectors.jsearch import JSearchConnector
from app.connectors.adzuna import AdzunaConnector


class JobService:
    """
    Orchestrates multi-source job search and persistence.
    Deduplicates by (source, source_id) and optionally by semantic similarity.
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
        Saves results to database.
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
            saved_count = self._save_jobs(all_jobs, db)
            print(f"  Saved {saved_count} new jobs to database")

            # Log search
            self._log_search(db, query, location, len(all_jobs), ",".join(sources))

        return all_jobs

    def _save_jobs(self, jobs: list[NormalizedJob], db: Session) -> int:
        """Save normalized jobs to database. Returns count of NEW jobs saved."""
        saved = 0

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
            saved += 1

            # Log activity
            self._log_activity(db, "job_found", "job", 0, {
                "title": norm_job.title,
                "company": norm_job.company_name,
                "source": norm_job.source,
            })

        db.commit()
        return saved

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
            # Try ISO format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass
        try:
            # Try common format
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
