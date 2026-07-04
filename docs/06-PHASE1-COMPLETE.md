# CareerPilot AI — Phase 1 Progress Report

> **Date:** 2026-07-05
> **Phase:** Phase 1 — Backend Foundation ✅ COMPLETE
> **Next:** Phase 2 — AI Matching + Scoring + Dedup

---

## What Was Built (Phase 1)

### Backend API — 15 files, ~4,250 lines of code

| File | Purpose | Status |
|------|---------|:------:|
| `backend/app/config.py` | All settings from .env, AEM scoring weights, salary targets | ✅ |
| `backend/app/database.py` | SQLite connection with WAL mode, FTS5, pragma tuning | ✅ |
| `backend/app/models.py` | 9 SQLAlchemy ORM models (Profile, Company, Job, Application, etc.) | ✅ |
| `backend/app/schemas.py` | 20+ Pydantic request/response schemas | ✅ |
| `backend/app/main.py` | FastAPI app with CORS, lifespan, router registration | ✅ |
| `backend/app/routers/health.py` | `/health` — checks DB, Ollama, Gemini status | ✅ |
| `backend/app/routers/profile.py` | Profile CRUD + India CTC salary calculator | ✅ |
| `backend/app/routers/jobs.py` | Job listing, search, filters, FTS5, stats | ✅ |
| `backend/app/routers/applications.py` | Application tracking, status updates, follow-ups | ✅ |
| `backend/app/connectors/base.py` | Connector SDK: authenticate, search_jobs, normalize, health_check | ✅ |
| `backend/app/connectors/jsearch.py` | JSearch API (LinkedIn+Indeed+Naukri via Google for Jobs) | ✅ |
| `backend/app/connectors/adzuna.py` | Adzuna API (additional India jobs) | ✅ |
| `backend/app/services/llm.py` | LLM service with smart Ollama/Gemini routing | ✅ |
| `backend/app/services/embeddings.py` | Embedding service (nomic-embed-text + ChromaDB) | ✅ |
| `backend/app/services/telegram.py` | Telegram notifications (job alerts, digests, reminders) | ✅ |
| `backend/app/services/job_service.py` | Multi-source search orchestration + persistence | ✅ |
| `backend/Dockerfile` | Container build for backend | ✅ |
| `docker-compose.yml` | 3-service Docker setup (backend, frontend, ollama) | ✅ |
| `backend/tests/test_backend.py` | 34 passing tests | ✅ |

### API Endpoints (13 working)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (DB + Ollama + Gemini status) |
| GET | `/api/profile/` | Get your profile |
| PUT | `/api/profile/` | Update profile (partial) |
| POST | `/api/profile/resume-text` | Update parsed resume text |
| GET | `/api/profile/salary-calculator` | India CTC → in-hand calculator |
| GET | `/api/jobs/` | List jobs with filters (remote, source, search, score) |
| GET | `/api/jobs/{id}` | Get single job |
| POST | `/api/jobs/search` | Search external APIs (JSearch, Adzuna) |
| POST | `/api/jobs/score` | Score job match (placeholder for Phase 2) |
| DELETE | `/api/jobs/{id}` | Soft-delete job |
| GET | `/api/jobs/stats/summary` | Dashboard stats |
| POST | `/api/applications/` | Create application |
| PUT | `/api/applications/{id}` | Update application status |
| GET | `/api/applications/stats/summary` | Application stats |
| GET | `/api/applications/followups/upcoming` | Follow-up reminders |

### Test Results
```
34 tests PASSED:
  - 4 config tests
  - 6 model tests
  - 1 health endpoint test
  - 4 profile endpoint tests
  - 7 job endpoint tests
  - 5 application endpoint tests
  - 2 JSearch connector tests
  - 2 Adzuna connector tests
  - 2 NormalizedJob tests
```

---

## What's NOT Done Yet (Phase 2+)

| Feature | Phase | Priority |
|---------|-------|:--------:|
| AI job scoring (skill match, experience match, salary match, etc.) | Phase 2 | 🔴 High |
| Job deduplication (embedding similarity + fuzzy match) | Phase 2 | 🔴 High |
| Keyword extraction from job descriptions | Phase 2 | 🟡 Medium |
| Resume tailoring agent (Gemini Flash) | Phase 3 | 🔴 High |
| Cover letter generation agent | Phase 3 | 🟡 Medium |
| Next.js frontend dashboard | Phase 4 | 🔴 High |
| Google Sheets sync service | Phase 4 | 🟡 Medium |
| Telegram bot daily job search scheduler | Phase 4 | 🟡 Medium |
| Chrome extension (MV3, unpacked) | Phase 5 | 🟢 Nice |
| Interview prep agent | Phase 5 | 🟡 Medium |
| Company research agent (Serper + Gemini) | Phase 5 | 🟢 Nice |
| Greenhouse/Lever connectors | Phase 5 | 🟢 Nice |

---

## Key Architecture Decisions Made

1. **Ollama for background tasks** (scoring, dedup) — free, unlimited, ~15 sec/job
2. **Gemini Flash for interactive tasks** (resume, cover letter) — fast, 500 RPD free
3. **SQLite with WAL mode** — concurrent reads, single writer, zero setup
4. **ChromaDB for embeddings** — just a folder, no server needed
5. **JSearch as primary source** — legal, covers LinkedIn/Indeed/Naukri
6. **Telegram for notifications** — instant, free, phone-accessible
7. **FTS5 for full-text search** — built into SQLite, fast job search
8. **India-first** — CTC calculator, LPA salary display, Hyderabad default

---

## To Start Phase 2: AI Matching + Scoring

The next step is building the scoring pipeline that:
1. Takes a job + your profile
2. Computes skill_match (30%), experience_match (25%), salary_match (15%), location_match (10%), company_quality (10%), remote_preference (10%)
3. Uses Ollama for LLM reasoning on why it's a good/bad match
4. Stores match_score, strengths, weaknesses, recommendations
5. Auto-scores new jobs as they come in

Say "go" when ready for Phase 2!
