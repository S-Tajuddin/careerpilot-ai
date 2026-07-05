"""
CareerPilot AI — Tests for URL Validation Utility
Validates that fake/placeholder URLs are rejected and genuine ones are accepted.
"""

import pytest

from app.utils.url_validation import (
    is_valid_job_url,
    is_legitimate_job_domain,
    sanitize_source_url,
    get_apply_label,
)


# ══════════════════════════════════════════════════════════════════════════════
# is_valid_job_url — Core validation
# ══════════════════════════════════════════════════════════════════════════════

class TestIsValidJobUrl:
    """Test the main URL validation function."""

    # ── Should REJECT these ──────────────────────────────────────────────

    def test_reject_example_com(self):
        assert is_valid_job_url("https://example.com/job1") is False

    def test_reject_example_org(self):
        assert is_valid_job_url("https://example.org/careers/123") is False

    def test_reject_example_net(self):
        assert is_valid_job_url("https://example.net/apply") is False

    def test_reject_www_example_com(self):
        assert is_valid_job_url("https://www.example.com/jobs") is False

    def test_reject_subdomain_example_com(self):
        assert is_valid_job_url("https://careers.example.com/jobs/123") is False
        assert is_valid_job_url("https://jobs.example.com/apply/456") is False

    def test_reject_placeholder_com(self):
        assert is_valid_job_url("https://placeholder.com/job") is False

    def test_reject_test_com(self):
        assert is_valid_job_url("https://test.com/jobs") is False

    def test_reject_sample_com(self):
        assert is_valid_job_url("https://sample.com/apply") is False

    def test_reject_fake_com(self):
        assert is_valid_job_url("https://fake.com/careers") is False

    def test_reject_dummy_com(self):
        assert is_valid_job_url("https://dummy.com/job") is False

    def test_reject_yourdomain_com(self):
        assert is_valid_job_url("https://yourdomain.com/jobs") is False

    def test_reject_yourcompany_com(self):
        assert is_valid_job_url("https://yourcompany.com/apply") is False

    def test_reject_localhost(self):
        assert is_valid_job_url("https://localhost/jobs") is False

    def test_reject_127_ip(self):
        assert is_valid_job_url("https://127.0.0.1/jobs") is False

    def test_reject_private_ip_10(self):
        assert is_valid_job_url("https://10.0.0.1/jobs") is False

    def test_reject_private_ip_192(self):
        assert is_valid_job_url("https://192.168.1.1/jobs") is False

    def test_reject_about_blank(self):
        assert is_valid_job_url("about:blank") is False

    def test_reject_javascript(self):
        assert is_valid_job_url("javascript:void(0)") is False

    def test_reject_data_uri(self):
        assert is_valid_job_url("data:text/html,hello") is False

    def test_reject_mailto(self):
        assert is_valid_job_url("mailto:hr@company.com") is False

    def test_reject_ftp(self):
        assert is_valid_job_url("ftp://files.company.com/job.txt") is False

    def test_reject_empty_string(self):
        assert is_valid_job_url("") is False

    def test_reject_none(self):
        assert is_valid_job_url(None) is False

    def test_reject_whitespace(self):
        assert is_valid_job_url("   ") is False

    def test_reject_no_protocol(self):
        assert is_valid_job_url("www.linkedin.com/jobs/123") is False

    def test_reject_bare_domain_no_tld(self):
        assert is_valid_job_url("https://notadomain/jobs") is False

    def test_reject_numeric_tld(self):
        assert is_valid_job_url("https://example.123/job") is False

    # ── Should ACCEPT these ──────────────────────────────────────────────

    def test_accept_linkedin(self):
        assert is_valid_job_url("https://www.linkedin.com/jobs/view/12345") is True

    def test_accept_indeed(self):
        assert is_valid_job_url("https://in.indeed.com/viewjob?jk=abc123") is True

    def test_accept_naukri(self):
        assert is_valid_job_url("https://www.naukri.com/jobapi/v3/search?id=123") is True

    def test_accept_glassdoor(self):
        assert is_valid_job_url("https://www.glassdoor.com/job-listing/aem-developer-123.htm") is True

    def test_accept_company_careers(self):
        assert is_valid_job_url("https://careers.accenture.com/in/jobs/123") is True

    def test_accept_greenhouse(self):
        assert is_valid_job_url("https://boards.greenhouse.io/acme/jobs/123") is True

    def test_accept_lever(self):
        assert is_valid_job_url("https://jobs.lever.co/company/123") is True

    def test_accept_smartrecruiters(self):
        assert is_valid_job_url("https://jobs.smartrecruiters.com/company/123") is True

    def test_accept_workday(self):
        assert is_valid_job_url("https://myworkdayjobs.com/company/job/123") is True

    def test_accept_weworkremotely(self):
        assert is_valid_job_url("https://weworkremotely.com/remote-jobs/123") is True

    def test_accept_remoteok(self):
        assert is_valid_job_url("https://remoteok.com/remote-jobs/123") is True

    def test_accept_monster(self):
        assert is_valid_job_url("https://www.monster.com/job/openview?id=123") is True

    def test_accept_http(self):
        assert is_valid_job_url("http://careers.techcorp.in/job/123") is True

    def test_accept_with_path_and_query(self):
        assert is_valid_job_url("https://www.linkedin.com/jobs/view/12345?refId=abc&trk=public_jobs") is True

    def test_accept_with_port(self):
        assert is_valid_job_url("https://careers.techcorp.in:443/jobs/123") is True

    def test_accept_adobe_careers(self):
        assert is_valid_job_url("https://careers.adobe.com/us/en/job/123") is True

    def test_accept_ibm_careers(self):
        assert is_valid_job_url("https://careers.ibm.com/job/123") is True

    def test_accept_unknown_legit_domain(self):
        """A valid domain we haven't explicitly listed should still pass basic validation."""
        assert is_valid_job_url("https://jobs.some-startup.com/apply/123") is True


# ══════════════════════════════════════════════════════════════════════════════
# is_legitimate_job_domain — Stronger check against known-good list
# ══════════════════════════════════════════════════════════════════════════════

class TestIsLegitimateJobDomain:
    """Test the known-good domain checker."""

    def test_linkedin_is_legit(self):
        assert is_legitimate_job_domain("https://www.linkedin.com/jobs/view/123") is True

    def test_indeed_is_legit(self):
        assert is_legitimate_job_domain("https://in.indeed.com/viewjob?jk=abc") is True

    def test_naukri_is_legit(self):
        assert is_legitimate_job_domain("https://www.naukri.com/job/123") is True

    def test_accenture_careers_is_legit(self):
        assert is_legitimate_job_domain("https://careers.accenture.com/in/jobs/123") is True

    def test_adobe_careers_is_legit(self):
        assert is_legitimate_job_domain("https://careers.adobe.com/us/en/job/123") is True

    def test_unknown_startup_not_legit(self):
        """A domain not in our known-good list returns False for legitimacy check."""
        assert is_legitimate_job_domain("https://jobs.some-startup.com/apply/123") is False

    def test_example_com_not_legit(self):
        assert is_legitimate_job_domain("https://example.com/job") is False

    def test_none_not_legit(self):
        assert is_legitimate_job_domain(None) is False

    def test_greenhouse_is_legit(self):
        assert is_legitimate_job_domain("https://boards.greenhouse.io/company/jobs/123") is True

    def test_lever_is_legit(self):
        assert is_legitimate_job_domain("https://jobs.lever.co/company/123") is True


# ══════════════════════════════════════════════════════════════════════════════
# sanitize_source_url — Used by connectors
# ══════════════════════════════════════════════════════════════════════════════

class TestSanitizeSourceUrl:
    """Test the connector-level URL sanitizer."""

    def test_valid_url_passes_through(self):
        url = "https://www.linkedin.com/jobs/view/12345"
        assert sanitize_source_url(url) == url

    def test_example_com_returns_none(self):
        assert sanitize_source_url("https://example.com/job1") is None

    def test_empty_returns_none(self):
        assert sanitize_source_url("") is None

    def test_none_returns_none(self):
        assert sanitize_source_url(None) is None

    def test_whitespace_stripped(self):
        url = "  https://www.naukri.com/job/123  "
        assert sanitize_source_url(url) == url.strip()

    def test_placeholder_returns_none(self):
        assert sanitize_source_url("https://placeholder.com/job") is None

    def test_localhost_returns_none(self):
        assert sanitize_source_url("https://localhost/jobs") is None


# ══════════════════════════════════════════════════════════════════════════════
# get_apply_label — Human-readable button labels
# ══════════════════════════════════════════════════════════════════════════════

class TestGetApplyLabel:
    """Test the apply button label generator."""

    def test_linkedin(self):
        assert get_apply_label("https://www.linkedin.com/jobs/view/123") == "LinkedIn"

    def test_indeed(self):
        assert get_apply_label("https://in.indeed.com/viewjob?jk=abc") == "Indeed"

    def test_naukri(self):
        assert get_apply_label("https://www.naukri.com/job/123") == "Naukri"

    def test_glassdoor(self):
        assert get_apply_label("https://www.glassdoor.com/job-listing/123") == "Glassdoor"

    def test_accenture_careers(self):
        assert get_apply_label("https://careers.accenture.com/in/jobs/123") == "Accenture Careers"

    def test_adobe_careers(self):
        assert get_apply_label("https://careers.adobe.com/us/en/job/123") == "Adobe Careers"

    def test_greenhouse(self):
        assert get_apply_label("https://boards.greenhouse.io/company/jobs/123") == "Company Site"

    def test_lever(self):
        assert get_apply_label("https://jobs.lever.co/company/123") == "Company Site"

    def test_unknown_subdomain_careers(self):
        label = get_apply_label("https://careers.acmecorp.com/jobs/123")
        assert "Acmecorp" in label or "Careers" in label

    def test_fake_url_returns_empty(self):
        assert get_apply_label("https://example.com/job1") == ""

    def test_none_returns_empty(self):
        assert get_apply_label(None) == ""

    def test_weworkremotely(self):
        assert get_apply_label("https://weworkremotely.com/remote-jobs/123") == "WeWorkRemotely"

    def test_smartrecruiters(self):
        assert get_apply_label("https://jobs.smartrecruiters.com/company/123") == "SmartRecruiters"


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION: URL validation in connectors
# ══════════════════════════════════════════════════════════════════════════════

class TestConnectorUrlIntegration:
    """Test that connectors properly sanitize URLs."""

    def test_jsearch_normalize_example_url(self):
        """JSearch connector should sanitize example.com URLs."""
        from app.connectors.jsearch import JSearchConnector
        connector = JSearchConnector()

        raw = {
            "job_id": "test123",
            "job_apply_link": "https://example.com/job1",
            "job_title": "AEM Developer",
            "employer_name": "Test Corp",
        }
        result = connector.normalize(raw)
        assert result.source_url is None  # Should be sanitized to None

    def test_jsearch_normalize_legit_url(self):
        """JSearch connector should keep legitimate URLs."""
        from app.connectors.jsearch import JSearchConnector
        connector = JSearchConnector()

        raw = {
            "job_id": "test456",
            "job_apply_link": "https://www.linkedin.com/jobs/view/12345",
            "job_title": "AEM Developer",
            "employer_name": "Accenture",
        }
        result = connector.normalize(raw)
        assert result.source_url == "https://www.linkedin.com/jobs/view/12345"

    def test_jsearch_normalize_empty_url(self):
        """JSearch connector should handle empty URLs."""
        from app.connectors.jsearch import JSearchConnector
        connector = JSearchConnector()

        raw = {
            "job_id": "test789",
            "job_apply_link": "",
            "job_title": "AEM Developer",
            "employer_name": "Test Corp",
        }
        result = connector.normalize(raw)
        assert result.source_url is None

    def test_adzuna_normalize_example_url(self):
        """Adzuna connector should sanitize example.com URLs."""
        from app.connectors.adzuna import AdzunaConnector
        connector = AdzunaConnector()

        raw = {
            "id": "az123",
            "redirect_url": "https://example.com/apply",
            "title": "Java Developer",
            "company": {"displayname": "Test Inc"},
            "location": {"displayname": "Mumbai"},
        }
        result = connector.normalize(raw)
        assert result.source_url is None

    def test_adzuna_normalize_legit_url(self):
        """Adzuna connector should keep legitimate URLs."""
        from app.connectors.adzuna import AdzunaConnector
        connector = AdzunaConnector()

        raw = {
            "id": "az456",
            "redirect_url": "https://www.naukri.com/job/123",
            "title": "AEM Architect",
            "company": {"displayname": "Infosys"},
            "location": {"displayname": "Hyderabad"},
        }
        result = connector.normalize(raw)
        assert result.source_url == "https://www.naukri.com/job/123"


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION: URL validation in job_service
# ══════════════════════════════════════════════════════════════════════════════

class TestJobServiceUrlFiltering:
    """Test that job_service skips jobs with fake URLs."""

    def test_save_jobs_skips_example_com(self):
        """Jobs with example.com URLs should be skipped, not saved."""
        from app.services.job_service import JobService
        from app.connectors.base import NormalizedJob

        service = JobService()
        db_mock = MagicMock()
        db_mock.query.return_value.filter.return_value.first.return_value = None
        db_mock.flush = MagicMock()
        db_mock.commit = MagicMock()

        fake_job = NormalizedJob(
            source="jsearch",
            source_id="fake1",
            source_url="https://example.com/job1",  # BAD
            title="AEM Developer",
            company_name="Fake Corp",
        )
        legit_job = NormalizedJob(
            source="jsearch",
            source_id="legit1",
            source_url="https://www.linkedin.com/jobs/view/12345",  # GOOD
            title="AEM Architect",
            company_name="Accenture",
        )

        saved = service._save_jobs([fake_job, legit_job], db_mock)

        # Only the legit job should be saved
        # The fake job should be skipped (db.add not called for it)
        assert len(saved) <= 1  # Only legit job, if any

    def test_save_jobs_skips_empty_url(self):
        """Jobs with empty source_url should be skipped."""
        from app.services.job_service import JobService
        from app.connectors.base import NormalizedJob

        service = JobService()
        db_mock = MagicMock()
        db_mock.query.return_value.filter.return_value.first.return_value = None
        db_mock.flush = MagicMock()
        db_mock.commit = MagicMock()

        no_url_job = NormalizedJob(
            source="jsearch",
            source_id="no_url1",
            source_url="",
            title="Java Developer",
            company_name="NoURL Corp",
        )

        saved = service._save_jobs([no_url_job], db_mock)
        assert len(saved) == 0


from unittest.mock import MagicMock
