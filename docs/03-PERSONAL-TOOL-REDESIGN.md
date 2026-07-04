# CareerPilot AI — Personal Tool Redesign

> **Context:** This is a PERSONAL productivity tool, NOT a SaaS product.
> One user. One machine. Zero customers. Maximum utility.

---

## What Changes When It's Personal

### ❌ REMOVE (Not Needed for Personal Use)

| Feature | Why Remove |
|---------|-----------|
| Supabase Auth (login/signup/OAuth) | You're the only user |
| JWT tokens, session management | No one to authenticate |
| RBAC (Role-Based Access Control) | One role: you |
| Multi-tenancy / user isolation | One tenant: you |
| Subscription billing / Stripe | No customers |
| Rate limiting per user | One user |
| DPDP / GDPR compliance | Personal data, not a business |
| Privacy notices in 22 languages | You're not serving anyone |
| DPO appointment, DPIA audits | Not a data fiduciary |
| Complex notification system (email/Slack/Push) | Telegram bot is enough |
| Upstash managed Redis | Local Redis or skip it |
| Resend email service | Not needed |
| Docker Hub container hosting | Run locally |
| GitHub Actions CI/CD | Run locally, push to GitHub for backup |
| Prometheus + Grafana monitoring | Overkill |
| OpenTelemetry logging | Overkill |
| Horizontal scaling architecture | One server |
| API versioning (/v1/, /v2/) | You're the only consumer |
| API rate limiting | Only you call it |
| CSRF protection | Only you use it |
| Complex error pages, onboarding flows | Not needed |
| Subscription tiers (Free/Pro/Premium) | No customers |
| India-adjusted PPP pricing | Not selling anything |
| Dashboard with "Top Companies" analytics | Keep it simple |
| Browser extension for Chrome Web Store | Personal use = unpacked extension is fine |

### ✅ KEEP (Core Value)

| Feature | Why Keep |
|---------|---------|
| Job search from multiple sources | Core value |
| AI matching / scoring | Core value |
| Resume tailoring | Core value |
| Cover letter generation | Core value |
| Application tracking | Core value — your "Excel sheet" |
| Interview prep questions | Core value |
| Company research | Useful |
| Deduplication | Essential — don't waste time on same job |
| Browser extension (autofill assist) | Useful, even for personal use |
| Telegram notifications | Perfect for personal — instant, free |
| Excel/CSV export | You asked for it |

### 🔄 SIMPLIFY

| Before (SaaS) | After (Personal) |
|----------------|-----------------|
| Supabase (cloud DB) | SQLite or local PostgreSQL |
| Supabase Auth | No auth — just open the app |
| Supabase Storage | Local filesystem |
| Upstash Redis | Local Redis OR just use Python dicts/celery with SQLite |
| Complex Next.js dashboard | Simple Next.js app (or even Streamlit!) |
| Celery + Redis for background jobs | Simple Python asyncio tasks |
| ChromaDB / Qdrant (vector DB) | SQLite with sqlite-vss OR ChromaDB local (just a folder) |
| LiteLLM proxy | Direct Ollama + Gemini API calls |
| Docker Compose with 8 services | Single `docker-compose.yml` with 3-4 services |
| 15+ connectors | 3-4 connectors that matter for India |

---

## Redesigned Architecture — Personal Tool

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR LAPTOP / PC                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Next.js Web App (:3000)                 │   │
│  │   (Simple dashboard — jobs, tracking, settings)   │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                                │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │           FastAPI Backend (:8000)                  │   │
│  │                                                    │   │
│  │  /jobs/search      → Search JSearch + Adzuna      │   │
│  │  /jobs/score       → Ollama/Gemini scoring        │   │
│  │  /resume/tailor    → Ollama/Gemini tailoring      │   │
│  │  /cover-letter     → Ollama/Gemini generation     │   │
│  │  /applications     → Track + export to Excel      │   │
│  │  /interview-prep   → Generate questions            │   │
│  │  /company/research → Serper + Gemini summary       │   │
│  └──────┬──────────┬──────────┬─────────────────────┘   │
│         │          │          │                           │
│  ┌──────▼──┐ ┌────▼────┐ ┌──▼──────────────────────┐   │
│  │ SQLite  │ │ Ollama  │ │ External APIs (free)     │   │
│  │ Database│ │ :11434  │ │                           │   │
│  │         │ │         │ │  JSearch (jobs)           │   │
│  │ Jobs    │ │ qwen3   │ │  Adzuna (jobs)            │   │
│  │ Apps    │ │ nomic   │ │  Gemini Flash (LLM)       │   │
│  │ Profile │ │         │ │  Serper (search)           │   │
│  │ Embeds  │ │         │ │  Telegram Bot (notifs)     │   │
│  └─────────┘ └─────────┘ └──────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │        Chrome Extension (unpacked)                 │   │
│  │  Detect job pages → Read JD → Send to backend     │   │
│  │  → Get tailored resume → Autofill assist          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Simplified Tech Stack

### Backend
| Component | SaaS Version | Personal Version | Why |
|-----------|-------------|-----------------|-----|
| **Language** | Python 3.12 | Python 3.12 | Same |
| **Framework** | FastAPI | FastAPI | Same — it's great |
| **Database** | PostgreSQL (Supabase) | **SQLite** | Zero setup, one file, fast enough |
| **ORM** | SQLAlchemy | SQLAlchemy | Same |
| **Migrations** | Alembic | Alembic | Same |
| **Vector search** | pgvector | **sqlite-vss** or **ChromaDB local** | No server needed |
| **Background jobs** | Celery + Redis | **Python asyncio + subprocess** | No Redis needed |
| **Caching** | Redis | **Python dict + SQLite** | Good enough |
| **Validation** | Pydantic | Pydantic | Same |

### Frontend
| Component | SaaS Version | Personal Version | Why |
|-----------|-------------|-----------------|-----|
| **Framework** | Next.js + React | **Next.js + React** (or Streamlit) | Next.js if you want polish; Streamlit for speed |
| **Styling** | Tailwind + shadcn/ui | **Tailwind + shadcn/ui** | Same — great DX |
| **State** | Zustand + React Query | **Zustand + React Query** | Same |
| **Charts** | Recharts | **Recharts** | Same |

### AI
| Component | SaaS Version | Personal Version | Why |
|-----------|-------------|-----------------|-----|
| **Primary LLM** | Ollama qwen3:8b/14b | **Ollama qwen3:8b/14b** | Same — free |
| **Fallback LLM** | Gemini Flash | **Gemini Flash** | Same — free |
| **Embeddings** | nomic-embed-text (Ollama) | **nomic-embed-text (Ollama)** | Same — free |
| **Embedding store** | pgvector | **ChromaDB local** (just a folder) | Zero setup |

### Data Sources
| Source | Why |
|--------|-----|
| **JSearch API** | LinkedIn + Indeed + Naukri + Glassdoor (200 free/month) |
| **Adzuna API** | Additional India jobs (free) |
| **Direct ATS APIs** | Greenhouse, Lever, Ashby (no auth needed) |
| **Serper.dev** | Company research (2,500 free queries) |

### Notifications
| Channel | Why |
|---------|-----|
| **Telegram Bot** | Perfect for personal — instant, free, works on phone |

### Storage
| Type | SaaS Version | Personal Version |
|------|-------------|-----------------|
| **Resumes** | Supabase Storage | **Local folder** (`./data/resumes/`) |
| **Cover letters** | Supabase Storage | **Local folder** (`./data/cover-letters/`) |
| **Exports** | N/A | **Local folder** (`./data/exports/`) |

---

## Simplified Project Structure

```
careerpilot-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # All settings from .env
│   │   ├── database.py          # SQLite connection
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── agents/
│   │   │   ├── search.py        # Job search agent
│   │   │   ├── ranking.py       # Job scoring agent
│   │   │   ├── resume.py        # Resume tailoring agent
│   │   │   ├── cover_letter.py  # Cover letter agent
│   │   │   ├── interview.py     # Interview prep agent
│   │   │   └── company.py       # Company research agent
│   │   ├── connectors/
│   │   │   ├── base.py          # Connector SDK interface
│   │   │   ├── jsearch.py       # JSearch API connector
│   │   │   ├── adzuna.py        # Adzuna connector
│   │   │   ├── greenhouse.py    # Greenhouse public API
│   │   │   ├── lever.py         # Lever public API
│   │   │   └── ashby.py         # Ashby public API
│   │   ├── services/
│   │   │   ├── llm.py           # Ollama + Gemini client
│   │   │   ├── embeddings.py    # nomic-embed via Ollama
│   │   │   ├── dedup.py         # Job deduplication
│   │   │   ├── parser.py        # Resume parsing
│   │   │   └── telegram.py      # Telegram notifications
│   │   └── routers/
│   │       ├── jobs.py          # /jobs/* endpoints
│   │       ├── applications.py  # /applications/* endpoints
│   │       ├── resume.py        # /resume/* endpoints
│   │       ├── interview.py     # /interview/* endpoints
│   │       └── settings.py      # /settings/* endpoints
│   ├── alembic/                  # Database migrations
│   ├── data/                     # Local storage
│   │   ├── careerpilot.db       # SQLite database
│   │   ├── chroma/              # ChromaDB vector store
│   │   ├── resumes/             # Resume files
│   │   ├── cover_letters/       # Generated cover letters
│   │   └── exports/             # Excel/CSV exports
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js app router
│   │   ├── components/          # UI components
│   │   ├── lib/                 # API client, utils
│   │   └── stores/              # Zustand stores
│   ├── package.json
│   └── Dockerfile
│
├── extension/
│   ├── manifest.json            # Chrome extension (MV3)
│   ├── content.js               # Read job pages
│   ├── background.js            # Service worker
│   ├── popup/                   # Extension popup UI
│   └── icons/
│
├── docker-compose.yml           # Just 3 services: backend, frontend, ollama
├── .env.example
└── README.md
```

**That's it. No `apps/`, `services/`, `packages/` monorepo complexity.**
**No 8 microservices. Just: backend + frontend + extension.**

---

## Simplified Database Schema (SQLite)

```sql
-- One user. No auth tables. Just data tables.

-- Your profile (single row)
CREATE TABLE profile (
    id INTEGER PRIMARY KEY DEFAULT 1,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    location TEXT,
    summary TEXT,
    skills TEXT,          -- JSON array: ["Python", "React", ...]
    experience_years REAL,
    current_role TEXT,
    expected_salary_min INTEGER,
    expected_salary_max INTEGER,
    preferred_locations TEXT,  -- JSON array
    remote_preference TEXT,    -- 'remote', 'hybrid', 'onsite', 'any'
    notice_period TEXT,        -- 'immediate', '15_days', '30_days', '60_days', '90_days'
    resume_text TEXT,          -- Parsed resume full text
    resume_file_path TEXT,     -- Path to latest resume file
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Companies
CREATE TABLE companies (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    website TEXT,
    industry TEXT,
    size TEXT,             -- 'startup', 'mid', 'large', 'enterprise'
    location TEXT,
    description TEXT,
    research_notes TEXT,   -- AI-generated research summary
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jobs (from all sources, deduplicated)
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,           -- 'jsearch', 'adzuna', 'greenhouse', 'lever', 'ashby'
    source_id TEXT,                 -- ID from the source
    source_url TEXT,                -- URL to original listing
    title TEXT NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    company_name TEXT NOT NULL,
    location TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT DEFAULT 'INR',
    job_type TEXT,                  -- 'full_time', 'part_time', 'contract', 'internship'
    is_remote BOOLEAN DEFAULT FALSE,
    description TEXT,
    requirements TEXT,              -- Extracted requirements
    skills_required TEXT,           -- JSON array of skills
    experience_required TEXT,
    posted_date TIMESTAMP,
    expiry_date TIMESTAMP,
    match_score REAL,              -- AI score 0-100
    match_reasons TEXT,            -- JSON: {strengths: [], weaknesses: []}
    embedding_id TEXT,             -- ChromaDB document ID
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, source_id)      -- Prevent duplicate from same source
);

-- Applications (your tracking sheet)
CREATE TABLE applications (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    status TEXT DEFAULT 'not_applied',  -- not_applied, saved, applying, applied,
                                        -- interview_scheduled, interview_done,
                                        -- offer, rejected, withdrawn, expired
    applied_at TIMESTAMP,
    resume_version TEXT,           -- Which resume version was sent
    cover_letter_path TEXT,        -- Path to cover letter file
    notes TEXT,                    -- Your personal notes
    rating INTEGER,                -- 1-5 interest level
    next_followup DATE,
    followup_count INTEGER DEFAULT 0,
    response_notes TEXT,           -- Notes from recruiter response
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id)                 -- Can't apply to same job twice
);

-- Cover Letters (generated)
CREATE TABLE cover_letters (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    content TEXT NOT NULL,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interview Prep
CREATE TABLE interview_prep (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    company_id INTEGER REFERENCES companies(id),
    questions TEXT NOT NULL,       -- JSON array of questions
    tips TEXT,                     -- JSON: preparation tips
    salary_negotiation_tips TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search History
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY,
    query TEXT NOT NULL,
    filters TEXT,                  -- JSON: location, salary, etc.
    results_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity Log
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY,
    action TEXT NOT NULL,          -- 'job_found', 'job_scored', 'application_sent', etc.
    entity_type TEXT,              -- 'job', 'application', 'resume'
    entity_id INTEGER,
    details TEXT,                  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Settings
CREATE TABLE settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    telegram_chat_id TEXT,
    telegram_bot_token TEXT,
    default_search_query TEXT,
    default_location TEXT,
    min_salary INTEGER,
    job_alerts_enabled BOOLEAN DEFAULT TRUE,
    alert_frequency TEXT DEFAULT 'daily',  -- 'realtime', 'daily', 'weekly'
    auto_score_jobs BOOLEAN DEFAULT TRUE,
    llm_provider TEXT DEFAULT 'ollama',    -- 'ollama' or 'gemini'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Simplified .env File

```bash
# ==============================================================
# CareerPilot AI — Personal Tool — Environment Variables
# ==============================================================

# --- LLM ---
OLLAMA_HOST=http://localhost:11434
GOOGLE_API_KEY=AIzaSyB...                    # Gemini Flash (free, 500 RPD)

# --- Job Search APIs ---
RAPIDAPI_KEY=ab1234...                        # JSearch (free, 200 req/mo)
JSEARCH_HOST=jsearch.p.rapidapi.com
ADZUNA_APP_ID=12345                          # Adzuna (free)
ADZUNA_APP_KEY=abc123...

# --- Company Research ---
SERPER_API_KEY=abc123...                      # Serper.dev (free, 2500 queries)

# --- Notifications ---
TELEGRAM_BOT_TOKEN=123456:ABC...             # Telegram bot (free)
TELEGRAM_CHAT_ID=987654321                   # Your chat ID

# --- App ---
APP_ENV=development
APP_URL=http://localhost:3000
API_URL=http://localhost:8000
SECRET_KEY=some-random-string-here
DATABASE_PATH=./data/careerpilot.db
```

**That's 8 variables. Down from 15+. No Supabase, no Redis, no Resend, no Docker Hub.**

---

## Simplified Accounts Needed

| # | Service | Why | Free Tier | Credit Card? |
|---|---------|-----|-----------|:---:|
| 1 | **JSearch (RapidAPI)** | Job search | 200 req/mo | ❌ |
| 2 | **Google Gemini** | LLM fallback | 500 RPD | ❌ |
| 3 | **Serper.dev** | Company research | 2,500 queries | ❌ |
| 4 | **Adzuna** | Extra India jobs | Free | ❌ |
| 5 | **Telegram** | Notifications | Free forever | ❌ |
| 6 | **Ollama** | Primary LLM | Free (local) | ❌ |

**6 accounts. That's it. No Supabase, no Upstash, no Resend, no Docker Hub, no GitHub Actions.**

Everything else (database, storage, caching) runs locally.

---

## What You Get — Daily Workflow

```
MORNING (Automatic)
│
├── 9:00 AM → Telegram notification:
│   "🆕 12 new jobs matching your profile found!
│    Top match: Senior Python Dev at Google — 94% match
│    Apply by: Jul 8"
│
├── 9:05 AM → Open dashboard
│   ├── See new jobs, sorted by match score
│   ├── Already-applied jobs shown with "✅ Applied" badge
│   └── Duplicate jobs from Naukri/LinkedIn/Indeed merged
│
├── 9:10 AM → Click on a job
│   ├── See match breakdown (skills 90%, location 80%, salary 70%)
│   ├── See strengths & weaknesses
│   └── See: "You're missing: Kubernetes, GCP"
│
├── 9:15 AM → Click "Tailor Resume & Apply"
│   ├── Auto-generates tailored resume (ATS-optimized)
│   ├── Auto-generates cover letter
│   ├── Opens apply link in browser
│   └── Extension helps autofill forms
│
├── 9:30 AM → Click "Mark as Applied"
│   ├── Status → Applied
│   ├── Follow-up reminder set for 5 days
│   └── Logged in application tracker
│
EVENING (Manual Review)
│
├── 7:00 PM → Check application tracker
│   ├── See all applications with status
│   ├── "Follow up with Amazon (applied 6 days ago)"
│   └── Export to Excel for offline review
│
├── 7:15 PM → Interview prep
│   ├── Select upcoming interview
│   ├── Get likely questions + suggested answers
│   ├── Company research summary
│   └── Salary negotiation tips (CTC → in-hand calculation)
│
└── 7:30 PM → Done for the day
```

---

## Docker Compose (Just 3 Services)

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data    # SQLite DB + resumes + exports
    environment:
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    # deploy:                          # Uncomment if you have NVIDIA GPU
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

volumes:
  ollama_data:
```

**3 containers. That's it. `docker compose up` and you're running.**

---

## Telegram Bot Setup (New — replaces all notifications)

### Step-by-step:

```
STEP 1: Open Telegram, search for @BotFather

STEP 2: Send: /newbot

STEP 3: BotFather asks for a name. Type: CareerPilot AI

STEP 4: BotFather asks for a username. Type: careerpilot_yourname_bot
  (Must end in "bot")

STEP 5: BotFather gives you:
  ┌──────────────────────────────────────────────────┐
  │ Done! Congratulations on your new bot...          │
  │ Use this token to access the HTTP API:            │
  │ 7123456789:AAH...                  ← COPY THIS   │
  │                                                    │
  │ Keep your token secure!                            │
  └──────────────────────────────────────────────────┘

STEP 6: Get your Chat ID:
  - Send any message to your new bot
  - Open: https://api.telegram.org/botYOUR_TOKEN/getUpdates
  - Look for "chat":{"id": 123456789}  ← COPY THIS

STEP 7: Test:
  curl "https://api.telegram.org/botYOUR_TOKEN/sendMessage?chat_id=YOUR_CHAT_ID&text=CareerPilot%20is%20alive!"
```

Save in `.env`:
```bash
TELEGRAM_BOT_TOKEN=7123456789:AAH...
TELEGRAM_CHAT_ID=123456789
```

---

## Roadmap — Simplified (5 Phases, Not 10)

| Phase | What | Time |
|-------|------|------|
| **Phase 1** | Backend + Job Search + Profile | 2 weeks |
| **Phase 2** | AI Matching + Scoring + Dedup | 1 week |
| **Phase 3** | Resume Tailoring + Cover Letters | 1 week |
| **Phase 4** | Dashboard + Application Tracker + Telegram | 1 week |
| **Phase 5** | Browser Extension + Interview Prep + Polish | 2 weeks |

**Total: ~7 weeks to a fully working personal tool.**

---

## Decision: Confirm Before We Start

1. **Database:** SQLite (simplest, one file, runs anywhere) ✅ or PostgreSQL (more powerful but needs setup)?
2. **Frontend:** Next.js (professional, more work) or Streamlit (Python-only, faster to build, less pretty)?
3. **Target:** India jobs only, or India + remote/global?
4. **Ollama hardware:** Do you have a GPU? Which one? (Determines which models you can run)
5. **Your primary role:** What's your job profile? (Software developer? Data analyst? This shapes the matching logic)

Confirm these and I'll begin Phase 1 immediately.
