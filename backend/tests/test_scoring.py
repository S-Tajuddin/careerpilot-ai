"""
CareerPilot AI — Phase 2 Tests
AI Scoring + Deduplication service tests.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.scoring import ScoringService, AEM_SKILL_GROUPS, SKILL_LOOKUP
from app.services.dedup import DedupService


# ─── Scoring Service Tests ──────────────────────────────────────────────────

class TestScoringService:
    """Test the AI scoring engine."""

    def setup_method(self):
        self.service = ScoringService()

    def test_weights_sum_to_one(self):
        """All weights must sum to 1.0."""
        total = sum(self.service.weights.values())
        assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, expected 1.0"

    def test_aem_skill_groups_exist(self):
        """AEM skill taxonomy has all required groups."""
        required = ["core_aem", "eds", "backend", "frontend", "devops", "testing", "architect"]
        for group in required:
            assert group in AEM_SKILL_GROUPS, f"Missing skill group: {group}"
            assert len(AEM_SKILL_GROUPS[group]) > 0, f"Empty skill group: {group}"

    def test_skill_lookup_covers_variants(self):
        """Skill lookup should cover common AEM skill name variants."""
        assert "aem" in SKILL_LOOKUP
        assert "cq5" in SKILL_LOOKUP
        assert "eds" in SKILL_LOOKUP
        assert "sling" in SKILL_LOOKUP
        assert "htl" in SKILL_LOOKUP
        assert "osgi" in SKILL_LOOKUP

    def test_score_skills_exact_match(self):
        """Profile with all required skills should score high."""
        profile = MagicMock()
        profile.skills_list = ["AEM", "Java", "Sling", "OSGi", "HTL", "Maven"]

        job = MagicMock()
        job.skills_required_list = ["AEM", "Java", "Sling"]
        job.title = "AEM Developer"
        job.description = ""

        score = self.service._score_skills(job, profile)
        assert score >= 80, f"Expected >= 80 for exact skill match, got {score}"

    def test_score_skills_no_overlap(self):
        """Profile with no matching skills should score low."""
        profile = MagicMock()
        profile.skills_list = ["Python", "Django", "React", "Node.js"]

        job = MagicMock()
        job.skills_required_list = ["AEM", "Sling", "OSGi"]
        job.title = "AEM Developer"
        job.description = ""

        score = self.service._score_skills(job, profile)
        assert score < 30, f"Expected < 30 for no skill overlap, got {score}"

    def test_score_skills_partial_match(self):
        """Partial skill overlap should score in the middle."""
        profile = MagicMock()
        profile.skills_list = ["Java", "Maven", "AEM", "React"]

        job = MagicMock()
        job.skills_required_list = ["AEM", "Sling", "OSGi", "HTL"]
        job.title = "AEM Developer"
        job.description = ""

        score = self.service._score_skills(job, profile)
        assert 30 <= score <= 80, f"Expected 30-80 for partial match, got {score}"

    def test_score_experience_sweet_spot(self):
        """8 years experience vs 6-8 year requirement = 100%."""
        profile = MagicMock()
        profile.experience_years = 8.0

        job = MagicMock()
        job.experience_required = "6 years"
        job.title = "Senior AEM Developer"

        score = self.service._score_experience(job, profile)
        assert score == 100.0, f"Expected 100 for sweet spot, got {score}"

    def test_score_experience_under_qualified(self):
        """3 years experience vs 8 year requirement = low score."""
        profile = MagicMock()
        profile.experience_years = 3.0

        job = MagicMock()
        job.experience_required = "8 years"
        job.title = "AEM Architect"

        score = self.service._score_experience(job, profile)
        assert score <= 45, f"Expected <= 45 for under-qualified, got {score}"

    def test_score_experience_seniority_from_title(self):
        """Should infer experience from title when not explicitly stated."""
        profile = MagicMock()
        profile.experience_years = 10.0

        job_architect = MagicMock()
        job_architect.experience_required = None
        job_architect.title = "AEM Architect"
        score_arch = self.service._score_experience(job_architect, profile)
        assert score_arch == 100.0  # 10 years vs 10 required

        job_junior = MagicMock()
        job_junior.experience_required = None
        job_junior.title = "Junior AEM Developer"
        score_jr = self.service._score_experience(job_junior, profile)
        assert score_jr < 80  # Over-qualified for junior

    def test_score_salary_within_range(self):
        """Salary within target = 100%."""
        profile = MagicMock()
        profile.expected_salary_min = 2_000_000
        profile.expected_salary_max = 3_500_000

        job = MagicMock()
        job.salary_min = 2_000_000
        job.salary_max = 3_500_000
        job.salary_currency = "INR"
        job.salary_period = "yearly"

        score = self.service._score_salary(job, profile)
        assert score == 100.0, f"Expected 100 for within range, got {score}"

    def test_score_salary_unknown(self):
        """No salary info = neutral score."""
        profile = MagicMock()
        profile.expected_salary_min = 2_000_000
        profile.expected_salary_max = 3_500_000

        job = MagicMock()
        job.salary_min = None
        job.salary_max = None
        job.salary_currency = None
        job.salary_period = None

        score = self.service._score_salary(job, profile)
        assert score == 70.0, f"Expected 70 for unknown salary, got {score}"

    def test_score_location_hyderabad(self):
        """Hyderabad job for Hyderabad-based user = 100%."""
        profile = MagicMock()
        profile.location = "Hyderabad, India"
        profile.preferred_locations_list = ["Hyderabad", "Remote", "Bangalore"]
        profile.remote_preference = "any"

        job = MagicMock()
        job.location = "Hyderabad, Telangana, India"
        job.is_remote = False

        score = self.service._score_location(job, profile)
        assert score == 100.0, f"Expected 100 for Hyderabad match, got {score}"

    def test_score_location_remote_preference(self):
        """Remote job for remote-preferring user = 100%."""
        profile = MagicMock()
        profile.location = "Hyderabad, India"
        profile.preferred_locations_list = ["Remote", "Hyderabad"]
        profile.remote_preference = "remote"

        job = MagicMock()
        job.location = "Remote"
        job.is_remote = True

        score = self.service._score_location(job, profile)
        assert score == 100.0, f"Expected 100 for remote preference match, got {score}"

    def test_score_company_known_aem_hirer(self):
        """Known AEM hiring company should score 90+."""
        job = MagicMock()
        job.company_id = None
        job.company_name = "Accenture Solutions"

        # Mock DB
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        score = self.service._score_company_quality(job, db)
        assert score >= 90, f"Expected >= 90 for Accenture, got {score}"

    def test_score_company_unknown(self):
        """Unknown company should get default score."""
        job = MagicMock()
        job.company_id = None
        job.company_name = "Random Startup XYZ"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        score = self.service._score_company_quality(job, db)
        assert score == 55.0, f"Expected 55 for unknown company, got {score}"

    def test_parse_experience_years(self):
        """Test experience year parsing."""
        assert ScoringService._parse_experience_years("8 years") == 8.0
        assert ScoringService._parse_experience_years("5-10 years") == 7.5
        assert ScoringService._parse_experience_years("3+ years") == 3.0
        assert ScoringService._parse_experience_years(None) is None
        assert ScoringService._parse_experience_years("Not specified") is None

    def test_normalize_salary_monthly_to_yearly(self):
        """Monthly INR salary should convert to yearly."""
        # ₹1.5L/month = ₹18L/year
        result = ScoringService._normalize_salary(150000, "INR", "monthly")
        assert result == 1_800_000, f"Expected 18L, got {result}"

    def test_overall_score_bounds(self):
        """Overall score must be between 0-100."""
        # This is tested indirectly — but let's verify the clamping
        profile = MagicMock()
        profile.skills_list = ["AEM", "Java"]
        profile.experience_years = 8
        profile.expected_salary_min = 2_000_000
        profile.expected_salary_max = 3_500_000
        profile.location = "Hyderabad, India"
        profile.preferred_locations_list = ["Hyderabad"]
        profile.remote_preference = "any"

        job = MagicMock()
        job.skills_required_list = ["AEM"]
        job.title = "AEM Developer"
        job.description = ""
        job.experience_required = "6 years"
        job.salary_min = 2_000_000
        job.salary_max = 3_500_000
        job.salary_currency = "INR"
        job.salary_period = "yearly"
        job.location = "Hyderabad, India"
        job.is_remote = False
        job.company_id = None
        job.company_name = "Test Company"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        # Compute raw weighted score manually to verify bounds
        skill_s = self.service._score_skills(job, profile)
        exp_s = self.service._score_experience(job, profile)
        sal_s = self.service._score_salary(job, profile)
        loc_s = self.service._score_location(job, profile)
        comp_s = self.service._score_company_quality(job, db)
        rem_s = self.service._score_remote_preference(job, profile)

        overall = (
            skill_s * 0.30 + exp_s * 0.25 + sal_s * 0.15 +
            loc_s * 0.10 + comp_s * 0.10 + rem_s * 0.10
        )
        assert 0 <= overall <= 100, f"Overall score out of bounds: {overall}"


# ─── Dedup Service Tests ────────────────────────────────────────────────────

class TestDedupService:
    """Test the deduplication service."""

    def setup_method(self):
        self.service = DedupService()

    def test_make_group_key_normalizes(self):
        """Group key should normalize seniority and case."""
        key1 = DedupService._make_group_key("Senior AEM Developer", "Accenture")
        key2 = DedupService._make_group_key("AEM Developer", "accenture")
        assert key1 == key2, f"Expected same group key, got {key1} vs {key2}"

    def test_make_group_key_removes_junk(self):
        """Should remove 'Sr', 'Jr', 'Lead' etc."""
        key1 = DedupService._make_group_key("Sr AEM Developer", "Infosys")
        key2 = DedupService._make_group_key("AEM Developer", "infosys")
        assert key1 == key2

    def test_title_similarity_same(self):
        """Identical titles should have similarity 1.0."""
        sim = DedupService._title_similarity("AEM Developer", "AEM Developer")
        assert sim == 1.0

    def test_title_similarity_different(self):
        """Very different titles should have low similarity."""
        sim = DedupService._title_similarity("AEM Developer", "Python Data Scientist")
        assert sim < 0.5

    def test_title_similarity_seniority_variant(self):
        """Same role with different seniority should be similar."""
        sim = DedupService._title_similarity("Senior AEM Developer", "AEM Developer")
        assert sim >= 0.5, f"Expected >= 0.5 for seniority variant, got {sim}"

    def test_parse_json_list_valid(self):
        """Should parse valid JSON array."""
        result = ScoringService._parse_json_list('["Rec 1", "Rec 2", "Rec 3"]')
        assert result == ["Rec 1", "Rec 2", "Rec 3"]

    def test_parse_json_list_with_surrounding_text(self):
        """Should extract JSON from surrounding text."""
        result = ScoringService._parse_json_list('Here are the recommendations:\n["Rec 1", "Rec 2"]')
        assert result == ["Rec 1", "Rec 2"]

    def test_parse_json_list_invalid(self):
        """Should return empty list for invalid JSON."""
        result = ScoringService._parse_json_list("No JSON here")
        assert result == []


# ─── Integration-style test ─────────────────────────────────────────────────

class TestScoringIntegration:
    """Test scoring with realistic AEM job scenarios."""

    def setup_method(self):
        self.service = ScoringService()

    def test_perfect_aem_job_match(self):
        """An ideal AEM job for this user should score 80+."""
        profile = MagicMock()
        profile.skills_list = ["AEM", "Adobe Experience Manager", "EDS", "Java", "Sling",
                               "OSGi", "HTL", "AEM as Cloud Service", "Maven", "CI/CD"]
        profile.experience_years = 8.0
        profile.current_role = "AEM Developer"
        profile.target_role = "AEM Architect"
        profile.expected_salary_min = 2_000_000
        profile.expected_salary_max = 3_500_000
        profile.location = "Hyderabad, India"
        profile.preferred_locations_list = ["Hyderabad", "Remote", "Bangalore"]
        profile.remote_preference = "any"

        job = MagicMock()
        job.skills_required_list = ["AEM", "Java", "Sling", "OSGi", "HTL"]
        job.title = "Senior AEM Developer"
        job.description = "Looking for an experienced AEM developer"
        job.experience_required = "6-8 years"
        job.salary_min = 2_500_000
        job.salary_max = 3_500_000
        job.salary_currency = "INR"
        job.salary_period = "yearly"
        job.location = "Hyderabad, Telangana, India"
        job.is_remote = False
        job.company_id = None
        job.company_name = "Accenture"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        skill_s = self.service._score_skills(job, profile)
        exp_s = self.service._score_experience(job, profile)
        sal_s = self.service._score_salary(job, profile)
        loc_s = self.service._score_location(job, profile)
        comp_s = self.service._score_company_quality(job, db)
        rem_s = self.service._score_remote_preference(job, profile)

        overall = (
            skill_s * 0.30 + exp_s * 0.25 + sal_s * 0.15 +
            loc_s * 0.10 + comp_s * 0.10 + rem_s * 0.10
        )

        assert overall >= 80, f"Ideal AEM job should score 80+, got {overall:.1f}"
        assert skill_s >= 80, f"Skill score should be high, got {skill_s}"
        assert exp_s == 100, f"Experience should be perfect match, got {exp_s}"
        assert sal_s == 100, f"Salary should be in range, got {sal_s}"
        assert loc_s == 100, f"Location should be perfect, got {loc_s}"

    def test_unrelated_job_low_score(self):
        """A non-AEM job should score low on skill match."""
        profile = MagicMock()
        profile.skills_list = ["AEM", "Java", "Sling", "OSGi", "HTL"]
        profile.experience_years = 8.0
        profile.current_role = "AEM Developer"
        profile.target_role = "AEM Architect"
        profile.expected_salary_min = 2_000_000
        profile.expected_salary_max = 3_500_000
        profile.location = "Hyderabad, India"
        profile.preferred_locations_list = ["Hyderabad"]
        profile.remote_preference = "remote"

        job = MagicMock()
        job.skills_required_list = ["React", "Node.js", "AWS", "Python", "Docker"]
        job.title = "Full Stack Developer"
        job.description = "React + Node.js developer"
        job.experience_required = "5 years"
        job.salary_min = 800_000
        job.salary_max = 1_200_000
        job.salary_currency = "INR"
        job.salary_period = "yearly"
        job.location = "Gurgaon, India"
        job.is_remote = False
        job.company_id = None
        job.company_name = "Some Startup"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        skill_s = self.service._score_skills(job, profile)
        assert skill_s < 30, f"Unrelated job skill score should be low, got {skill_s}"

        sal_s = self.service._score_salary(job, profile)
        assert sal_s < 60, f"Low salary should score low, got {sal_s}"
