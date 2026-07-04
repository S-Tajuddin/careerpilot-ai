"""
CareerPilot AI — Connector SDK
Base class that all job source connectors must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from app.config import settings


@dataclass
class NormalizedJob:
    """Standardized job representation from any source."""
    source: str                                # jsearch, adzuna, greenhouse, lever, manual
    source_id: str                             # Original ID from the source
    source_url: str                            # Direct link to original listing
    title: str
    company_name: str
    location: Optional[str] = None
    salary_min: Optional[int] = None           # INR yearly (or USD yearly for remote)
    salary_max: Optional[int] = None
    salary_currency: str = "INR"
    salary_period: str = "yearly"
    job_type: Optional[str] = None             # full_time, part_time, contract
    is_remote: bool = False
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills_required: list[str] = field(default_factory=list)
    experience_required: Optional[str] = None
    posted_date: Optional[str] = None          # ISO format string

    def salary_lpa(self) -> Optional[float]:
        """Convert salary to LPA (Lakhs Per Annum) for display."""
        if not self.salary_min and not self.salary_max:
            return None
        val = self.salary_max or self.salary_min
        if self.salary_currency == "INR":
            return val / 100000
        elif self.salary_currency == "USD":
            return val / 1000  # Show as $K
        return None


class BaseConnector(ABC):
    """
    Abstract base class for job source connectors.
    All connectors must implement these 5 methods.
    """

    def __init__(self):
        self.source_name: str = "base"

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Verify API credentials are valid.
        Returns True if authentication succeeds, False otherwise.
        """
        pass

    @abstractmethod
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
        Search for jobs matching the query.
        
        Args:
            query: Search keywords (e.g., "AEM developer")
            location: City/region (e.g., "Hyderabad")
            country: Country code (e.g., "in" for India)
            remote_only: Only return remote jobs
            date_posted: Filter by recency ("today", "week", "month")
            max_results: Maximum results to return
        
        Returns:
            List of NormalizedJob objects
        """
        pass

    @abstractmethod
    async def get_job(self, source_id: str) -> Optional[NormalizedJob]:
        """
        Get a single job by its source ID.
        
        Args:
            source_id: The original ID from this source
        
        Returns:
            Single NormalizedJob or None if not found
        """
        pass

    @abstractmethod
    def normalize(self, raw_job: dict) -> NormalizedJob:
        """
        Convert raw API response into NormalizedJob format.
        Each connector knows its own response structure.
        
        Args:
            raw_job: Raw dictionary from the API response
        
        Returns:
            NormalizedJob with standardized fields
        """
        pass

    @abstractmethod
    async def health_check(self) -> dict:
        """
        Check if the connector's API is accessible.
        
        Returns:
            dict with "status" ("ok"/"error") and optional "details"
        """
        pass
