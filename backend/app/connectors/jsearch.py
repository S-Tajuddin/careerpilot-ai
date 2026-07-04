"""
CareerPilot AI — JSearch Connector
Uses JSearch API to search jobs from Google for Jobs
which aggregates LinkedIn, Indeed, Naukri, Glassdoor, etc.
Free tier: 200 requests/month.

Updated 2026-07: JSearch API changed endpoints:
  - Old: /search (DEPRECATED — returns "Endpoint does not exist")
  - New: /search-v2 (with cursor-based pagination)
  - Job details: /job-details
  - Also available directly at api.openwebninja.com (avoids RapidAPI data limits)
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

    Two access methods:
    1. Via RapidAPI: jsearch.p.rapidapi.com (X-RapidAPI-Key header)
    2. Direct via OpenWeb Ninja: api.openwebninja.com (x-api-key header)

    Endpoints (as of 2026):
    - /search-v2    — Search jobs (cursor-based pagination, recommended)
    - /job-details  — Get single job by job_id
    - /estimated-salary — Salary estimates by title + location
    """

    def __init__(self):
        super().__init__()
        self.source_name = "jsearch"

        # Determine access method based on config
        if settings.rapidapi_key and not settings.jsearch_direct_key:
            # RapidAPI mode
            self.base_url = f"https://{settings.jsearch_host}"
            self.headers = {
                "X-RapidAPI-Key": settings.rapidapi_key or "",
                "X-RapidAPI-Host": settings.jsearch_host,
            }
            self._mode = "rapidapi"
        else:
            # Direct OpenWeb Ninja mode (preferred)
            self.base_url = "https://api.openwebninja.com/jsearch"
            self.headers = {
                "x-api-key": settings.jsearch_direct_key or settings.rapidapi_key or "",
            }
            self._mode = "direct"

    async def authenticate(self) -> bool:
        """Verify API key works by making a minimal search request."""
        key = settings.rapidapi_key or settings.jsearch_direct_key
        if not key:
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.base_url}/search-v2",
                    headers=self.headers,
                    params={"query": "test", "country": "us", "num_pages": 1},
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
        Search JSearch for jobs using /search-v2 endpoint.

        JSearch uses Google for Jobs syntax:
        - query: "AEM developer in Hyderabad" or "AEM developer"
        - location is appended to query for best results
        """
        key = settings.rapidapi_key or settings.jsearch_direct_key
        if not key:
            return []

        # Build search query — JSearch works best with "query in location" format
        search_query = query
        if location and not remote_only:
            search_query = f"{query} in {location}"
        elif remote_only:
            search_query = f"{query} remote"

        params = {
            "query": search_query,
            "country": country,
            "num_pages": 1,  # First page only (up to 10 jobs per page)
        }

        # Optional filters
        if date_posted and date_posted in ("today", "week", "month"):
            params["date_posted"] = date_posted
        if remote_only:
            params["work_from_home"] = "true"

        # Request enriched data (skills, technologies, seniority, etc.)
        params["enrich"] = "true"

        all_jobs = []
        cursor = None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch pages until we have enough results
                for _ in range(3):  # Max 3 pages to respect rate limits
                    if cursor:
                        params["cursor"] = cursor

                    resp = await client.get(
                        f"{self.base_url}/search-v2",
                        headers=self.headers,
                        params=params,
                    )

                    if resp.status_code != 200:
                        print(f"JSearch API error: {resp.status_code} — {resp.text[:200]}")
                        break

                    data = resp.json()
                    raw_jobs = data.get("data", [])

                    for raw in raw_jobs:
                        try:
                            normalized = self.normalize(raw)
                            all_jobs.append(normalized)
                        except Exception as e:
                            print(f"JSearch normalize error: {e}")
                            continue

                    # Check if there are more results
                    next_cursor = data.get("next_cursor") or data.get("cursor")
                    if not next_cursor or len(all_jobs) >= max_results:
                        break
                    cursor = next_cursor

        except httpx.HTTPStatusError as e:
            print(f"JSearch API error: {e.response.status_code} — {e.response.text[:200]}")
        except httpx.RequestError as e:
            print(f"JSearch request error: {e}")
        except Exception as e:
            print(f"JSearch unexpected error: {e}")

        return all_jobs[:max_results]

    async def get_job(self, source_id: str) -> Optional[NormalizedJob]:
        """Get a single job by JSearch job_id."""
        key = settings.rapidapi_key or settings.jsearch_direct_key
        if not key:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {
                    "job_id": source_id,
                    "country": "in",
                }
                resp = await client.get(
                    f"{self.base_url}/job-details",
                    headers=self.headers,
                    params=params,
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

        Handles both old format and new enriched format (2026):
        - Core fields: job_id, employer_name, job_title, job_city, etc.
        - Enriched fields: required_technologies, preferred_technologies,
          seniority_level, work_arrangement, required_experience_years,
          soft_skills, methodologies, benefits_extended, industry, job_function
        """
        # Salary parsing
        salary_min = raw_job.get("job_min_salary")
        salary_max = raw_job.get("job_max_salary")
        salary_currency = raw_job.get("job_salary_currency") or "INR"
        salary_period = raw_job.get("job_salary_period") or "YEAR"

        # Normalize salary period
        salary_period_lower = salary_period.lower().strip()
        if salary_period_lower in ("month", "monthly"):
            salary_period = "monthly"
        elif salary_period_lower in ("year", "yearly", "annually"):
            salary_period = "yearly"
        elif salary_period_lower in ("hour", "hourly"):
            salary_period = "hourly"

        # If monthly salary in INR, convert to yearly
        if salary_currency == "INR" and salary_period == "monthly":
            if salary_min:
                salary_min = salary_min * 12
            if salary_max:
                salary_max = salary_max * 12
            salary_period = "yearly"

        # Location
        city = raw_job.get("job_city", "") or ""
        state = raw_job.get("job_state", "") or ""
        country = raw_job.get("job_country", "") or ""
        location_parts = [p for p in [city, state, country] if p]
        location = ", ".join(location_parts) if location_parts else None

        # Is remote — check both old and new fields
        is_remote = bool(raw_job.get("job_is_remote", False))
        work_arrangement = raw_job.get("work_arrangement", "")
        if work_arrangement == "remote":
            is_remote = True

        # Posted date
        posted_date = raw_job.get("job_posted_at_datetime_utc")

        # Employment type — check both old and new formats
        job_type_raw = raw_job.get("job_employment_type", "")
        if not job_type_raw:
            job_types = raw_job.get("job_employment_types", [])
            if job_types:
                job_type_raw = job_types[0]
        job_type = self._normalize_job_type(str(job_type_raw))

        # Skills — prioritize enriched fields, fall back to job_highlights
        skills = []
        required_techs = raw_job.get("required_technologies", [])
        preferred_techs = raw_job.get("preferred_technologies", [])
        if required_techs:
            skills.extend(required_techs)
        if preferred_techs:
            skills.extend(preferred_techs)

        # Fallback: try job_required_skills
        if not skills:
            raw_skills = raw_job.get("job_required_skills") or []
            if isinstance(raw_skills, str):
                skills = [s.strip() for s in raw_skills.split(",") if s.strip()]
            elif isinstance(raw_skills, list):
                skills = raw_skills

        # Fallback: extract from job_highlights.Qualifications
        if not skills:
            highlights = raw_job.get("job_highlights", {})
            if isinstance(highlights, dict):
                qualifications = highlights.get("Qualifications", [])
                # These are long sentences, not skill names — skip

        # Experience — prefer enriched field
        experience = None
        exp_years = raw_job.get("required_experience_years")
        if exp_years:
            experience = f"{exp_years} years"
        else:
            raw_exp = raw_job.get("job_required_experience")
            if isinstance(raw_exp, dict):
                months = raw_exp.get("required_experience_in_months", "")
                if months:
                    experience = f"{int(months) // 12} years"

        # Description
        description = raw_job.get("job_description", "")

        # Seniority level (enriched)
        seniority = raw_job.get("seniority_level")

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
            experience_required=experience,
            posted_date=posted_date,
        )

    async def health_check(self) -> dict:
        """Check if JSearch API is accessible."""
        key = settings.rapidapi_key or settings.jsearch_direct_key
        if not key:
            return {"status": "error", "details": "No API key configured (RAPIDAPI_KEY or JSEARCH_DIRECT_KEY)"}

        try:
            is_authed = await self.authenticate()
            if is_authed:
                return {"status": "ok", "details": f"JSearch API accessible (mode: {self._mode})"}
            else:
                return {"status": "error", "details": "Authentication failed — check your API key"}
        except Exception as e:
            return {"status": "error", "details": str(e)}

    @staticmethod
    def _normalize_job_type(raw: str) -> Optional[str]:
        """Map JSearch employment type to our standard."""
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
