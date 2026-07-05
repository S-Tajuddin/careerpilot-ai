"""
CareerPilot AI — Adzuna Connector
Adzuna API for additional India job listings.
Free tier: unlimited (with attribution).
API docs: https://developer.adzuna.com/docs/search
"""

from datetime import datetime
from typing import Optional

import httpx

from app.config import settings
from app.connectors.base import BaseConnector, NormalizedJob
from app.utils.url_validation import sanitize_source_url


class AdzunaConnector(BaseConnector):
    """
    Adzuna API connector — secondary job source for India.
    Aggregates from various job boards.
    
    API base: https://api.adzuna.com/v1/api/jobs/{country}/search/{version}
    """

    def __init__(self):
        super().__init__()
        self.source_name = "adzuna"
        self.base_url = "https://api.adzuna.com/v1/api/jobs"
        self.app_id = settings.adzuna_app_id
        self.app_key = settings.adzuna_app_key

    async def authenticate(self) -> bool:
        """Verify Adzuna API credentials."""
        if not self.app_id or not self.app_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/in/search/1",
                    params={
                        "app_id": self.app_id,
                        "app_key": self.app_key,
                        "results_per_page": 1,
                        "what": "test",
                    },
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
        """Search Adzuna for jobs in India."""
        if not self.app_id or not self.app_key:
            return []

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": min(max_results, 50),
            "what": query,
            "content-type": "application/json",
        }

        # Location filter
        if location:
            # Adzuna uses location0=India, location1=state, location2=city
            params["where"] = location

        # Distance from location (in km)
        if location:
            params["distance"] = 30

        # Salary range filter (in INR for India)
        if settings.expected_salary_min:
            params["salary_min"] = settings.expected_salary_min // 12  # Monthly

        # Sort by date (newest first)
        params["sort_by"] = "date"

        # Full-time only
        params["full_time"] = 1

        # Remote filter
        if remote_only:
            params["what"] = f"{query} remote"

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    f"{self.base_url}/{country}/search/1",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            print(f"Adzuna API error: {e.response.status_code}")
            return []
        except Exception as e:
            print(f"Adzuna request error: {e}")
            return []

        jobs = []
        for raw in data.get("results", [])[:max_results]:
            try:
                normalized = self.normalize(raw)
                jobs.append(normalized)
            except Exception as e:
                print(f"Adzuna normalize error: {e}")
                continue

        return jobs

    async def get_job(self, source_id: str) -> Optional[NormalizedJob]:
        """Adzuna doesn't have a direct 'get by ID' endpoint — return None."""
        return None

    def normalize(self, raw_job: dict) -> NormalizedJob:
        """
        Convert Adzuna API response to NormalizedJob.
        
        Key fields:
        - id, title, company.display_name, location.display_name
        - description, redirect_url, created, salary_min, salary_max
        - contract_time, contract_type
        """
        # Salary
        salary_min = raw_job.get("salary_min")
        salary_max = raw_job.get("salary_max")
        # Adzuna returns yearly salary for India in INR

        # Location — API uses display_name (snake_case), not displayname
        location_obj = raw_job.get("location", {})
        display_location = location_obj.get("display_name") or location_obj.get("displayname")
        if display_location:
            location = str(display_location)
        else:
            location_parts = []
            for key in ["area", "region"]:
                val = location_obj.get(key)
                if val:
                    if isinstance(val, list):
                        location_parts.extend(val)
                    else:
                        location_parts.append(str(val))
            location = ", ".join(location_parts) if location_parts else None

        # Company — API uses display_name (snake_case), not displayname
        company = raw_job.get("company", {})
        company_name = (
            company.get("display_name")
            or company.get("displayname")
            or "Unknown Company"
        )

        # Job type
        contract_time = raw_job.get("contract_time", "")
        contract_type = raw_job.get("contract_type", "")
        job_type = self._normalize_job_type(contract_time, contract_type)

        # Is remote (Adzuna doesn't have explicit remote flag)
        is_remote = False
        title_lower = (raw_job.get("title", "") + " " + raw_job.get("description", "")).lower()
        if "remote" in title_lower or "work from home" in title_lower:
            is_remote = True

        # Posted date
        created = raw_job.get("created")

        # Description
        description = raw_job.get("description", "")

        return NormalizedJob(
            source="adzuna",
            source_id=str(raw_job.get("id", "")),
            source_url=sanitize_source_url(raw_job.get("redirect_url", "")),
            title=raw_job.get("title", "Unknown Title"),
            company_name=company_name,
            location=location,
            salary_min=int(salary_min) if salary_min else None,
            salary_max=int(salary_max) if salary_max else None,
            salary_currency="INR",
            salary_period="yearly",
            job_type=job_type,
            is_remote=is_remote,
            description=description,
            requirements=None,
            skills_required=[],
            experience_required=None,
            posted_date=created,
        )

    async def health_check(self) -> dict:
        """Check if Adzuna API is accessible."""
        if not self.app_id or not self.app_key:
            return {"status": "error", "details": "ADZUNA_APP_ID/KEY not configured"}

        try:
            is_authed = await self.authenticate()
            if is_authed:
                return {"status": "ok", "details": "Adzuna API accessible"}
            return {"status": "error", "details": "Authentication failed"}
        except Exception as e:
            return {"status": "error", "details": str(e)}

    @staticmethod
    def _normalize_job_type(contract_time: str, contract_type: str) -> Optional[str]:
        """Map Adzuna contract types to our standard."""
        if contract_type in ("contract", "gig"):
            return "contract"
        if contract_type == "internship":
            return "internship"
        if contract_time == "full_time" or contract_type == "permanent":
            return "full_time"
        if contract_time == "part_time":
            return "part_time"
        return "full_time"  # Default for India market
