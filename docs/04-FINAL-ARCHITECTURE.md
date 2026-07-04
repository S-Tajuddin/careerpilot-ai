# CareerPilot AI — Your Hardware, Database & Profile Analysis

> **Date:** 2026-07-04

---

## 1. Can Google Sheets or Local Excel Work as a Database?

### Honest Answer: Half Yes, Half No

Here's the problem — CareerPilot needs **two very different types of data work**:

| Type of Work | What It Needs | Google Sheets? | Local Excel? |
|-------------|---------------|:-:|:-:|
| **AI Brain** — Scoring, matching, deduplication, embeddings | Fast queries, vector search, relational joins, bulk reads | ❌ No | ❌ No |
| **Your Tracking** — Application status, notes, follow-ups | Simple rows, easy to view/edit, phone-accessible | ✅ Yes | ✅ Yes |

### Why Google/Excel CANNOT Be the Main Database

| Problem | Example |
|---------|---------|
| **No vector search** | "Find me jobs semantically similar to this AEM role" → Need embedding similarity → Sheets can't do this |
| **No relational queries** | "Show me all jobs at companies where I already applied" → Need SQL JOINs → Sheets can't do this efficiently |
| **API rate limits** | Google Sheets API: **60 requests/minute**. If scoring 50 jobs = 50 reads + 50 writes = 100 API calls = you're rate-limited |
| **No full-text search** | "Find jobs mentioning AEM Components or Sling Models" → Need FTS index → Sheets can't do this |
| **Slow at scale** | 1,000+ job rows → Google Sheets gets sluggish, API calls timeout |
| **No dedup logic** | "Is 'AEM Developer' at 'Accenture' the same job as 'Adobe Experience Manager Dev' at 'Accenture Solutions'?" → Need fuzzy matching + embeddings → Sheets can't do this |
| **No concurrent access** | Background job search running while you view dashboard → Both write to same sheet → Data conflicts |

### The Best Approach: SQLite + Google Sheets SYNC

```
┌─────────────────────────────────────────────────────────────┐
│                     SQLite Database                          │
│                    (The REAL database)                        │
│                                                              │
│  Jobs, Applications, Companies, Embeddings, Scores,         │
│  Profile, Search History — everything                        │
│                                                              │
│  Fast queries, vector search, full-text search,              │
│  deduplication, scoring — all happen here                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    Auto-sync (one-way)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Google Sheet                                │
│              (Your VIEW + EDIT layer)                         │
│                                                              │
│  Columns: Company | Role | Status | Match Score |            │
│           Applied Date | Follow-up | Notes | Link            │
│                                                              │
│  ✅ You can view on phone                                    │
│  ✅ You can edit status/notes from anywhere                  │
│  ✅ You can sort/filter visually                             │
│  ✅ You can share with someone                               │
│  ✅ Familiar spreadsheet interface                           │
│                                                              │
│  Edits sync BACK to SQLite automatically                     │
└─────────────────────────────────────────────────────────────┘
```

### How the Sync Works

```
SQLite → Google Sheets (every 5 minutes or on change)
  - New jobs found → appear as new rows in Sheets
  - Score changes → update in Sheets
  - Application status changes → update in Sheets

Google Sheets → SQLite (on edit)
  - You change status to "Applied" in Sheets → updates in SQLite
  - You add notes in Sheets → saves to SQLite
  - You change match rating → updates scoring model
```

### What This Means for You

| What You Do | Where |
|-------------|-------|
| View all your jobs | **Google Sheets** (or dashboard) |
| Check application status on phone | **Google Sheets** |
| Add notes about an interview | **Google Sheets** |
| Search for AEM jobs | **Dashboard** (uses SQLite + AI) |
| Score a job match | **Dashboard** (uses SQLite + Ollama) |
| Tailor resume for a job | **Dashboard** (uses Ollama + Gemini) |
| Export application history | **Google Sheets** (already there!) |

**TL;DR: SQLite is the brain. Google Sheets is your window. They stay in sync automatically.**

---

## 2. Your Hardware: Lenovo ThinkBook 14, i7, 16GB RAM, 512GB SSD

### What This Means for Ollama

| Factor | Your Setup | Impact |
|--------|-----------|--------|
| **CPU** | Intel i7 (12th-13th gen likely) | Good for CPU inference |
| **RAM** | 16 GB | Can run 8B models comfortably, 14B with swap (slow) |
| **GPU** | ❌ None (integrated Intel graphics) | No GPU acceleration — CPU only |
| **Storage** | 512 GB SSD | Plenty of space (models take ~5-15 GB each) |

### Model Recommendations for YOUR Hardware

| Task | Model | RAM Usage | Speed on Your CPU | Verdict |
|------|-------|-----------|-------------------|---------|
| **Job scoring** | `qwen3:8b` | ~6 GB | ~8-15 tok/s | ✅ **Use this** — fast enough |
| **Dedup check** | `qwen3:4b` | ~3 GB | ~15-25 tok/s | ✅ **Use this** — very fast |
| **Embeddings** | `nomic-embed-text` | ~1 GB | ~50+ embeds/s | ✅ **Use this** — fast even on CPU |
| **Resume tailoring** | `qwen3:8b` | ~6 GB | ~8-15 tok/s | ⚠️ Slow but works |
| **Cover letters** | `qwen3:8b` | ~6 GB | ~8-15 tok/s | ⚠️ Slow but works |
| **qwen3:14b** | — | ~10 GB | ~3-5 tok/s | ❌ Too slow, will swap |
| **qwen3:32b** | — | ~20 GB | N/A | ❌ Won't fit |

### The Real Speed Experience on Your Laptop

```
"What skills match this AEM job?" (qwen3:8b on CPU)
  → Takes ~15-20 seconds for a full response
  → Acceptable for scoring (runs in background)
  → Acceptable for resume tailoring (you wait 30 sec)

"What skills match this AEM job?" (Gemini Flash API)
  → Takes ~2-3 seconds
  → Much faster for interactive tasks
```

### Recommended Strategy for Your Hardware

```
┌──────────────────────────────────────────────────────────────┐
│                    BACKGROUND TASKS                           │
│              (User doesn't wait for these)                    │
│                                                               │
│  Use Ollama qwen3:8b (CPU, free, unlimited):                │
│  ✅ Scoring new jobs (happens automatically)                 │
│  ✅ Deduplication comparison                                  │
│  ✅ Keyword extraction from job descriptions                  │
│  ✅ Generating embeddings for semantic search                 │
│  ✅ Daily job search + scoring pipeline                       │
│                                                               │
│  Speed: 15-20 sec per job → Fine, runs in background         │
│  Cost: ₹0                                                     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                   INTERACTIVE TASKS                           │
│              (User is waiting for a response)                 │
│                                                               │
│  Use Gemini Flash API (cloud, free, fast):                   │
│  ✅ Resume tailoring (user clicks "Tailor Resume")           │
│  ✅ Cover letter generation (user clicks "Generate")         │
│  ✅ Interview prep questions (user clicks "Prepare")         │
│  ✅ Company research summary                                  │
│                                                               │
│  Speed: 2-3 seconds → User gets instant response             │
│  Cost: ₹0 (free tier, 500 requests/day)                     │
│                                                               │
│  Fallback: If Gemini is down → use Ollama (slower but works)│
└──────────────────────────────────────────────────────────────┘
```

### Disk Space Budget

| What | Size | Remaining |
|------|------|-----------|
| Total SSD | 512 GB | — |
| OS + Apps (estimated) | ~100 GB | 412 GB |
| Ollama models (qwen3:8b + nomic-embed) | ~5.5 GB | 406 GB |
| SQLite database (10K jobs) | ~50 MB | 406 GB |
| ChromaDB embeddings (10K jobs) | ~200 MB | 406 GB |
| Resumes + cover letters | ~100 MB | 406 GB |
| **CareerPilot total** | **~6 GB** | **406 GB free** |

**Plenty of space. No worries.**

---

## 3. Your Profile: AEM Developer / EDS Developer — Senior / Architect

### What This Means for Job Search Strategy

AEM/EDS is a **niche, high-value skill**. This is very different from searching for "Python developer" (thousands of jobs) vs "AEM Developer" (fewer but higher-paying jobs).

**AEM Job Market in India:**

| Metric | Value |
|--------|-------|
| Average AEM Developer salary (India) | ₹15-16 LPA |
| Senior AEM Developer (8+ yrs) | ₹18-25 LPA |
| AEM Architect (10+ yrs) | ₹25-40+ LPA |
| Top hiring companies | Accenture, Cognizant, Wipro, TCS, Capgemini, Adobe, IBM, Deloitte |
| EDS-specific companies | Adobe partners, digital agencies, enterprise consulting |

### Search Keywords We'll Configure for You

```
PRIMARY (exact match):
  "AEM developer"
  "Adobe Experience Manager developer"
  "EDS developer"
  "Edge Delivery Services developer"
  "AEM architect"

SECONDARY (related, often AEM jobs):
  "AEM Sites developer"
  "AEM Forms developer"
  "Adobe developer"
  "CQ5 developer"         ← Legacy name, still used
  "AEM as Cloud Service"
  "AEMaaCS developer"

BROADER (might contain AEM roles):
  "CMS developer"         ← Wider net
  "Java developer" + AEM  ← AEM is Java-based
  "Digital experience developer"
  "Content management developer"
  "Full stack developer" + Adobe
  "Senior Java developer" + CMS

REMOTE/GLOBAL:
  "AEM developer remote"
  "Adobe Experience Manager remote"
  "AEM developer work from home"
  "AEM contractor"         ← Contract roles, often remote
```

### Companies Known to Hire AEM in India

```python
AEM_HIRING_COMPANIES = {
    # Big 4 / Consulting
    "accenture", "deloitte", "pwc", "ey", "kpmg",
    # Indian IT
    "tcs", "infosys", "wipro", "hcl", "tech mahindra", "cognizant", "l&t",
    # Adobe Partners
    "cognizant", "ibm", "accenture", "wipro", "infosys",
    # Product / Direct
    "adobe", "sap", "oracle",
    # Digital Agencies
    "publicis sapient", "degdigital", "cognizant", "epam",
    # Enterprise
    "capgemini", "atos", "virtusa", "hexaware", "mindtree", "mphasis",
    # EDS specific
    "adobe", "aem", "eds",
}
```

### AEM-Specific Matching Logic

Your scoring algorithm should weigh these differently than a generic developer:

```python
# AEM-specific scoring weights
AEM_SCORING = {
    "skill_match": 0.30,       # AEM, EDS, Sling, OSGi, etc.
    "experience_match": 0.25,  # Senior/Architect level
    "salary_match": 0.15,      # ₹18-40 LPA range
    "location_match": 0.10,    # Hyderabad preferred, Remote best
    "company_quality": 0.10,   # Adobe partners > random companies
    "remote_preference": 0.10, # Remote > Hybrid > Onsite
}

# Must-have skills for AEM Senior/Architect
AEM_CORE_SKILLS = [
    "AEM", "Adobe Experience Manager", "AEM Sites", "AEM Forms",
    "AEM as Cloud Service", "AEMaaCS", "EDS", "Edge Delivery Services",
    "Sling", "OSGi", "JCR", "Jackrabbit Oak",
    "HTL", "Sightly",  # AEM templating
    "AEM Dispatcher", "AEM Assets",
    "Java", "Maven", "Apache Felix",
]

# Nice-to-have skills (boost score)
AEM_BONUS_SKILLS = [
    "AEM Forms", "AEM Assets", "AEM Screens",
    "Workfront", "Adobe Target", "Adobe Analytics",
    "CI/CD", "Cloud Manager", "DevOps",
    "React", "Angular",  # For EDS/frontend
    "Document-based Authoring",  # EDS-specific
    "Franklin",  # EDS former name
    "AIO",  # Adobe IO
]
```

### Salary Intelligence for AEM in India

```
AEM Developer Salary Ranges (India, 2026):

  2-4 years:  ₹4-10 LPA     (AEM Developer)
  4-6 years:  ₹8-15 LPA     (Senior AEM Developer)
  6-8 years:  ₹12-20 LPA    (Lead AEM Developer)
  8-12 years: ₹18-30 LPA    (AEM Architect)
  12+ years:  ₹25-45 LPA    (Principal Architect / Director)

  Remote for US/EU companies: $80K-180K USD (~₹65L-1.5Cr)
  (This is the big opportunity — remote AEM roles pay 3-5x Indian salary)

Your target (Senior/Architect):
  India: ₹20-35 LPA
  Remote: $100K-150K USD
```

---

## 4. Final Architecture — Personal AEM Career Tool

```
┌─────────────────────────────────────────────────────────────────┐
│                      YOUR THINKBOOK 14                           │
│                    i7 / 16GB / 512GB SSD                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Next.js Dashboard (:3000)                      │  │
│  │                                                             │  │
│  │  🔍 Search Jobs    📊 My Applications    📄 Resume          │  │
│  │  🎯 Match Score    📝 Cover Letters     🎤 Interview       │  │
│  │  🏢 Company Info   ⚙️ Settings          📤 Export          │  │
│  └───────────────────────────┬────────────────────────────────┘  │
│                              │                                    │
│  ┌───────────────────────────▼────────────────────────────────┐  │
│  │              FastAPI Backend (:8000)                         │  │
│  │                                                             │  │
│  │  Search: JSearch + Adzuna + Greenhouse + Lever              │  │
│  │  Scoring: Ollama qwen3:8b (background, free)                │  │
│  │  Tailoring: Gemini Flash (interactive, free)                │  │
│  │  Embeddings: nomic-embed-text (Ollama, free)               │  │
│  │  Dedup: Embedding similarity + fuzzy match                  │  │
│  │  Notifications: Telegram bot (free)                         │  │
│  │  Sync: Google Sheets (for phone access)                     │  │
│  └───────────────────────────┬────────────────────────────────┘  │
│                              │                                    │
│        ┌─────────────────────┼─────────────────────┐             │
│        │                     │                     │              │
│  ┌─────▼──────┐  ┌──────────▼──────────┐  ┌──────▼──────────┐  │
│  │   SQLite   │  │   Ollama (:11434)   │  │  Google Sheets  │  │
│  │  Database  │  │                     │  │   (synced)      │  │
│  │            │  │  qwen3:8b  (5.2 GB) │  │                 │  │
│  │ Jobs       │  │  nomic-embed (274MB)│  │  Application    │  │
│  │ Apps       │  │                     │  │  Tracker view   │  │
│  │ Profile    │  │  ~8-15 tok/s (CPU)  │  │  (phone ready)  │  │
│  │ Embeddings │  │  FREE, unlimited    │  │  FREE           │  │
│  └────────────┘  └─────────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │         Chrome Extension (unpacked, personal use)           │  │
│  │  Detect AEM job pages → Read JD → Autofill assist          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │         Telegram Bot                                        │  │
│  │  "🆕 3 new AEM jobs found! Top: AEM Architect at           │  │
│  │   Accenture — 91% match — ₹25-30 LPA"                      │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Accounts You Actually Need (6, All Free)

| # | Service | What For | Free Tier | Your Setup Time |
|---|---------|---------|-----------|:---:|
| 1 | **JSearch (RapidAPI)** | AEM job search from LinkedIn/Indeed/Naukri | 200 req/mo | 10 min |
| 2 | **Google Gemini** | Resume tailoring + cover letters | 500 RPD | 10 min |
| 3 | **Serper.dev** | Company research | 2,500 queries | 5 min |
| 4 | **Adzuna** | Extra India jobs | Free | 5 min |
| 5 | **Telegram Bot** | Job alerts on phone | Free forever | 5 min |
| 6 | **Ollama** | Job scoring + embeddings | Free (local) | 15 min |
| 7 | **Google Sheets** | Application tracker view | Free | 5 min |

**7 accounts. ₹0. ~55 minutes total setup.**

---

## 6. Your Daily Workflow (AEM-Focused)

```
6:30 AM (Automatic — background job runs)
│
├── Backend searches JSearch + Adzuna for AEM/EDS jobs
├── Scores each job against your profile
├── Deduplicates across sources  
├── Saves to SQLite + syncs to Google Sheets
│
7:00 AM → Telegram notification:
│   "🆕 5 new AEM jobs found!
│    1. AEM Architect @ Accenture, Hyd — 91% match — ₹25-30L
│    2. Sr. AEM Developer @ Adobe, Remote — 88% match — $120K
│    3. EDS Developer @ Cognizant, Hyd — 85% match — ₹18-22L
│    4. AEM Lead @ Capgemini, Pune — 78% match — ₹20-25L
│    5. Java + AEM @ Wipro, Hyd — 72% match — ₹15-20L"
│
9:00 AM → Open Dashboard
│   ├── See all new AEM jobs, sorted by match score
│   ├── Click "AEM Architect @ Accenture"
│   │   ├── Match: 91% — Skills 95%, Experience 90%, Location 85%
│   │   ├── Strengths: "Strong AEM + Java + OSGi match"
│   │   ├── Gaps: "AEM Forms experience mentioned (you don't list it)"
│   │   └── "Tailor Resume" button
│   │
│   ├── Click "Tailor Resume"
│   │   ├── Gemini generates tailored resume (2-3 seconds)
│   │   ├── Highlights AEM Components, Sling, EDS experience
│   │   ├── Adds missing keywords from JD
│   │   ├── ATS score: 87%
│   │   └── Download as PDF
│   │
│   ├── Click "Generate Cover Letter"
│   │   ├── Personalized for Accenture + AEM Architect role
│   │   ├── Mentions specific AEM projects from your resume
│   │   └── Download as PDF
│   │
│   ├── Click "Apply" → Opens application link
│   │   ├── Extension detects application form
│   │   ├── Offers to autofill name, email, phone, resume upload
│   │   └── You review + submit manually
│   │
│   └── Mark "Applied" → Status updates in SQLite + Google Sheets
│
7:00 PM → Check Google Sheets on phone
│   ├── All applications with status
│   ├── "Follow up with Adobe (applied 5 days ago)"
│   └── Edit notes: "Recruiter called, interview next Tuesday"
│
Next day → Interview prep
│   ├── Select "Adobe — AEM Architect interview"
│   ├── Get 15 likely questions:
│   │   "How would you design a multi-site AEM architecture?"
│   │   "Explain AEM as Cloud Service vs On-Premise trade-offs"
│   │   "How do you implement EDS with AEM?"
│   │   ...
│   ├── Get suggested answers based on YOUR experience
│   └── Salary negotiation tips: "Target ₹28-32 LPA, your leverage is..."
```

---

## CONFIRMED DECISIONS

| Decision | Your Choice | Confirmed |
|----------|------------|:---------:|
| Database | SQLite + Google Sheets sync | ✅ |
| Frontend | Next.js | ✅ |
| Job target | India + Remote/Global | ✅ |
| Hardware | i7 / 16GB / no GPU | ✅ |
| LLM strategy | Ollama 8B (background) + Gemini Flash (interactive) | ✅ |
| Your role | AEM Developer / EDS Developer — Senior / Architect | ✅ |
| Target salary | ₹20-35 LPA (India) / $100K-150K (Remote) | ✅ |
| Notifications | Telegram bot | ✅ |
| Export | Google Sheets (auto-synced) | ✅ |

---

*Ready to start Phase 1? Say "go" and I'll begin with the actual code.*
