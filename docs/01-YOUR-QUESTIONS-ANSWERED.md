# CareerPilot AI — Your 4 Questions Answered (Deep-Dive)

> **Date:** 2026-07-04
> **Status:** Pre-Phase 1 — Decision Gate Responses

---

## Question 1: How Can I Access LinkedIn & Indeed Without Scraping?

### Short Answer
You **cannot access them directly** without legal risk. But you **CAN access their data through aggregator APIs** that have already solved this problem legally. These aggregators scrape LinkedIn/Indeed on their own infrastructure and serve you clean JSON — **you never touch LinkedIn or Indeed yourself.**

---

### Method 1: JSearch API (RECOMMENDED — Best for India)

**What it is:** The most comprehensive job search API. It aggregates from **Google for Jobs**, which itself aggregates from LinkedIn, Indeed, Glassdoor, ZipRecruiter, Monster, and every public job site on the web.

**How it works:**
```
Google for Jobs indexes ALL job sites → JSearch queries Google for Jobs → You get clean JSON
```

**Key details:**
- **Coverage:** LinkedIn, Indeed, Glassdoor, ZipRecruiter, Dice, Monster + thousands of company career pages
- **India support:** Yes! Use `country=in` and `language=en` or `language=hi`
- **40+ data points per job:** title, description, location, salary, skills, experience, education, apply URL, employer, remote flag
- **Salary estimates:** Even when employers don't post salary
- **Publisher filter:** Add `"via linkedin"` or `"via indeed"` to query to filter by source

**Endpoints you'll use:**

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `/search` | Search jobs by keyword + location | `query=python developer in hyderabad&country=in` |
| `/search-v2` | Cursor-based pagination for bulk fetching | Same + `cursor=xxx` |
| `/job-details` | Get full details for a specific job | `job_id=bxHhpNOMPsWLyE9vAAAAAA==` |
| `/estimated-salary` | Salary estimates by title + location | `job_title=software engineer&location=hyderabad&country=in` |

**Pricing:**
| Plan | Requests | Cost |
|------|----------|------|
| Free tier | 500/month | $0 |
| Basic | 5,000/month | ~$15/month |
| Pro | 25,000/month | ~$75/month |
| Mega (separate API) | High volume | Custom |

**India-specific query examples:**
```
# Software jobs in Hyderabad
GET /search?query=software engineer in hyderabad&country=in&language=en&date_posted=week

# Remote jobs in India
GET /search?query=python developer in india&country=in&work_from_home=true

# Freshers jobs
GET /search?query=fresher software developer in bangalore&country=in

# Jobs from LinkedIn specifically
GET /search?query=backend developer in mumbai via linkedin&country=in

# Jobs from Indeed specifically  
GET /search?query=data analyst in delhi via indeed&country=in
```

**Why this is the best option for you:**
1. ✅ You never touch LinkedIn or Indeed directly — zero legal risk
2. ✅ Google for Jobs already indexes Naukri, Foundit, and Indian company career pages
3. ✅ India-specific filtering built in
4. ✅ Salary estimation (critical since most Indian job postings hide salary)
5. ✅ Available on RapidAPI — easy signup, no enterprise deal needed

---

### Method 2: LoopCV API (Best for Auto-Apply + Resume Parsing)

**What it is:** A full-featured job automation API that aggregates from 30+ sources AND can auto-apply on your behalf.

**Coverage for India:** LinkedIn, Indeed, Glassdoor + other global boards. India-specific coverage is weaker than JSearch.

**Key API features CareerPilot can use:**

| Feature | Endpoint | What it gives you |
|---------|----------|-------------------|
| Job Search | `POST /v1/jobs/search` | Aggregated listings from 30+ sources |
| Resume Parsing | `POST /v1/resume/parse` | Structured JSON from PDF/DOCX resume |
| Job Matching | `POST /v1/jobs/match` | ML-ranked job recommendations |
| Auto-Apply | `POST /v1/applications/submit` | Submit applications on behalf of user |
| Webhooks | Register URL | Real-time notifications for new matches |

**Pricing:**
| Plan | Cost | Apps/Month |
|------|------|------------|
| Basic (Free) | $0 | 10 applications |
| Standard | $19.99/mo | 100 applications |
| Premium | $59.99/mo | 300 applications |

**API pricing:** Free tier available for evaluation; contact for production pricing.

**Why use LoopCV alongside JSearch:**
- LoopCV gives you **resume parsing** (saves building from scratch)
- LoopCV gives you **auto-apply** capability (legally, with user consent)
- LoopCV gives you **job matching ML model** trained on application outcomes

---

### Method 3: Fresh LinkedIn Scraper API (RapidAPI) — USE WITH CAUTION

**What it is:** A third-party scraper API specifically for LinkedIn jobs.

**How it works:** Someone else runs the scrapers. You query their API.

**Endpoints:**
```
GET /api/v1/job/search?keyword=python&location=hyderabad
GET /api/v1/job/detail?job_id=4172815660
```

**⚠️ Risk Assessment:**
- This is NOT an official LinkedIn API
- The scraper operator takes the legal risk, not you
- BUT: LinkedIn could shut down the scraper at any time → your integration breaks
- RapidAPI terms require you to comply with source website TOS
- **Use as a FALLBACK, not primary source**

---

### Method 4: India-Specific Job Sources (MUST ADD)

Since you're targeting India, **these platforms matter more than LinkedIn/Indeed:**

| Platform | India Market Share | API Access | How to Integrate |
|----------|-------------------|------------|-----------------|
| **Naukri** | 62-70% | ❌ No public API | JSearch covers it via Google for Jobs |
| **Foundit (Monster India)** | Top 5 | ❌ No public API | JSearch covers it via Google for Jobs |
| **LinkedIn India** | 100M+ users | ❌ Direct scraping prohibited | JSearch (`via linkedin`) or LoopCV |
| **Indeed India** | Major aggregator | ❌ Publisher API deprecated | JSearch (`via indeed`) |
| **Internshala** | Fresher focus | ⚠️ Unofficial API / scraping | Scrape public pages (legal) |
| **Freshersworld** | Fresher focus | ❌ No API | Scrape public pages (legal) |
| **Apna.co** | Blue-collar/Tier 2-3 | ❌ No public API | Contact for partnership |
| **CutShort** | Tech/startup | ⚠️ Partial API | Contact for partnership |
| **Instahyre** | Mid-senior tech | ❌ Invite-only | Not feasible |
| **iimjobs** | MBA/leadership | ❌ No API | Scrape public pages |
| **National Career Service** | Government jobs | ✅ Open data | API available on data.gov.in |

### Recommended Data Source Stack for India

```
┌──────────────────────────────────────────────────────────────────┐
│                    PRIMARY: JSearch API                          │
│  (Covers LinkedIn, Indeed, Glassdoor, Naukri, Foundit via      │
│   Google for Jobs aggregation. India-aware. Salary estimates.)  │
│                                                                  │
│  query=software engineer in hyderabad&country=in                │
│  query=python developer in bangalore via linkedin&country=in    │
│  query=fresher jobs in mumbai via indeed&country=in             │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│                 SECONDARY: Direct ATS APIs                       │
│  (Greenhouse, Lever, Ashby, Workable — for MNC jobs in India)  │
│                                                                  │
│  Google India → greenhouse board → grab all Indian jobs         │
│  Microsoft India → greenhouse board → grab all Indian jobs      │
│  Amazon India → lever postings → grab all Indian jobs           │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│               TERTIARY: India-Specific Scraping                  │
│  (Internshala, Freshersworld — public pages, legal to scrape)   │
│                                                                  │
│  Freshersworld: public job listings → parse HTML                │
│  Internshala: public internship listings → parse HTML           │
│  National Career Service: open data API (data.gov.in)           │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│                ENHANCEMENT: LoopCV API                           │
│  (Resume parsing, job matching ML, auto-apply capability)       │
│                                                                  │
│  POST /v1/resume/parse → structured profile                     │
│  POST /v1/jobs/match → ML-ranked recommendations               │
│  POST /v1/applications/submit → auto-apply with consent        │
└──────────────────────────────────────────────────────────────────┘
```

### The Bottom Line on LinkedIn & Indeed Access

| Approach | Legal Risk | Cost | India Coverage | Reliability |
|----------|-----------|------|----------------|-------------|
| Direct scraping | 🔴 HIGH | Low (proxies) | Good | Unreliable (blocks) |
| JSearch API | 🟢 ZERO | $0-75/mo | Good | High (Google-backed) |
| LoopCV API | 🟢 ZERO | $0-60/mo | Medium | Medium |
| Fresh LinkedIn Scraper | 🟡 MEDIUM | $10-50/mo | Good | Low (can be shut down) |
| LinkedIn Official API | 🟢 ZERO | Enterprise only | Good | High (not available to you) |

**✅ My recommendation: JSearch as primary + LoopCV as secondary = covers 90%+ of Indian job market at zero legal risk.**

---

## Question 2: What If I Use Ollama LLM + Free Models?

### Short Answer
This is an **excellent idea for cost savings** but requires understanding the trade-offs. With the right model selection, you can run CareerPilot AI at **near-zero marginal LLM cost**. However, quality will be noticeably lower than GPT-4o/Claude for complex tasks like resume tailoring.

---

### The Recommended Ollama Model Stack

Not all models are equal for CareerPilot's use cases. Here's what to use for each agent:

#### Tier 1: Lightweight Models (Fits 8GB VRAM / 16GB RAM)

| Agent | Model | Size | VRAM | Quality | Speed |
|-------|-------|------|------|---------|-------|
| **Search Agent** (dedup, normalize) | `qwen3:8b` | 5.2GB | 6GB | Good | 50-80 tok/s |
| **Ranking Agent** (score computation) | `qwen3:8b` | 5.2GB | 6GB | Good | 50-80 tok/s |
| **Analytics Agent** (trends, stats) | `qwen3:8b` | 5.2GB | 6GB | Good | 50-80 tok/s |
| **Recruiter Agent** (outreach messages) | `gemma3:12b` | 7.3GB | 8GB | Very Good | 24-40 tok/s |

#### Tier 2: Medium Models (Fits 12-16GB VRAM / 32GB RAM)

| Agent | Model | Size | VRAM | Quality | Speed |
|-------|-------|------|------|---------|-------|
| **Resume Agent** (tailoring) | `qwen3:14b` | 9GB | 10GB | Very Good | 18-30 tok/s |
| **Cover Letter Agent** | `qwen3:14b` | 9GB | 10GB | Very Good | 18-30 tok/s |
| **Company Research Agent** | `mistral-small:24b` | 14GB | 16GB | Excellent | 36-55 tok/s |
| **Interview Agent** (questions) | `mistral-small:24b` | 14GB | 16GB | Excellent | 36-55 tok/s |

#### Tier 3: Heavy Models (Needs 24GB+ VRAM / 64GB RAM)

| Agent | Model | Size | VRAM | Quality | Speed |
|-------|-------|------|------|---------|-------|
| **Resume Agent** (complex tailoring) | `qwen3:32b` | 18GB | 20GB | Excellent | 10-20 tok/s |
| **All agents** (premium tier) | `qwen3:32b` | 18GB | 20GB | Near-GPT4 | 10-20 tok/s |

### Why These Specific Models?

**Qwen3 (Alibaba)** — Best for CareerPilot because:
- ✅ **Excellent instruction following** — critical for structured outputs (JSON scores, formatted resumes)
- ✅ **Strong multilingual support** — important for Hindi + English India market
- ✅ **Good at structured text generation** — resumes, cover letters, interview questions
- ✅ **Multiple sizes** — 8B, 14B, 32B let you scale quality vs speed

**Gemma 3 (Google)** — Good alternative because:
- ✅ **Long context window** (up to 128K tokens) — useful for long job descriptions + resume combinations
- ✅ **Strong reasoning** at smaller sizes
- ⚠️ Less multilingual than Qwen

**Mistral Small 3.1 (24B)** — Best medium model because:
- ✅ **Best quality at 24B size** — punches above its weight
- ✅ **Strong at reasoning and code** — good for technical job matching
- ⚠️ Requires 16GB VRAM

### Hardware Requirements & Cost

| Setup | What It Runs | Hardware | Cost (India) |
|-------|-------------|----------|-------------|
| **Budget** | All 8B models | 16GB RAM, no GPU | ₹0 (use existing PC) |
| **Standard** | Mix of 8B + 14B | RTX 4060 (8GB) + 16GB RAM | ~₹25,000 (used GPU) |
| **Recommended** | Mix of 8B + 24B | RTX 4060 Ti (16GB) + 32GB RAM | ~₹40,000 |
| **Premium** | All 32B | RTX 4090 (24GB) + 64GB RAM | ~₹1,50,000 |

### The Hybrid Strategy (BEST APPROACH)

Don't go 100% Ollama. Use a **hybrid approach:**

```
┌─────────────────────────────────────────────────────────────┐
│                    OLLAMA (Self-Hosted)                      │
│                                                              │
│  Use for HIGH-VOLUME, LOW-STAKES tasks:                     │
│  ✅ Job scoring (100+ per user per day)                     │
│  ✅ Job deduplication comparison                             │
│  ✅ Basic job summarization                                  │
│  ✅ Keyword extraction from job descriptions                 │
│  ✅ Skills gap analysis                                      │
│  ✅ Search query generation                                  │
│  ✅ Analytics & reporting                                    │
│  ✅ Notification content generation                          │
│                                                              │
│  Cost: ₹0 marginal (just electricity)                       │
│  Models: qwen3:8b for scoring, qwen3:14b for summaries     │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│              CLOUD LLM (Gemini Flash / GPT-4o-mini)         │
│                                                              │
│  Use for LOW-VOLUME, HIGH-STAKES tasks:                     │
│  ✅ Resume tailoring (10 per month per user)                │
│  ✅ Cover letter generation (10 per month per user)         │
│  ✅ Interview question preparation (5 per month per user)   │
│  ✅ Company research deep analysis                           │
│                                                              │
│  Cost: Gemini Flash = $0.50/$3 per 1M tokens               │
│        = ~₹0.50 per resume tailoring                        │
│        GPT-4o-mini = $0.15/$0.60 per 1M tokens             │
│        = ~₹0.15 per resume tailoring                        │
└─────────────────────────────────────────────────────────────┘
```

### Cost Comparison: Ollama vs Cloud vs Hybrid

| Setup | Monthly Cost (1,000 users) | Quality | Latency |
|-------|---------------------------|---------|---------|
| **100% Cloud (GPT-4o)** | ~₹1,45,000 ($1,730) | Excellent | 1-3 sec |
| **100% Cloud (Gemini Flash)** | ~₹7,500 ($90) | Very Good | 1-2 sec |
| **100% Ollama (8B models)** | ~₹2,000 (electricity) | Fair | 3-10 sec |
| **Hybrid (Ollama 8B + Gemini Flash)** | ~₹3,000 ($36) | Very Good | 1-10 sec |
| **Hybrid (Ollama 14B + GPT-4o-mini)** | ~₹4,500 ($54) | Very Good-Excellent | 2-8 sec |

### ✅ My Recommendation: Hybrid with Ollama 14B + Gemini Flash

- **90% of LLM calls** → Ollama (qwen3:8b or 14b) → FREE
- **10% of LLM calls** (resume tailoring, cover letters) → Gemini Flash → ₹0.50 per call
- **Total cost at 1,000 users:** ~₹3,000/month
- **Total cost at 10,000 users:** ~₹30,000/month
- **This is 95% cheaper than 100% GPT-4o**

### Ollama-Specific Implementation Details

```yaml
# docker-compose.yml addition
services:
  ollama:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

  # Pre-pull models on startup
  ollama-setup:
    image: ollama/ollama:latest
    depends_on:
      - ollama
    entrypoint: >
      sh -c "
        sleep 5 &&
        ollama pull qwen3:8b &&
        ollama pull qwen3:14b &&
        ollama pull nomic-embed-text
      "
```

```python
# LiteLLM config for hybrid routing
model_list:
  # Ollama models (free, self-hosted)
  - model_name: "career-scoring"
    litellm_params:
      model: "ollama/qwen3:8b"
      api_base: "http://ollama:11434"
  
  - model_name: "career-analysis"
    litellm_params:
      model: "ollama/qwen3:14b"
      api_base: "http://ollama:11434"
  
  # Cloud fallback (paid, high quality)
  - model_name: "career-premium"
    litellm_params:
      model: "gemini/gemini-2.5-flash"
      api_key: "os.environ/GEMINI_API_KEY"
  
  - model_name: "career-resume"
    litellm_params:
      model: "gemini/gemini-2.5-flash"
      api_key: "os.environ/GEMINI_API_KEY"
```

### ⚠️ Ollama Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Quality gap vs GPT-4o** | Use Ollama for scoring (binary: good/bad match), cloud for creative tasks |
| **Latency on CPU-only** | Require GPU for production; use cloud fallback for CPU users |
| **Model crashes/OOM** | Health checks + automatic cloud fallback via LiteLLM |
| **Hallucination in resumes** | Same strict prompting + human review regardless of model |
| **Context window limits** | Qwen3 8B = 32K tokens; use chunking for long JDs |
| **Server maintenance** | Docker auto-restart + monitoring + cloud fallback |

---

## Question 3: Excel Sheet for Deduplication & Application Tracking

### Short Answer
An **Excel sheet works for a personal tool** but is **not viable for a SaaS platform** serving multiple users. However, the *concept* is excellent — we need to build this as a **database-backed Application Tracker** that serves the same purpose but is scalable, real-time, and multi-user.

---

### What You're Really Asking For

You want two things:
1. **Deduplication:** "Have I seen this job before?" → Don't show it again
2. **Application Tracking:** "Have I already applied to this?" → Don't apply again; track status

These are related but distinct problems. Let me address both.

### Problem 1: Job Deduplication (Preventing Duplicate Job Listings)

**The challenge:** The same job appears on multiple platforms.

Example:
```
Source 1 (LinkedIn): "Senior Python Developer at Amazon, Hyderabad"
Source 2 (Indeed):   "Sr. Python Developer - Amazon India, Hyderabad"
Source 3 (Naukri):   "Senior Python Developer - Amazon Web Services, HYD"
Source 4 (Greenhouse): "Software Development Engineer II, Python - Amazon, Hyderabad"
```

These are ALL the same job. Your system needs to detect this.

**Why Excel doesn't work for this:**
- You'd need to manually compare 4 rows across 4 sheets
- No fuzzy matching (can't detect "Sr." = "Senior")
- No embedding similarity (can't detect semantic equivalence)
- Doesn't scale beyond ~500 jobs
- No real-time sync between users

**What we'll build instead:**

```sql
-- Deduplication happens in the database
-- When a new job is found:

Step 1: Exact match check
  → Same company + same title + same location + same date range = duplicate

Step 2: Fuzzy match check  
  → Company name similarity > 0.9 (fuzzy string matching)
  → Title similarity > 0.85
  → Location overlap
  → Same job posting date (±3 days)

Step 3: Embedding similarity check
  → Generate embedding of job description
  → Compare against existing embeddings
  → Similarity > 0.92 = likely duplicate

Step 4: LLM verification (for edge cases only)
  → Ask Ollama: "Are these two job listings for the same position?"
  → Only called when Steps 1-3 are inconclusive

Result: Merge into one canonical job record with multiple sources
```

**Database schema for deduplication:**

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    canonical_job_id UUID REFERENCES canonical_jobs(id),  -- Links duplicates together
    source VARCHAR(50),           -- 'linkedin', 'indeed', 'naukri', 'greenhouse'
    source_job_id VARCHAR(255),   -- Original ID from the source
    source_url TEXT,              -- URL to the original listing
    title VARCHAR(500),
    company VARCHAR(500),
    location VARCHAR(500),
    description TEXT,
    salary_min DECIMAL,
    salary_max DECIMAL,
    salary_currency VARCHAR(3),
    job_type VARCHAR(50),         -- full-time, part-time, contract, internship
    remote BOOLEAN,
    posted_date TIMESTAMP,
    embedding VECTOR(768),        -- pgvector for similarity search
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE canonical_jobs (
    id UUID PRIMARY KEY,
    canonical_title VARCHAR(500),
    canonical_company VARCHAR(500),
    canonical_location VARCHAR(500),
    unified_description TEXT,     -- Best description from all sources
    all_sources JSONB,            -- List of all sources that have this job
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP,       -- Updated when any source still shows this job
    is_active BOOLEAN DEFAULT TRUE
);
```

### Problem 2: Application Tracking (The "Excel" Concept, But Better)

**Your concept is right.** Here's how we build it properly:

```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    job_id UUID REFERENCES jobs(id),
    status VARCHAR(50) DEFAULT 'not_applied',
    -- Statuses: not_applied, saved, applying, applied, interview_scheduled,
    --           interview_completed, offer_received, offer_accepted,
    --           offer_rejected, rejected, withdrawn, expired
    
    -- When was it applied?
    applied_at TIMESTAMP,
    
    -- What was sent?
    resume_version_id UUID REFERENCES resumes(id),
    cover_letter_id UUID REFERENCES cover_letters(id),
    
    -- Response tracking
    last_response_at TIMESTAMP,
    last_response_type VARCHAR(50),  -- 'auto_reply', 'recruiter_email', 'interview_invite', 'rejection'
    
    -- User notes
    notes TEXT,
    rating SMALLINT,  -- 1-5, how interested is the user?
    
    -- Follow-up
    next_followup_date TIMESTAMP,
    followup_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, job_id)  -- Can't apply to the same job twice!
);
```

**The "Excel-like" view in the dashboard:**

```
┌──────────────────────────────────────────────────────────────────────┐
│                    APPLICATION TRACKER                                │
├──────┬──────────────┬────────────┬───────────┬──────────┬───────────┤
│ Status│ Company      │ Role       │ Applied   │ Response │ Follow-up │
├──────┼──────────────┼────────────┼───────────┼──────────┼───────────┤
│ 🟢    │ Google       │ SDE III    │ Jul 1     │ Interview│ Jul 8     │
│ 🟡    │ Amazon       │ SDE II     │ Jun 28    │ Pending  │ Jul 5 ⚠️  │
│ 🔵    │ Microsoft    │ Sr. Eng    │ Jun 25    │ OA sent  │ Jul 3     │
│ 🔴    │ Flipkart     │ SDE II     │ Jun 20    │ Rejected │ -         │
│ ⚪    │ Swiggy       │ Tech Lead  │ -         │ -        │ -         │
│ 🟢    │ Atlassian    │ SDE III    │ Jun 15    │ Offer!   │ -         │
└──────┴──────────────┴────────────┴───────────┴──────────┴───────────┘

Filters: [All] [Saved] [Applied] [Interview] [Offer] [Rejected]
Sort by: [Date Applied] [Match Score] [Company] [Last Response]
Export: [CSV] [Excel] [PDF]
```

### How Deduplication + Application Tracking Work Together

```
NEW JOB FOUND (from JSearch)
    │
    ▼
Is this a duplicate of an existing job?
    │
    ├── YES → Link to canonical_job. Check: Has user already applied?
    │          │
    │          ├── Already applied → DON'T show in search results
    │          └── Not applied → Show with "Also on: LinkedIn, Indeed, Naukri"
    │
    └── NO → Create new canonical_job. Show in search results.
               │
               ▼
        User clicks "Apply"
               │
               ▼
        Create application record (status: applied)
               │
               ▼
        Next time this job appears from ANY source → 
        System knows: "You already applied to this" ✅
```

### Export to Excel (Yes, We'll Support This!)

```python
# API endpoint for Excel export
@router.get("/v1/applications/export")
async def export_applications(
    format: Literal["xlsx", "csv", "pdf"],
    status: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Export application history to Excel/CSV/PDF.
    
    This gives users the "Excel sheet" they want, 
    but auto-populated from the database.
    """
    ...
```

**Excel export columns:**
| Column | Description |
|--------|-------------|
| Company | Employer name |
| Role | Job title |
| Status | Current application status |
| Match Score | AI match score (0-100) |
| Applied Date | When you applied |
| Source | Where you found it (LinkedIn/Indeed/Naukri) |
| Salary Range | If available |
| Location | Job location |
| Remote | Yes/No |
| Last Response | Date + type of last response |
| Days Since Applied | Auto-calculated |
| Follow-up Due | When to follow up next |
| Notes | Your personal notes |
| Resume Version | Which resume you sent |
| Cover Letter | Which cover letter you used |

### ✅ My Recommendation

| Feature | Approach |
|---------|----------|
| Deduplication | 3-tier: exact match → fuzzy match → embedding similarity → LLM verify |
| Application tracking | PostgreSQL database with status workflow |
| "Already applied" check | Database constraint + UI badge on search results |
| Excel export | Supported via API (xlsx, csv, pdf) |
| Follow-up reminders | Auto-calculated based on days since applied |

---

## Question 4: India Priority — Rules, Regulations & Market Fit

### Short Answer
India-first is a smart strategy. The market is massive (100M+ job seekers), underserved by AI tools, and has specific compliance requirements under the new DPDP Act. Here's everything you need to know.

---

### 4.1 Legal & Compliance: India's DPDP Act 2023

**The law is now active.** The DPDP Rules were notified on November 13, 2025. Full compliance required by mid-May 2027 (18-month phase-in).

**What DPDP means for CareerPilot:**

| Obligation | What CareerPilot Must Do | Priority |
|-----------|-------------------------|----------|
| **Consent** | Clear, plain-language consent before collecting personal data (resume, profile, preferences) | 🔴 Critical |
| **Multilingual notices** | Privacy notices in English + at least one regional language (22 scheduled languages) | 🟡 Important |
| **Data Principal Rights** | Users can request access, correction, or deletion of their data at any time | 🔴 Critical |
| **Data breach reporting** | Must notify Data Protection Board + affected users within **72 hours** | 🔴 Critical |
| **Data minimization** | Only collect data actually needed; don't hoard | 🟡 Important |
| **Purpose limitation** | Only use data for stated purposes (job matching, resume tailoring) | 🟡 Important |
| **Data retention** | Mandatory 1-year retention; then delete upon user request | 🔴 Critical |
| **Cross-border transfer** | Blacklist-based (permissive by default); don't transfer to prohibited countries | 🟡 Important |
| **Grievance redressal** | Must respond to user complaints within 90 days | 🟡 Important |
| **Significant Data Fiduciary** | If classified as SDF, must appoint DPO, do annual DPIAs, independent audits | 🟡 Monitor |

**Are you a "Significant Data Fiduciary" (SDF)?**

Probably NOT initially. SDF classification depends on:
- Volume of data processed
- Sensitivity of data
- Risk to data principals
- Impact on national security or electoral democracy

Once you hit significant scale (likely 1M+ users or processing children's data), you may be classified as SDF and need:
- India-based Data Protection Officer (DPO)
- Annual Data Protection Impact Assessments (DPIAs)
- Independent data audits
- Algorithmic due diligence (AI fairness checks)

**Key differences from GDPR that benefit you:**
- ✅ No separate "sensitive data" category — simpler compliance
- ✅ Blacklist approach to cross-border transfers — data can flow OUT of India by default (only restricted countries blocked)
- ✅ "Legitimate use" exception covers recruitment data processing — no explicit consent needed for basic HR activities
- ✅ Publicly available data exemption — job postings on public websites have reduced DPDP obligations

**What CareerPilot MUST implement for India compliance:**

```python
# Core compliance features to build from Day 1

1. CONSENT MANAGEMENT
   - Onboarding consent flow (simple language, not legalese)
   - Granular consent: "Can we use your resume for matching?" / "Can we store your data?"
   - One-click consent withdrawal
   - Consent history log (auditable)

2. DATA PRINCIPAL RIGHTS
   - GET /v1/me/data — Export all user data
   - DELETE /v1/me/data — Delete all user data (right to erasure)
   - PATCH /v1/me/data — Correct inaccurate data
   - POST /v1/me/grievance — File a complaint

3. DATA BREACH PROTOCOL
   - Automated breach detection
   - 72-hour notification to DPB + affected users
   - Incident logging and documentation

4. DATA RETENTION
   - Auto-delete job postings > 30 days old
   - Auto-delete inactive accounts > 12 months (with 30-day warning)
   - Resume data deleted within 7 days of account deletion

5. LOCALIZATION
   - Privacy notices in Hindi + English minimum
   - Option for Telugu, Tamil, Kannada, Bengali, Marathi
   - All consent forms bilingual

6. AUDIT TRAIL
   - Log all access to personal data
   - Timestamp + user ID + purpose for every data access
   - Quarterly compliance reports
```

### 4.2 India-Specific Job Market Features

**Unique to India that CareerPilot MUST support:**

| Feature | Why | Implementation |
|---------|-----|---------------|
| **CTC vs In-hand salary** | Indian jobs post CTC (Cost to Company) which includes PF, gratuity, variable pay. Users need in-hand estimate | CTC → In-hand calculator (deduct PF 12%, gratuity, variable, tax) |
| **Notice period matching** | Most Indian jobs require 60-90 day notice. Employers filter by notice period | Add notice_period field to profile; filter jobs by "immediate" / "15 days" / "30 days" / "60 days" / "90 days" |
| **Fresher vs Experience** | Indian market heavily segments by "fresher" (< 1 year) vs experienced | Clear fresher flag on profile; special matching for campus/fresher jobs |
| **Tier 1/2/3 city classification** | Salary bands differ drastically between metro and non-metro | Auto-classify locations; adjust salary expectations |
| **Government job tracking** | Huge demand for sarkari naukri (government jobs) | Integrate National Career Service API; add exam date tracking |
| **Walk-in interview alerts** | Common in India, especially for freshers | Parse "walk-in" from job descriptions; send immediate alerts |
| **Referral-based hiring** | 40-50% of Indian tech hiring happens through referrals | "Do you know anyone at this company?" feature |
| **Resume format preferences** | Indian employers expect photo, father's name, DOB on resume (unlike US) | Region-aware resume templates |
| **Hindi + English bilingual JDs** | Many jobs, especially in Tier 2/3, post in Hindi or Hinglish | Multilingual JD parsing and matching |
| **Internshala/college placement** | Campus placement is a massive channel | Internshala integration; campus placement calendar |

### 4.3 India-Specific Connectors to Add

| Connector | Priority | Method |
|-----------|----------|--------|
| **Naukri.com** | 🔴 Critical | Via JSearch (Google for Jobs indexes Naukri) |
| **Foundit (Monster India)** | 🟡 Important | Via JSearch |
| **Internshala** | 🔴 Critical (freshers) | Scrape public pages |
| **Freshersworld** | 🟡 Important | Scrape public pages |
| **Apna.co** | 🟡 Important (blue-collar) | API partnership or scrape |
| **CutShort** | 🟡 Important (tech/startup) | API partnership |
| **National Career Service** | 🟢 Nice-to-have | data.gov.in API |
| **iimjobs** | 🟢 Nice-to-have (MBA) | Scrape public pages |
| **Instahyre** | 🟢 Nice-to-have (senior tech) | Not feasible (invite-only) |

### 4.4 Salary Intelligence for India

Most Indian job postings **don't reveal salary**. CareerPilot should build salary intelligence:

```
SALARY ESTIMATION ENGINE
    │
    ├── JSearch /estimated-salary endpoint
    │   (Free with JSearch API)
    │
    ├── Glassdoor salary data
    │   (Via JSearch aggregation)
    │
    ├── Community-submitted salary data
    │   (Users optionally share their CTC)
    │
    ├── CTC → In-hand calculator
    │   ├── Deduct: EPF (12% employee + 12% employer)
    │   ├── Deduct: Professional tax (₹200-2500/month, state-dependent)
    │   ├── Deduct: Income tax (new vs old regime)
    │   ├── Deduct: Gratuity (4.81% of basic)
    │   ├── Deduct: Variable pay (typically 10-30% of CTC)
    │   └── Result: Monthly in-hand salary
    │
    └── Salary comparison
        ├── By role + experience + location
        ├── "This offer is 15% below market for your profile"
        └── "Top 10% of SDE II in Hyderabad earn ₹35L+"
```

### 4.5 Currency & Localization

```yaml
# India-specific configuration
india:
  currency: INR
  currency_symbol: ₹
  salary_format: "₹{amount} LPA"  # Lakhs Per Annum
  date_format: "DD/MM/YYYY"
  phone_format: "+91 XXXXX XXXXX"
  languages:
    - en  # English (primary)
    - hi  # Hindi
    - te  # Telugu (your region)
    - ta  # Tamil
    - kn  # Kannada
    - bn  # Bengali
    - mr  # Marathi
  time_zone: "Asia/Kolkata"  # IST (UTC+5:30)
  work_week: "Monday-Friday"
  notice_period_options:
    - immediate
    - 15_days
    - 30_days
    - 60_days
    - 90_days
  experience_format: "X.X years"
  education_system:
    - "10th"
    - "12th/PUC"
    - "Diploma"
    - "B.Tech/B.E."
    - "M.Tech/M.E."
    - "BCA/MCA"
    - "B.Sc/M.Sc"
    - "BBA/MBA"
    - "B.Com/M.Com"
    - "CA/CS"
    - "MBBS/MD"
```

### 4.6 India Market Sizing & Strategy

| Metric | Value |
|--------|-------|
| **Total addressable market** | 100M+ active job seekers in India |
| **IT/Tech job seekers** | ~5M+ |
| **Annual campus graduates** | ~1.5M engineering + 0.5M MBA |
| **Average time to find a job** | 3-6 months |
| **Average applications per person** | 50-200 |
| **CareerPilot TAM (IT/tech + freshers)** | ~7M users |
| **Target for Year 1** | 10,000 users |
| **Conversion rate (freemium)** | 10-15% |
| **Pricing (India-adjusted)** | ₹99-499/month (vs $10-50 global) |

**India pricing strategy:**
| Tier | Price (India) | Price (Global) | Features |
|------|--------------|----------------|----------|
| Free | ₹0 | $0 | 10 job matches/day, basic scoring |
| Pro | ₹149/month (~$1.80) | $9.99/month | Unlimited matches, resume tailoring, cover letters |
| Premium | ₹499/month (~$6) | $29.99/month | Auto-apply, interview prep, company research, priority matching |

This is **PPP-adjusted** (Purchasing Power Parity) pricing — standard practice for India market.

---

## Summary: Updated Decisions

| Decision | Your Direction | Confirmed Strategy |
|----------|---------------|-------------------|
| **LinkedIn/Indeed access** | Aggregator APIs | ✅ JSearch (primary) + LoopCV (secondary) |
| **LLM strategy** | Ollama + free models | ✅ Hybrid: Ollama qwen3:8b/14b (90%) + Gemini Flash (10%) |
| **Deduplication** | Excel sheet concept | ✅ Database-backed with embedding similarity + Excel export |
| **Geographic focus** | India-first | ✅ DPDP compliant, India connectors, ₹ pricing, CTC calculator |
| **Vector DB** | — | ✅ pgvector (simpler, one less service) |
| **Data sourcing** | — | ✅ JSearch + direct ATS APIs + India-specific scrapers |
| **Pricing model** | — | ✅ Freemium, India-adjusted: ₹0/149/499 per month |
| **Deployment** | — | ✅ Self-hosted Ollama + Supabase + Docker |

---

## Required Accounts & Secrets (Updated for India-First + Ollama)

| # | Service | Purpose | Free Tier | Secrets Needed | Priority |
|---|---------|---------|-----------|----------------|----------|
| 1 | **Supabase** | Auth + DB + Storage | 500MB, 50K MAU | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` | 🔴 Day 1 |
| 2 | **JSearch (RapidAPI)** | Job search (LinkedIn/Indeed/Naukri) | 500 req/month | `RAPIDAPI_KEY` | 🔴 Day 1 |
| 3 | **Google Gemini** | Premium LLM fallback | 1,500 RPD free | `GOOGLE_API_KEY` | 🔴 Day 1 |
| 4 | **Ollama** | Primary LLM (self-hosted) | Free (need GPU) | No API key | 🔴 Day 1 |
| 5 | **Serper.dev** | Google search for companies | 2,500 free queries | `SERPER_API_KEY` | 🟡 Week 1 |
| 6 | **Adzuna** | Additional job source | Free tier | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | 🟡 Week 1 |
| 7 | **Resend** | Email notifications | 3,000/month free | `RESEND_API_KEY` | 🟡 Week 2 |
| 8 | **LoopCV** | Resume parsing + auto-apply | Free tier | `LOOPCV_API_KEY` | 🟢 Month 1 |
| 9 | **Chrome Web Store** | Browser extension | $5 one-time | Developer account | 🟢 Month 2 |
| 10 | **Upstash** (optional) | Managed Redis | 10K cmd/day free | `REDIS_URL` | 🟡 Week 2 |

**You can start building with just items 1-4. Total cost: $0.**

---

*Ready for Phase 1? Confirm and I'll begin with Project Planning, System Architecture, UI Mockups, and Database Design.*
