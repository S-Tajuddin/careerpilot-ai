"""
CareerPilot AI — JSearch Connector
Uses JSearch API (via RapidAPI) to search jobs from Google for Jobs
which aggregates LinkedIn, Indeed, Naukri, Glassdoor, etc.
Free tier: 200 requests/month.
"""

from datetime import datetime
from typing import Optional

import httpx

from app.config import settings
from app.connectors.base import BaseConnector, NormalizedJob


class JSearchConnector(BaseConnector):
    """
    JSearch API connector — the primary job source.
    Aggregates from: LinkedIn, Indeed, Naukri, Glassdoor, ZipRecruiter, etc.
    via Google for Jobs index.
    
    API docs: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
    """

    def __init__(self):
        super().__init__()
        self.source_name = "jsearch"
        self.base_url = f"https://{settings.jsearch_host}"
        self.headers = {
            "X-RapidAPI-Key": settings.rapidapi_key or "",
            "X-RapidAPI-Host": settings.jsearch_host,
        }

    async def authenticate(self) -> bool:
        """Verify RapidAPI key works by making a minimal request."""
        if not settings.rapidapi_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/search",
                    headers=self.headers,
                    params={"query": "test", "num_pages": 1},
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        country: str = "in",
        remote_only: bool = False,
        date_posted: Optional[str] = None,
        max_results: int = 20,
    ) -> list[NormalizedJob]:
        """
        Search JSearch for jobs.
        
        JSearch uses Google for Jobs syntax:
        - query: "AEM developer in Hyderabad" or "AEM developer"
        - location is appended to query for best results
        """
        if not settings.rapidapi_key:
            return []

        # Build search query — JSearch works best with "query in location" format
        search_query = query
        if location and not remote_only:
            search_query = f"{query} in {location}"
        elif remote_only:
            search_query = f"{query} remote"

        # Number of pages (each page = ~10 results)
        num_pages = max(1, (max_results + 9) // 10)

        params = {
            "query": search_query,
            "num_pages": num_pages,
        }

        # Optional filters
        if country:
            # JSearch uses 2-letter country code
            params["country"] = country
        if date_posted and date_posted in ("today", "week", "month"):
            params["date_posted"] = date_posted
        if remote_only:
            params["remote_jobs_only"] = "true"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.base_url}/search",
                    headers=self.headers,
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            print(f"JSearch API error: {e.response.status_code} — {e.response.text[:200]}")
            return []
        except httpx.RequestError as e:
            print(f"JSearch request error: {e}")
            return []
        except Exception as e:
            print(f"JSearch unexpected error: {e}")
            return []

        # Parse results
        jobs = []
        raw_jobs = data.get("data", [])

        for raw in raw_jobs[:max_results]:
            try:
                normalized = self.normalize(raw)
                jobs.append(normalized)
            except Exception as e:
                print(f"JSearch normalize error for job: {e}")
                continue

        return jobs

    async def get_job(self, source_id: str) -> Optional[NormalizedJob]:
        """Get a single job by JSearch job_id."""
        if not settings.rapidapi_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.base_url}/job-details",
                    headers=self.headers,
                    params={"job_id": source_id},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            print(f"JSearch get_job error: {e}")
            return None

        raw_jobs = data.get("data", [])
        if raw_jobs:
            return self.normalize(raw_jobs[0])
        return None

    def normalize(self, raw_job: dict) -> NormalizedJob:
        """
        Convert JSearch API response to NormalizedJob.
        
        JSearch response fields (key ones):
        - job_id, employer_name, job_title, job_city, job_country
        - job_description, job_apply_link, job_posted_at_datetime_utc
        - job_min_salary, job_max_salary, job_salary_currency, job_salary_period
        - job_is_remote, job_employment_type
        - job_required_skills (sometimes), job_required_experience
        """
        # Salary parsing
        salary_min = raw_job.get("job_min_salary")
        salary_max = raw_job.get("job_max_salary")
        salary_currency = raw_job.get("job_salary_currency", "INR") or "INR"
        salary_period = raw_job.get("job_salary_period", "yearly") or "yearly"

        # Normalize salary period
        if salary_period in ("month", "monthly"):
            salary_period = "monthly"
        elif salary_period in ("year", "yearly", "annually"):
            salary_period = "yearly"
        elif salary_period in ("hour", "hourly"):
            salary_period = "hourly"

        # If monthly salary in INR, convert to yearly
        if salary_currency == "INR" and salary_period == "monthly":
            if salary_min:
                salary_min = salary_min * 12
            if salary_max:
                salary_max = salary_max * 12
            salary_period = "yearly"

        # Location
        city = raw_job.get("job_city", "")
        state = raw_job.get("job_state", "")
        country = raw_job.get("job_country", "")
        location_parts = [p for p in [city, state, country] if p]
        location = ", ".join(location_parts) if location_parts else None

        # Is remote
        is_remote = bool(raw_job.get("job_is_remote", False))

        # Posted date
        posted_date = raw_job.get("job_posted_at_datetime_utc")

        # Employment type
        job_type_raw = raw_job.get("job_employment_type", "").lower()
        job_type = self._normalize_job_type(job_type_raw)

        # Skills — try to extract from description if not provided
        skills = raw_job.get("job_required_skills") or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]

        # Experience
        experience = raw_job.get("job_required_experience")
        if isinstance(experience, dict):
            experience = experience.get("required_experience_in_months", "")
            if experience:
                experience = f"{int(experience) // 12} years"

        # Description
        description = raw_job.get("job_description", "")

        return NormalizedJob(
            source="jsearch",
            source_id=raw_job.get("job_id", ""),
            source_url=raw_job.get("job_apply_link", ""),
            title=raw_job.get("job_title", "Unknown Title"),
            company_name=raw_job.get("employer_name", "Unknown Company"),
            location=location,
            salary_min=int(salary_min) if salary_min else None,
            salary_max=int(salary_max) if salary_max else None,
            salary_currency=salary_currency,
            salary_period=salary_period,
            job_type=job_type,
            is_remote=is_remote,
            description=description,
            requirements=None,
            skills_required=skills,
            experience_required=str(experience) if experience else None,
            posted_date=posted_date,
        )

    async def health_check(self) -> dict:
        """Check if JSearch API is accessible."""
        if not settings.rapidapi_key:
            return {"status": "error", "details": "RAPIDAPI_KEY not configured"}

        try:
            is_authed = await self.authenticate()
            if is_authed:
                return {"status": "ok", "details": "JSearch API accessible"}
            else:
                return {"status": "error", "details": "Authentication failed"}
        except Exception as e:
            return {"status": "error", "details": str(e)}

    @staticmethod
    def _normalize_job_type(raw: str) -> Optional[str]:
        """Map JSearch employment type to our standard."""
        # Normalize: lowercase, replace underscores/hyphens with spaces, strip
        normalized = raw.lower().strip().replace("_", " ").replace("-", " ")
        mapping = {
            "full time": "full_time",
            "fulltime": "full_time",
            "part time": "part_time",
            "parttime": "part_time",
            "contract": "contract",
            "contractor": "contract",
            "internship": "internship",
            "intern": "internship",
            "temporary": "contract",
        }
        return mapping.get(normalized, None)
