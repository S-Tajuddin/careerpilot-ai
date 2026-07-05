# CareerPilot AI

> **Personal AI-powered career assistant** for an AEM/EDS Developer targeting Senior/Architect roles in India + Remote.  
> **Not a SaaS** — single-user tool running locally on a Lenovo ThinkBook 14 (i7, 16GB RAM, no GPU).

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Data Flow](#-data-flow)
- [Project Structure](#-project-structure)
- [Implementation Status](#-implementation-status)
- [Setup & Run](#-setup--run)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Tech Stack](#-tech-stack)

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CareerPilot AI                               │
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐    │
│  │   Frontend   │     │   Backend    │     │     Ollama       │    │
│  │  Next.js 14  │────▶│   FastAPI    │────▶│  qwen3:8b       │    │
│  │  Port 3000   │◀────│  Port 8000   │     │  nomic-embed    │    │
│  │  React 18    │     │  SQLite DB   │     │  Port 11434     │    │
│  └──────────────┘     └──────┬───────┘     └──────────────────┘    │
│                              │                                      │
│                    ┌─────────┼──────────┐                           │
│                    ▼         ▼          ▼                           │
│            ┌──────────┐ ┌────────┐ ┌──────────┐                    │
│            │  JSearch  │ │Adzuna │ │  Gemini  │                    │
│            │  (OpenWeb │ │  API  │ │  Flash   │                    │
│            │  Ninja)   │ │       │ │ (500RPD) │                    │
│            └──────────┘ └────────┘ └──────────┘                    │
│                                                      │             │
│                                              ┌───────▼────────┐    │
│                                              │   Telegram Bot  │    │
│                                              │   (Notifications)│    │
│                                              └────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Docker Compose (3 Services)

```yaml
services:
  backend:   # FastAPI + SQLite + all services
  frontend:  # Next.js 14.2.35 (pinned — Next 16 breaks Turbopack)
  ollama:    # LLM + embeddings (CPU only)
```

### Key Architecture Decisions

| Decision | Why |
|----------|-----|
| **SQLite** (not PostgreSQL) | One file, zero setup, perfect for single-user |
| **Ollama qwen3:8b** | Free, unlimited, runs on CPU at ~8-15 tok/s |
| **Gemini Flash** | Free 500 RPD, used for interactive tasks (resume parsing, company research) |
| **Two-tier scoring** | Quick Score (instant, deterministic) for auto-scoring; Deep Score (LLM) on-demand only |
| **Two-tier dedup** | Heuristic (title+company, instant) for auto; Semantic (embeddings) for manual trigger |
| **JSearch via OpenWeb Ninja** | Direct API, no RapidAPI wrapper needed; aggregates Google for Jobs (legal) |
| **Next.js 14.2.35 pinned** | Next 16 Turbopack causes build failures |
| **No auth/RBAC/billing** | Personal tool, single user |

---

## 🔄 Data Flow

### Flow 1: Resume Upload → Profile → Search

```
┌────────────────────────────────────────────────────────────────────────────┐
│  RESUME UPLOAD FLOW                                                        │
│                                                                            │
│  User drops PDF/DOCX on Profile page                                       │
│         │                                                                  │
│         ▼                                                                  │
│  Frontend ──POST /api/profile/resume-upload──▶ Backend                     │
│         │                                       │                         │
│         │                                       ▼                         │
│         │                              Save file to data/resumes/          │
│         │                                       │                         │
│         │                                       ▼                         │
│         │                              Extract text (PyPDF2 / python-docx) │
│         │                                       │                         │
│         │                                       ▼                         │
│         │                              Send to Gemini Flash for parsing    │
│         │                              ┌──────────────────────────┐       │
│         │                              │ Extracted:               │       │
│         │                              │  • full_name             │       │
│         │                              │  • skills (comprehensive)│       │
│         │                              │  • experience_years      │       │
│         │                              │  • current_role          │       │
│         │                              │  • target_roles          │       │
│         │                              │  • education             │       │
│         │                              │  • certifications        │       │
│         │                              │  • companies_worked      │       │
│         │                              │  • preferred_work_arr.   │       │
│         │                              └──────────┬───────────────┘       │
│         │                                         │                       │
│         │                                         ▼                       │
│         │                              Update Profile (merge skills)       │
│         │                                         │                       │
│         │                                         ▼                       │
│         │                              Re-score ALL existing jobs           │
│         │                              with updated profile                 │
│         │                                         │                       │
│         │                                         ▼                       │
│         │                              Generate search queries              │
│         │                              from resume skills+role              │
│         │                                         │                       │
│         ◀─────────────────────────────────────────┘                       │
│  Profile page shows: parsed data, skills chips, search query chips         │
└────────────────────────────────────────────────────────────────────────────┘
```

### Flow 2: Resume-Based Job Search

```
┌────────────────────────────────────────────────────────────────────────┐
│  RESUME SEARCH FLOW                                                     │
│                                                                         │
│  User clicks "🔍 Resume Search" on Profile or Jobs page                 │
│         │                                                               │
│         ▼                                                               │
│  GET /api/jobs/search-by-resume                                         │
│         │                                                               │
│         ▼                                                               │
│  Backend reads profile.resume_text                                      │
│         │                                                               │
│         ▼                                                               │
│  Generate 6-8 search queries from:                                      │
│    • target_role → "AEM Architect"                                      │
│    • skills → "AEM + Sling + OSGi developer"                            │
│    • experience → "senior AEM architect" (10+ yrs)                       │
│    • location → "AEM developer Hyderabad"                                │
│    • EDS skills → "Edge Delivery Services developer"                     │
│    • remote → "AEM architect remote"                                     │
│         │                                                               │
│         ▼                                                               │
│  For each query → search JSearch + Adzuna                               │
│         │                                                               │
│         ▼                                                               │
│  Save results → Quick Score each job → Heuristic dedup                  │
│         │                                                               │
│         ▼                                                               │
│  Return top jobs sorted by match_score (resume-prioritized)             │
└────────────────────────────────────────────────────────────────────────┘
```

### Flow 3: Two-Tier Scoring

```
┌──────────────────────────────────────────────────────────────────────┐
│  QUICK SCORE (auto, <1ms per job)          │  DEEP SCORE (on-demand) │
│                                             │                         │
│  6 dimensions:                              │  Quick Score +          │
│  ┌───────────────────┬──────────┐          │  ┌─────────────────┐   │
│  │ skill_match       │ weight:30│          │  │ LLM Recommend.  │   │
│  │ experience_match  │ weight:25│          │  │ (Ollama/Gemini) │   │
│  │ salary_match      │ weight:15│          │  └─────────────────┘   │
│  │ location_match    │ weight:10│          │  +                     │
│  │ company_quality   │ weight:10│          │  ┌─────────────────┐   │
│  │ remote_preference │ weight:10│          │  │ Embedding Store  │   │
│  └───────────────────┴──────────┘          │  │ (ChromaDB)      │   │
│  No LLM calls, no API calls               │  └─────────────────┘   │
│  Runs on every search result              │  ~5-15s per job         │
│                                             │  Manual trigger only    │
└──────────────────────────────────────────────────────────────────────┘
```

### Flow 4: Job Discovery Pipeline

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│  JSearch   │    │  Adzuna    │    │  Normalize │    │  Quick     │
│  /search-v2│───▶│  /search   │───▶│  → Job     │───▶│  Score     │
│  (primary) │    │  (India)   │    │  model     │    │  (6 dims)  │
└────────────┘    └────────────┘    └─────┬──────┘    └─────┬──────┘
                                          │                  │
                                          ▼                  ▼
                                    ┌────────────┐    ┌────────────┐
                                    │  Heuristic │    │  Update    │
                                    │  Dedup     │    │  DB        │
                                    │  (instant) │    │  + return  │
                                    └────────────┘    └────────────┘
```

### Flow 5: Cover Letter + Resume Tailoring

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DOCUMENT GENERATION FLOW                                                │
│                                                                          │
│  User clicks "Cover Letter" or "Tailor Resume" on a job card            │
│         │                                                                │
│         ▼                                                                │
│  POST /api/documents/cover-letter   OR   POST /api/documents/tailor-resume
│         │                                          │                     │
│         ▼                                          ▼                     │
│  ┌─────────────────────┐              ┌──────────────────────┐          │
│  │ Build prompt with:  │              │ Build prompt with:   │          │
│  │  • Job details      │              │  • Job requirements  │          │
│  │  • Profile + resume │              │  • FULL resume text  │          │
│  │  • Tone preference  │              │  • Skills list        │          │
│  │  • Notice period    │              │                      │          │
│  └─────────┬───────────┘              └──────────┬───────────┘          │
│            ▼                                     ▼                      │
│  ┌─────────────────────┐              ┌──────────────────────┐          │
│  │ Gemini Flash        │              │ Gemini Flash          │          │
│  │ (~2-3 seconds)      │              │ (~3-5 seconds)        │          │
│  │ Professional letter │              │ Reorganized resume    │          │
│  │ 3-4 paragraphs     │              │ Same facts, better    │          │
│  └─────────┬───────────┘              │ emphasis for THIS job │          │
│            ▼                          └──────────┬───────────┘          │
│  ┌─────────────────────┐                         ▼                      │
│  │ Save to DB + file   │              ┌──────────────────────┐          │
│  │ data/cover_letters/ │              │ Save to file only     │          │
│  │ Show in modal       │              │ data/exports/         │          │
│  │ Download as .txt    │              │ Download as .txt      │          │
│  │ Copy to clipboard   │              │ NEVER fabricates      │          │
│  └─────────────────────┘              └──────────────────────┘          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
careerpilot-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app + lifecycle
│   │   ├── config.py                # Settings from .env (Pydantic)
│   │   ├── database.py              # SQLite + WAL + FTS5
│   │   ├── models.py                # 9 SQLAlchemy ORM models
│   │   ├── schemas.py               # 20+ Pydantic request/response schemas
│   │   │
│   │   ├── routers/
│   │   │   ├── health.py            # GET /health (DB + Ollama + Gemini check)
│   │   │   ├── profile.py           # Profile CRUD + resume upload + search queries
│   │   │   ├── jobs.py              # Job list, search, scoring, dedup, stats
│   │   │   ├── applications.py      # Application CRUD + follow-ups
│   │   │   ├── company.py           # Company research via Gemini
│   │   │   ├── documents.py         # Cover letters + tailored resumes
│   │   │   └── scheduler.py         # Scheduler control + settings
│   │   │
│   │   ├── connectors/
│   │   │   ├── base.py              # Connector SDK (BaseConnector ABC)
│   │   │   ├── jsearch.py           # JSearch /search-v2 (OpenWeb Ninja)
│   │   │   └── adzuna.py            # Adzuna (India jobs)
│   │   │
│   │   ├── services/
│   │   │   ├── llm.py               # Smart Ollama ↔ Gemini routing
│   │   │   ├── embeddings.py        # nomic-embed-text + ChromaDB
│   │   │   ├── scoring.py           # Two-tier: quick_score + deep_score
│   │   │   ├── dedup.py             # Two-tier: heuristic + semantic
│   │   │   ├── resume_parser.py     # PDF/DOCX→text→Gemini parse→profile
│   │   │   ├── resume_tailor.py     # Tailor resume per job (Gemini Flash)
│   │   │   ├── cover_letter.py      # Generate cover letters (Gemini Flash)
│   │   │   ├── job_service.py       # Multi-source search orchestration
│   │   │   ├── scheduler.py         # APScheduler (4 cron jobs)
│   │   │   ├── telegram.py          # Telegram notifications
│   │   │   └── sheets.py            # Google Sheets sync (SKIPPED)
│   │   │
│   │   └── agents/
│   │       └── company.py           # Company research agent (Gemini)
│   │
│   ├── data/
│   │   ├── careerpilot.db           # SQLite database (live)
│   │   ├── resumes/                 # Uploaded resume files
│   │   ├── chroma/                  # Embedding vectors
│   │   ├── cover_letters/           # Generated cover letters
│   │   └── exports/                 # Exported data
│   │
│   ├── tests/
│   │   ├── test_backend.py          # 35 original tests
│   │   ├── test_scoring.py          # 28 scoring & dedup tests
│   │   ├── test_resume_parser.py    # 27 resume parser tests
│   │   └── test_documents.py        # 28 cover letter & resume tailor tests
│   │
│   ├── requirements.txt
│   ├── start.bat                    # Windows one-click startup
│   └── .env                         # API keys (user fills)
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout (Sidebar + Toaster)
│   │   │   ├── page.tsx             # Dashboard (stats, quick search, resume match)
│   │   │   ├── globals.css          # Dark theme, glass-morphism
│   │   │   ├── jobs/page.tsx        # Job search + results + scoring
│   │   │   ├── applications/page.tsx # Application tracking
│   │   │   ├── company/page.tsx     # Company intel
│   │   │   ├── profile/page.tsx     # Profile + Resume + Search Config
│   │   │   └── settings/page.tsx    # Scheduler + Telegram + search defaults
│   │   │
│   │   ├── components/
│   │   │   └── Sidebar.tsx          # Navigation (6 items)
│   │   │
│   │   └── lib/
│   │       └── api.ts               # API client (all backend endpoints)
│   │
│   ├── package.json                 # next@14.2.35 pinned
│   ├── next.config.js               # API proxy rewrite
│   └── tailwind.config.js
│
└── docker-compose.yml               # 3 services: backend, frontend, ollama
```

---

## ✅ Implementation Status

### ✅ Completed (Phase 1–3 + Resume Parser)

| Feature | Files | Status |
|---------|-------|--------|
| **FastAPI Backend** | `main.py`, `config.py`, `database.py` | ✅ Done |
| **9 ORM Models** | `models.py` (Profile, Company, Job, Application, CoverLetter, InterviewPrep, SearchHistory, ActivityLog, Settings) | ✅ Done |
| **Pydantic Schemas** | `schemas.py` (20+ request/response models) | ✅ Done |
| **7 Routers** | `routers/*.py` (health, profile, jobs, applications, company, documents, scheduler) | ✅ Done |
| **JSearch Connector** | `connectors/jsearch.py` (OpenWeb Ninja direct, `/search-v2`, enriched mode) | ✅ Done |
| **Adzuna Connector** | `connectors/adzuna.py` (India jobs) | ✅ Done |
| **Connector SDK** | `connectors/base.py` (BaseConnector ABC + NormalizedJob) | ✅ Done |
| **LLM Service** | `services/llm.py` (Ollama ↔ Gemini smart routing) | ✅ Done |
| **Embedding Service** | `services/embeddings.py` (nomic-embed-text + ChromaDB) | ✅ Done |
| **Two-Tier Scoring** | `services/scoring.py` (quick_score <1ms + deep_score LLM) | ✅ Done |
| **AEM Skill Taxonomy** | `scoring.py` (7 groups, 50+ variants, AEM-specific weights) | ✅ Done |
| **Two-Tier Dedup** | `services/dedup.py` (heuristic instant + semantic manual) | ✅ Done |
| **Resume Parser** | `services/resume_parser.py` (PDF/DOCX/TXT → Gemini parse → profile) | ✅ Done |
| **Resume Upload API** | `routers/profile.py` (POST /resume-upload, GET /resume-status, DELETE /resume) | ✅ Done |
| **Resume-Based Search** | `routers/jobs.py` (GET /search-by-resume) | ✅ Done |
| **Profile auto-update** | Resume → merge skills → update profile → re-score all jobs | ✅ Done |
| **Search Config on Profile** | Default chips + AI-generated chips unified on Profile page | ✅ Done |
| **Job Service** | `services/job_service.py` (multi-source search + auto-score + auto-dedup) | ✅ Done |
| **Company Research Agent** | `agents/company.py` (Gemini-based research, tips, salary intel) | ✅ Done |
| **Telegram Notifications** | `services/telegram.py` (job alerts, digests, reminders) | ✅ Done |
| **APScheduler** | `services/scheduler.py` (4 cron jobs: daily search, digest, followup, sheets sync) | ✅ Done |
| **Settings Router** | `routers/scheduler.py` (11 endpoints: scheduler, Telegram test, search defaults) | ✅ Done |
| **Frontend: 6 Pages** | Dashboard, Jobs, Applications, Company Intel, Profile, Settings | ✅ Done |
| **Dashboard** | Stats cards (clickable), quick search → /jobs, Resume Match button | ✅ Done |
| **Profile Page** | Resume upload + search config + personal info + career + skills + targets | ✅ Done |
| **Jobs Page** | Resume search banner, search bar + filters, chips from profile/resume, scoring modals | ✅ Done |
| **Dark Theme** | Glass-morphism, custom scrollbar, AEM skill highlighting | ✅ Done |
| **Collapsible Sidebar** | 6 nav items, system status indicator | ✅ Done |
| **Resume Tailoring** | `services/resume_tailor.py` (Gemini Flash — reorganize + emphasize, NEVER fabricate) | ✅ Done |
| **Cover Letter Generation** | `services/cover_letter.py` (Gemini Flash, 3 tones, profile+job context) | ✅ Done |
| **Documents Router** | `routers/documents.py` (7 endpoints: cover letter + tailored resume + downloads) | ✅ Done |
| **118 Tests** | 35 backend + 28 scoring/dedup + 27 resume parser + 28 documents | ✅ Done |
| **Docker Compose** | 3 services: backend, frontend, ollama | ✅ Done |

### ⏳ Pending / Not Started

| Feature | Phase | Notes |
|---------|-------|-------|
| **Interview Prep Agent** | Phase 3 | Deeper than company research — actual question prep |
| **Chrome Extension** | Phase 5 | One-click apply from LinkedIn/Indeed |
| **Google Sheets Sync** | Phase 4 | Temporarily SKIPPED per user request. gspread code exists in `sheets.py` |
| **Telegram Chat ID** | Setup | Bot token works, but user hasn't sent a message to bot to get chat_id |
| **End-to-end scheduler test** | Testing | Scheduler starts but hasn't been verified running a full cycle |
| **Salary intel from JSearch enriched** | Enhancement | JSearch returns `employer_reviews`, `benefits_extended` — not yet used |
| **Application follow-up automation** | Enhancement | Next follow-up dates tracked but not auto-triggered |

---

## 🚀 Setup & Run

### Prerequisites

- **Python 3.12** (not 3.14 — pydantic-core has no cp314 wheel)
- **Node.js 18+**
- **Ollama** (for local LLM)

### 1. Backend Setup

```bash
cd backend

# Create venv with Python 3.12
py -3.12 -m venv .venv        # Windows
python3.12 -m venv .venv      # Linux/Mac

# Activate
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

# Install deps
pip install -r requirements.txt

# Copy and fill .env
cp .env.example .env
# Fill in: JSEARCH_API_KEY, GOOGLE_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY, TELEGRAM_BOT_TOKEN
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Start Ollama

```bash
# Install Ollama: https://ollama.ai
ollama pull qwen3:8b
ollama pull nomic-embed-text
ollama serve
```

### 4. Run Everything

```bash
# Option A: Docker Compose
docker-compose up

# Option B: Manual (two terminals)
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Option C: Windows one-click
cd backend && start.bat
```

### 5. First Steps

1. Open http://localhost:3000
2. Go to **Profile** page → Upload your resume (PDF/DOCX)
3. AI parses your resume → skills, experience auto-populate
4. Search queries auto-generate from your resume
5. Click **🔍 Resume Search** to find matched jobs
6. Or search manually with the search bar + chips

---

## 📡 API Reference

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Check DB + Ollama + Gemini status |

### Profile & Resume
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/profile/` | Get your profile |
| PUT | `/api/profile/` | Update profile (partial) |
| POST | `/api/profile/resume-upload` | Upload PDF/DOCX/TXT → AI parses → profile updates |
| GET | `/api/profile/resume-status` | Check if resume is uploaded |
| GET | `/api/profile/resume-search-queries` | Get AI-generated search queries from resume |
| DELETE | `/api/profile/resume` | Remove resume |
| POST | `/api/profile/resume-text` | Manually set resume text |
| GET | `/api/profile/salary-calculator?ctc=25` | India CTC → in-hand calculator |

### Jobs
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/jobs/` | List jobs (paginated, filterable, sortable) |
| GET | `/api/jobs/search?query=...` | Search JSearch + Adzuna |
| GET | `/api/jobs/search-by-resume` | Resume-based multi-query search |
| POST | `/api/jobs/search` | Search (POST with body) |
| POST | `/api/jobs/score` | Deep score one job (LLM + embeddings) |
| POST | `/api/jobs/score/batch?mode=quick\|deep` | Score all unscored jobs |
| POST | `/api/jobs/dedup` | Run semantic deduplication |
| GET | `/api/jobs/stats/summary` | Dashboard stats |
| GET | `/api/jobs/{id}` | Get single job |
| GET | `/api/jobs/{id}/score-detail` | Detailed scoring breakdown |
| DELETE | `/api/jobs/{id}` | Soft-delete (deactivate) |

### Applications
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/applications/` | List applications |
| POST | `/api/applications/` | Create application |
| PUT | `/api/applications/{id}` | Update application |
| GET | `/api/applications/stats/summary` | Application pipeline stats |

### Company Research
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/company/research?company_name=...` | AI company research (Gemini) |
| GET | `/api/company/interview-tips?company_name=...` | Interview tips for company |
| GET | `/api/company/salary-intel?company_name=...` | Salary intelligence |
| GET | `/api/company/aem-hirers` | Known AEM hiring companies |

### Documents (Cover Letters + Tailored Resumes)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/documents/cover-letter` | Generate cover letter for a job (Gemini Flash, 3 tones) |
| GET | `/api/documents/cover-letter/job/{job_id}` | Get cover letters for a job |
| GET | `/api/documents/cover-letter/{id}` | Get specific cover letter |
| POST | `/api/documents/tailor-resume?job_id=...` | Generate tailored resume for a job (Gemini Flash) |
| GET | `/api/documents/tailored-resume/{job_id}` | Get tailored resume for a job |
| GET | `/api/documents/download/cover-letter/{id}` | Download cover letter as .txt |
| GET | `/api/documents/download/tailored-resume/{job_id}` | Download tailored resume as .txt |

### Scheduler & Settings
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/settings/` | Get all settings |
| PUT | `/api/settings/` | Update settings |
| POST | `/api/scheduler/start` | Start APScheduler |
| POST | `/api/scheduler/stop` | Stop APScheduler |
| POST | `/api/scheduler/trigger/daily-search` | Manual trigger: daily job search |
| POST | `/api/scheduler/trigger/daily-digest` | Manual trigger: Telegram digest |
| POST | `/api/telegram/test` | Test Telegram notification |

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# --- LLM ---
GOOGLE_API_KEY=             # Gemini Flash API key (free 500 RPD)

# --- Job Search APIs ---
JSEARCH_API_KEY=            # OpenWeb Ninja JSearch key
ADZUNA_APP_ID=              # Adzuna app ID (free)
ADZUNA_APP_KEY=             # Adzuna app key (free)

# --- Notifications ---
TELEGRAM_BOT_TOKEN=         # Telegram bot token
TELEGRAM_CHAT_ID=           # Your chat ID (send /start to bot first)

# --- Optional ---
LLM_PROVIDER=auto           # auto | ollama | gemini
```

### Scoring Weights (AEM-optimized)

```
skill_match      = 0.30   ← Highest — AEM skills are the key differentiator
experience_match = 0.25   ← 8+ years for senior/architect
salary_match     = 0.15   ← ₹20-35 LPA target
location_match   = 0.10   ← Hyderabad + Remote
company_quality  = 0.10   ← Known AEM employers get bonus
remote_preference= 0.10   ← Remote roles preferred
```

### Salary Targets

| Market | Range |
|--------|-------|
| India (8-12 yrs) | ₹18-30 LPA |
| India (12+ yrs) | ₹25-45 LPA |
| Remote US/EU | $80K-180K USD |

---

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_resume_parser.py -v    # 25 resume tests
pytest tests/test_scoring.py -v          # 28 scoring tests
pytest tests/test_backend.py -v          # 35 backend tests

# Total: 88 tests
```

---

## 💰 Cost: ₹0

| Service | Tier | Cost |
|---------|------|------|
| Ollama (qwen3:8b) | Local | ₹0 (unlimited) |
| Gemini Flash | Free tier | ₹0 (500 RPD) |
| JSearch (OpenWeb Ninja) | Free tier | ₹0 |
| Adzuna | Free tier | ₹0 |
| Telegram Bot | Free | ₹0 |
| SQLite | Local | ₹0 |
| Next.js + FastAPI | Open source | ₹0 |

---

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| Python 3.14 pydantic error | Install Python 3.12 alongside: `py -3.12 -m venv .venv` |
| Next.js Turbopack build error | Pin `next` to `14.2.35` in package.json |
| `useSearchParams` prerender error | Wrap in `<Suspense>` boundary |
| Ollama not responding | Start with: `ollama serve` |
| JSearch "Endpoint /search does not exist" | Use `/search-v2` (new endpoint) |
| TypeScript `catch (e: any)` error | Use `catch (err: unknown)` with instanceof check |
| FastAPI `/{job_id}` catches `/search` | Place ALL specific routes BEFORE parameterized routes |
| Resume parsing empty | Ensure PDF is text-based (not scanned image) |
| Telegram chat_id missing | Send any message to your bot, then hit getUpdates URL |
