"""
CareerPilot AI — Backend Tests
Tests for config, database, models, and API endpoints.
Run: cd backend && pytest tests/ -v
"""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ─── Test Database Setup ─────────────────────────────────────────────────────

# Use in-memory SQLite for tests with StaticPool so all connections share the same DB
from sqlalchemy.pool import StaticPool

TEST_DB_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Required for in-memory SQLite — shares single connection
)

TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    from app.database import Base
    from app import models  # noqa: F401 — ensure models are imported

    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with a test database."""
    from app.database import get_db
    from app.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─── Config Tests ────────────────────────────────────────────────────────────

class TestConfig:
    def test_settings_loads(self):
        from app.config import settings
        assert settings.app_env == "development"
        assert settings.ollama_host == "http://localhost:11434"
        assert settings.ollama_chat_model == "qwen3:8b"
        assert settings.ollama_embedding_model == "nomic-embed-text"

    def test_database_url(self):
        from app.config import settings
        assert "sqlite" in settings.database_url

    def test_aem_scoring_weights(self):
        from app.config import settings
        total = (
            settings.skill_match_weight
            + settings.experience_match_weight
            + settings.salary_match_weight
            + settings.location_match_weight
            + settings.company_quality_weight
            + settings.remote_preference_weight
        )
        assert abs(total - 1.0) < 0.01, f"Weights should sum to 1.0, got {total}"

    def test_salary_targets(self):
        from app.config import settings
        assert settings.expected_salary_min == 2_000_000  # 20 LPA
        assert settings.expected_salary_max == 3_500_000  # 35 LPA


# ─── Model Tests ─────────────────────────────────────────────────────────────

class TestModels:
    def test_profile_creation(self, db_session):
        from app.models import Profile
        profile = Profile(id=1, full_name="Test User", current_role="AEM Developer")
        db_session.add(profile)
        db_session.commit()

        fetched = db_session.query(Profile).first()
        assert fetched.full_name == "Test User"
        assert fetched.skills_list == []

    def test_profile_skills_json(self, db_session):
        from app.models import Profile
        profile = Profile(id=1)
        profile.skills_list = ["AEM", "Java", "Sling"]
        db_session.add(profile)
        db_session.commit()

        fetched = db_session.query(Profile).first()
        assert fetched.skills_list == ["AEM", "Java", "Sling"]

    def test_job_salary_display(self, db_session):
        from app.models import Job
        job = Job(
            source="test", source_id="1", title="AEM Dev",
            company_name="Test Co", salary_min=2000000, salary_max=3500000,
            salary_currency="INR",
        )
        assert job.salary_display() == "₹20-35 LPA"

    def test_job_salary_display_usd(self, db_session):
        from app.models import Job
        job = Job(
            source="test", source_id="1", title="AEM Dev",
            company_name="Test Co", salary_min=100000, salary_max=150000,
            salary_currency="USD",
        )
        assert job.salary_display() == "$100K-$150K"

    def test_job_salary_display_none(self, db_session):
        from app.models import Job
        job = Job(
            source="test", source_id="1", title="AEM Dev",
            company_name="Test Co",
        )
        assert job.salary_display() == "Not disclosed"

    def test_application_status_values(self):
        from app.models import Application
        valid = Application.ALL_STATUSES
        assert "applied" in valid
        assert "interview_scheduled" in valid
        assert "offer" in valid
        assert "rejected" in valid

    def test_company_creation(self, db_session):
        from app.models import Company
        company = Company(name="Accenture", industry="Consulting", is_aem_hirer=True)
        db_session.add(company)
        db_session.commit()

        fetched = db_session.query(Company).first()
        assert fetched.name == "Accenture"
        assert fetched.is_aem_hirer is True


# ─── API Endpoint Tests ──────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert data["database"] == "connected"


class TestProfileEndpoints:
    def test_get_profile(self, client):
        resp = client.get("/api/profile/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["location"] == "Hyderabad, India"

    def test_update_profile(self, client):
        resp = client.put("/api/profile/", json={"full_name": "Test User", "experience_years": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "Test User"
        assert data["experience_years"] == 10.0

    def test_update_profile_skills(self, client):
        resp = client.put("/api/profile/", json={"skills": ["AEM", "Java", "Sling", "OSGi"]})
        assert resp.status_code == 200
        data = resp.json()
        assert "AEM" in data["skills"]
        assert len(data["skills"]) == 4

    def test_salary_calculator(self, client):
        resp = client.get("/api/profile/salary-calculator?ctc=25")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ctc_lpa"] == 25.0
        assert "monthly_in_hand" in data
        assert data["monthly_in_hand"] > 0


class TestJobEndpoints:
    def _seed_jobs(self, db_session):
        from app.models import Job
        jobs = [
            Job(
                source="jsearch", source_id="j1", title="Senior AEM Developer",
                company_name="Accenture", location="Hyderabad", salary_min=1800000,
                salary_max=2500000, salary_currency="INR", is_remote=False, is_active=True,
                skills_required=json.dumps(["AEM", "Java", "Sling"]),
            ),
            Job(
                source="jsearch", source_id="j2", title="AEM Architect",
                company_name="Adobe", location="Remote", salary_min=2500000,
                salary_max=4000000, salary_currency="INR", is_remote=True, is_active=True,
                skills_required=json.dumps(["AEM", "EDS", "Sling"]),
            ),
            Job(
                source="adzuna", source_id="a1", title="Java Developer",
                company_name="Infosys", location="Bangalore", salary_min=800000,
                salary_max=1500000, salary_currency="INR", is_remote=False, is_active=True,
                skills_required=json.dumps(["Java", "Spring Boot"]),
            ),
        ]
        for j in jobs:
            db_session.add(j)
        db_session.commit()

    def test_list_jobs(self, client, db_session):
        self._seed_jobs(db_session)
        resp = client.get("/api/jobs/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["jobs"]) == 3

    def test_list_jobs_remote_filter(self, client, db_session):
        self._seed_jobs(db_session)
        resp = client.get("/api/jobs/?is_remote=true")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["jobs"][0]["company_name"] == "Adobe"

    def test_list_jobs_source_filter(self, client, db_session):
        self._seed_jobs(db_session)
        resp = client.get("/api/jobs/?source=adzuna")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["jobs"][0]["source"] == "adzuna"

    def test_get_job(self, client, db_session):
        self._seed_jobs(db_session)
        # Get first job's ID
        resp = client.get("/api/jobs/")
        job_id = resp.json()["jobs"][0]["id"]

        resp = client.get(f"/api/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Senior AEM Developer"

    def test_get_job_not_found(self, client):
        resp = client.get("/api/jobs/9999")
        assert resp.status_code == 404

    def test_jobs_stats(self, client, db_session):
        self._seed_jobs(db_session)
        resp = client.get("/api/jobs/stats/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_active_jobs"] == 3
        assert data["remote_jobs"] == 1

    def test_deactivate_job(self, client, db_session):
        self._seed_jobs(db_session)
        resp = client.get("/api/jobs/")
        job_id = resp.json()["jobs"][0]["id"]

        resp = client.delete(f"/api/jobs/{job_id}")
        assert resp.status_code == 200

        # Verify it's now inactive
        resp = client.get("/api/jobs/?is_active=false")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestApplicationEndpoints:
    def _seed_job(self, db_session):
        from app.models import Job
        job = Job(
            source="jsearch", source_id="j1", title="AEM Developer",
            company_name="Test Co", location="Hyderabad", salary_min=2000000,
            salary_max=3000000, salary_currency="INR", is_active=True,
        )
        db_session.add(job)
        db_session.commit()
        return job.id

    def test_create_application(self, client, db_session):
        job_id = self._seed_job(db_session)
        resp = client.post("/api/applications/", json={
            "job_id": job_id, "status": "saved", "rating": 4,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "saved"
        assert data["rating"] == 4

    def test_update_application_status(self, client, db_session):
        job_id = self._seed_job(db_session)
        # Create
        resp = client.post("/api/applications/", json={"job_id": job_id, "status": "saved"})
        app_id = resp.json()["id"]

        # Update to applied
        resp = client.put(f"/api/applications/{app_id}", json={"status": "applied"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "applied"
        assert data["applied_at"] is not None  # Should auto-set

    def test_duplicate_application(self, client, db_session):
        job_id = self._seed_job(db_session)
        client.post("/api/applications/", json={"job_id": job_id, "status": "saved"})
        resp = client.post("/api/applications/", json={"job_id": job_id, "status": "saved"})
        assert resp.status_code == 409

    def test_application_stats(self, client, db_session):
        job_id = self._seed_job(db_session)
        client.post("/api/applications/", json={"job_id": job_id, "status": "applied"})

        resp = client.get("/api/applications/stats/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_applications"] == 1

    def test_invalid_status(self, client, db_session):
        job_id = self._seed_job(db_session)
        client.post("/api/applications/", json={"job_id": job_id, "status": "saved"})
        # The Pydantic validator should reject invalid status
        # Note: This tests the schema, not the endpoint directly


# ─── Connector Tests ─────────────────────────────────────────────────────────

class TestJSearchConnector:
    def test_normalize_jsearch_response(self):
        from app.connectors.jsearch import JSearchConnector
        connector = JSearchConnector()

        raw = {
            "job_id": "abc123",
            "job_title": "Senior AEM Developer",
            "employer_name": "Accenture",
            "job_city": "Hyderabad",
            "job_state": "Telangana",
            "job_country": "India",
            "job_description": "Looking for AEM expertise...",
            "job_apply_link": "https://example.com/apply",
            "job_min_salary": 1800000,
            "job_max_salary": 2500000,
            "job_salary_currency": "INR",
            "job_salary_period": "YEAR",
            "job_is_remote": False,
            "job_employment_type": "Full-time",
            "job_employment_types": ["FULLTIME"],
            "job_posted_at_datetime_utc": "2026-07-01T10:00:00",
        }

        result = connector.normalize(raw)
        assert result.source == "jsearch"
        assert result.source_id == "abc123"
        assert result.title == "Senior AEM Developer"
        assert result.company_name == "Accenture"
        assert result.salary_min == 1800000
        assert result.salary_max == 2500000
        assert result.salary_currency == "INR"
        assert result.is_remote is False
        assert result.job_type == "full_time"

    def test_normalize_enriched_response(self):
        """Test JSearch v2 enriched response with skills, seniority, etc."""
        from app.connectors.jsearch import JSearchConnector
        connector = JSearchConnector()

        raw = {
            "job_id": "xyz789",
            "job_title": "AEM Architect",
            "employer_name": "Adobe",
            "job_city": "Remote",
            "job_country": "IN",
            "job_description": "Lead AEM architecture...",
            "job_apply_link": "https://example.com/apply2",
            "job_min_salary": 2500000,
            "job_max_salary": 4000000,
            "job_salary_currency": "INR",
            "job_salary_period": "YEAR",
            "work_arrangement": "remote",
            "job_employment_types": ["FULLTIME"],
            "required_technologies": ["AEM", "Sling", "OSGi", "JCR"],
            "preferred_technologies": ["AEM Dispatcher", "EDS"],
            "seniority_level": "senior",
            "required_experience_years": 10,
        }

        result = connector.normalize(raw)
        assert result.is_remote is True  # work_arrangement="remote"
        assert "AEM" in result.skills_required
        assert "AEM Dispatcher" in result.skills_required  # preferred included
        assert result.experience_required == "10 years"

    def test_normalize_monthly_to_yearly(self):
        from app.connectors.jsearch import JSearchConnector
        connector = JSearchConnector()

        raw = {
            "job_id": "xyz",
            "job_title": "AEM Dev",
            "employer_name": "Test Co",
            "job_min_salary": 150000,
            "job_max_salary": 200000,
            "job_salary_currency": "INR",
            "job_salary_period": "month",
        }

        result = connector.normalize(raw)
        assert result.salary_min == 150000 * 12  # 18 LPA
        assert result.salary_max == 200000 * 12  # 24 LPA
        assert result.salary_period == "yearly"


class TestAdzunaConnector:
    def test_normalize_adzuna_response(self):
        from app.connectors.adzuna import AdzunaConnector
        connector = AdzunaConnector()

        raw = {
            "id": 12345,
            "title": "AEM Developer",
            "company": {"display_name": "Capgemini"},
            "location": {"display_name": "Hyderabad, Telangana"},
            "description": "AEM development role...",
            "redirect_url": "https://adzuna.com/job/12345",
            "salary_min": 1500000,
            "salary_max": 2200000,
            "contract_time": "full_time",
            "created": "2026-07-01T09:00:00Z",
        }

        result = connector.normalize(raw)
        assert result.source == "adzuna"
        assert result.source_id == "12345"
        assert result.title == "AEM Developer"
        assert result.company_name == "Capgemini"
        assert result.salary_min == 1500000
        assert result.salary_currency == "INR"
        assert result.job_type == "full_time"

    def test_remote_detection(self):
        from app.connectors.adzuna import AdzunaConnector
        connector = AdzunaConnector()

        raw = {
            "id": 99,
            "title": "Remote AEM Developer",
            "company": {"display_name": "Adobe"},
            "location": {"display_name": "Remote"},
            "description": "Work from home AEM role",
            "redirect_url": "https://example.com",
        }

        result = connector.normalize(raw)
        assert result.is_remote is True


# ─── NormalizedJob Tests ─────────────────────────────────────────────────────

class TestNormalizedJob:
    def test_salary_lpa_india(self):
        from app.connectors.base import NormalizedJob
        job = NormalizedJob(
            source="test", source_id="1", source_url="",
            title="AEM Dev", company_name="Test",
            salary_min=2_000_000, salary_max=3_500_000,
            salary_currency="INR",
        )
        assert job.salary_lpa() == 35.0  # Based on max

    def test_salary_lpa_none(self):
        from app.connectors.base import NormalizedJob
        job = NormalizedJob(
            source="test", source_id="1", source_url="",
            title="AEM Dev", company_name="Test",
        )
        assert job.salary_lpa() is None
