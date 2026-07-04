# CareerPilot AI — Step-by-Step Account Setup Guide (100% FREE)

> **Goal:** Set up every free account and API key you need. Zero credit card. Zero cost.
>
> **Date:** 2026-07-04
> **Total time needed:** ~60-90 minutes for all accounts
> **Total cost:** ₹0

---

## Quick Overview — What You'll Set Up

| # | Service | What It Does | Free Tier | Time | Credit Card? |
|---|---------|-------------|-----------|------|-------------|
| 1 | Supabase | Auth + Database + Storage | 500MB DB, 50K MAU, 1GB storage | 10 min | ❌ No |
| 2 | JSearch (RapidAPI) | Job search (LinkedIn, Indeed, Naukri) | 200 req/month | 10 min | ❌ No |
| 3 | Google Gemini API | LLM for resume/cover letters | 500 RPD (Flash models) | 10 min | ❌ No |
| 4 | Ollama | Self-hosted LLM (scoring, matching) | Unlimited (your hardware) | 15 min | ❌ No |
| 5 | Serper.dev | Google search for companies | 2,500 queries one-time | 5 min | ❌ No |
| 6 | Adzuna | Additional job source | Free tier (India) | 5 min | ❌ No |
| 7 | Upstash Redis | Caching + background jobs | 256MB, 500K commands/month | 5 min | ❌ No |
| 8 | Resend | Email notifications | 3,000 emails/month | 5 min | ❌ No |
| 9 | GitHub | Code hosting + CI/CD | Unlimited private repos | 5 min | ❌ No |
| 10 | Docker Hub | Container image hosting | Unlimited public images | 5 min | ❌ No |

---

## 1. SUPABASE — Auth + Database + Storage

### What you'll get:
- `SUPABASE_URL` — Your project URL (like `https://abcdefgh.supabase.co`)
- `SUPABASE_ANON_KEY` — Public key (safe for frontend)
- `SUPABASE_SERVICE_KEY` — Secret key (backend only, NEVER expose)
- Free PostgreSQL database with pgvector support

### Step-by-step:

```
STEP 1: Go to https://supabase.com

STEP 2: Click "Start your project" (green button, top right)

STEP 3: Sign up (choose one):
  Option A: "Continue with GitHub" (RECOMMENDED — you'll need GitHub anyway)
  Option B: "Continue with Google"
  Option C: Enter email + password

STEP 4: After login, you'll see the Dashboard.
  Click "New Project" button.

STEP 5: Fill in the form:
  ┌─────────────────────────────────────────────────┐
  │ Name:           careerpilot-ai                   │
  │ Database Password: [click "Generate a password"] │
  │                  ↓ COPY THIS PASSWORD SAFE! ↓    │
  │ Region:         Southeast Asia (Singapore)       │
  │                  (closest to India with good      │
  │                   latency — ~50ms from Hyderabad) │
  └─────────────────────────────────────────────────┘
  
  Click "Create new project"

STEP 6: Wait 1-2 minutes while Supabase provisions your project.

STEP 7: Get your keys:
  - Click the ⚙️ Settings icon (left sidebar)
  - Click "API" 
  - You'll see:

  ┌───────────────────────────────────────────────────────┐
  │ Project URL                                           │
  │ https://abcdefghij.supabase.co     ← COPY THIS       │
  │                                                       │
  │ anon (public)                                         │
  │ eyJhbGciOiJIUzI1NiIs...            ← COPY THIS       │
  │                                                       │
  │ service_role (secret)                                 │
  │ eyJhbGciOiJIUzI1NiIs...            ← COPY THIS       │
  │ ⚠️ This key has admin access. NEVER put in frontend!  │
  └───────────────────────────────────────────────────────┘

STEP 8: Enable pgvector extension (needed for embeddings):
  - Click "SQL Editor" (left sidebar)
  - Click "+ New query"
  - Paste this SQL:

    CREATE EXTENSION IF NOT EXISTS vector;

  - Click "Run" (green button)
  - You should see "Success" message
```

### Save these in your `.env` file:
```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIs...
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.your-project-id.supabase.co:5432/postgres
```

### Free tier limits:
- 500 MB database
- 50,000 monthly active users (auth)
- 1 GB file storage
- 500 MB bandwidth
- 2 projects allowed

---

## 2. JSEARCH API (RapidAPI) — Job Search

### What you'll get:
- `RAPIDAPI_KEY` — Your API key for JSearch
- Access to jobs from LinkedIn, Indeed, Glassdoor, Naukri via Google for Jobs
- India support with `country=in`

### Step-by-step:

```
STEP 1: Go to https://rapidapi.com/open-web-ninja-open-web-ninja-default/api/jsearch

STEP 2: Click "Sign Up" (top right)
  - Choose "Continue with Google" or "Continue with GitHub"
  - Or create account with email + password

STEP 3: After signup, you'll be on the JSearch API page.
  Click "Pricing" tab at the top.

STEP 4: Select the FREE plan:
  ┌─────────────────────────────────────────────────┐
  │ BASIC                                           │
  │ $0.00 / month                                   │
  │ 200 requests / month                            │
  │ Rate limit: 1,000 requests / hour               │
  │                                                 │
  │ [Subscribe]  ← CLICK THIS                       │
  └─────────────────────────────────────────────────┘

  No credit card needed. Click confirm.

STEP 5: Get your API key:
  - Go back to the "Endpoints" tab
  - Look at the "Header Parameters" section on the right
  - You'll see:

  ┌───────────────────────────────────────────────────┐
  │ X-RapidAPI-Key                                     │
  │ ab1234cdef5678ghij9012klm3456nopq78... ← COPY THIS│
  │                                                     │
  │ X-RapidAPI-Host                                     │
  │ jsearch.p.rapidapi.com                             │
  └───────────────────────────────────────────────────┘

STEP 6: Test it! Click "Test Endpoint" on the /search endpoint.
  - Change query to: "software engineer in hyderabad"
  - Change country to: "in"
  - Click "Test Endpoint"
  - You should see JSON with job listings
```

### Save in your `.env` file:
```bash
RAPIDAPI_KEY=ab1234cdef5678ghij9012klm3456nopq78...
JSEARCH_HOST=jsearch.p.rapidapi.com
```

### Quick test in terminal:
```bash
curl -X GET "https://jsearch.p.rapidapi.com/search?query=python+developer+in+hyderabad&country=in&num_pages=1" \
  -H "X-RapidAPI-Key: YOUR_KEY_HERE" \
  -H "X-RapidAPI-Host: jsearch.p.rapidapi.com"
```

### Free tier limits:
- 200 requests/month (enough for development)
- 1,000 requests/hour rate limit
- All endpoints included

### 💡 TO GET MORE FREE REQUESTS:
JSearch is also available directly at https://www.openwebninja.com/api/jsearch
The direct portal offers a DIFFERENT free tier with potentially more requests.
Sign up there too with the same email and compare.

---

## 3. GOOGLE GEMINI API — LLM for Premium Features

### What you'll get:
- `GOOGLE_API_KEY` — API key starting with `AIza...`
- Free access to Gemini Flash models (2.5 Flash, 2.5 Flash-Lite, 3 Flash)
- 500 requests/day on Flash models (plenty for development)

### Step-by-step:

```
STEP 1: Go to https://aistudio.google.com

STEP 2: Sign in with your Google account (Gmail)
  - If you don't have one, create a Gmail account first

STEP 3: Accept the Terms of Service
  - Read and click "I agree" or "Accept"

STEP 4: Get your API key:
  - Click "Get API key" button (visible on the homepage)
  - OR click "API keys" in the left sidebar
  
  ┌──────────────────────────────────────────────────┐
  │ Click "Create API key"                           │
  │                                                  │
  │ Select a Google Cloud project:                   │
  │   - "Create new project" (RECOMMENDED)           │
  │   - Name it: "careerpilot-ai"                    │
  │                                                  │
  │ Click "Create API key in existing project"        │
  └──────────────────────────────────────────────────┘

STEP 5: Your API key appears:
  ┌──────────────────────────────────────────────────┐
  │ Your API key                                     │
  │ AIzaSyB1234567890abcdefghijklmnop...  ← COPY THIS│
  │                                                  │
  │ ⚠️ Copy this key now. You can always find it     │
  │    again in API keys page, but copy it safe.      │
  └──────────────────────────────────────────────────┘

STEP 6: IMPORTANT — Restrict your key (security best practice):
  - Click on the key name to edit it
  - Under "API restrictions", select "Restrict key"
  - Check only "Generative Language API"
  - Click Save

STEP 7: Test your key:
  - In Google AI Studio, go to "Prompt" tab
  - Select model: "Gemini 2.5 Flash"
  - Type: "Hello, respond with one sentence"
  - Click "Run"
  - You should get a response
```

### Save in your `.env` file:
```bash
GOOGLE_API_KEY=AIzaSyB1234567890abcdefghijklmnop...
```

### Quick test in terminal:
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
  -H "x-goog-api-key: YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "contents": [{
      "parts": [{"text": "Say hello in one sentence"}]
    }]
  }'
```

### Free tier limits (as of mid-2026):
| Model | RPM | RPD | TPM |
|-------|-----|-----|-----|
| Gemini 2.5 Flash | 10 | 500 | 250K shared |
| Gemini 2.5 Flash-Lite | 15 | 1,000 | 250K shared |
| Gemini 3 Flash | 10 | 500 | 250K shared |
| Gemini Pro models | ❌ Paid only | — | — |

### ⚠️ Important notes:
- **India is supported** — Google AI Studio works from India
- **No credit card needed** for free tier
- **Google may use your inputs to train models** on free tier (not an issue for job descriptions, but never send PII through free tier)
- Keys created after June 2026 are **restricted by default** — if you get auth errors, check key restrictions

---

## 4. OLLAMA — Self-Hosted LLM (Zero Cost, Unlimited)

### What you'll get:
- Local LLM server running on `http://localhost:11434`
- Free unlimited API calls to local models
- No API key needed (runs on your machine)

### Step-by-step:

#### On Linux (Ubuntu/Debian — most common for servers):

```
STEP 1: Install Ollama
  Open terminal and run:

  curl -fsSL https://ollama.com/install.sh | sh

  This downloads and installs Ollama, creates a systemd service,
  and starts it automatically.

STEP 2: Verify installation
  ollama --version
  # Should output: ollama version 0.x.x

STEP 3: Check service is running
  systemctl status ollama
  # Should show "active (running)"

STEP 4: Pull your first model (the one we'll use most)

  # Small model for job scoring (5.2 GB download)
  ollama pull qwen3:8b

  # Wait for download to complete (5-15 minutes depending on speed)

STEP 5: Test it
  ollama run qwen3:8b "What skills are needed for a Python developer?"
  
  You should get a response! Type /bye to exit.

STEP 6: Pull the embedding model (needed for semantic search)
  ollama pull nomic-embed-text

STEP 7: Pull the medium model for resume tailoring (9 GB download)
  # Only if you have 12GB+ VRAM or 32GB+ RAM
  ollama pull qwen3:14b
```

#### On Windows:

```
STEP 1: Download the installer
  Go to https://ollama.com/download
  
  Click "Download for Windows"
  
  Run the downloaded OllamaSetup.exe
  
  Follow the installation wizard (Next → Next → Install)

STEP 2: Open Command Prompt or PowerShell

STEP 3: Pull models
  ollama pull qwen3:8b
  ollama pull nomic-embed-text

STEP 4: Test
  ollama run qwen3:8b "Hello, respond in one sentence"
```

#### On macOS:

```
STEP 1: Install via Homebrew (recommended)
  brew install ollama

  OR download from https://ollama.com/download

STEP 2: Start Ollama
  ollama serve

STEP 3: In a new terminal, pull models
  ollama pull qwen3:8b
  ollama pull nomic-embed-text

STEP 4: Test
  ollama run qwen3:8b "Hello"
```

#### Using Docker (for deployment):

```bash
# CPU only
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# With NVIDIA GPU
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Pull models inside the container
docker exec -it ollama ollama pull qwen3:8b
docker exec -it ollama ollama pull nomic-embed-text
```

### Test the API:
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:8b",
  "prompt": "List 5 skills needed for a Python developer in Hyderabad",
  "stream": false
}'
```

### No `.env` entry needed — Ollama uses:
```bash
OLLAMA_HOST=http://localhost:11434  # default
# No API key required!
```

### Hardware requirements:
| Model | RAM Needed | VRAM Needed | Disk Space | Speed |
|-------|-----------|-------------|-----------|-------|
| qwen3:8b | 8 GB | 6 GB (GPU) | 5.2 GB | 30-80 tok/s |
| qwen3:14b | 16 GB | 10 GB (GPU) | 9 GB | 18-30 tok/s |
| nomic-embed-text | 4 GB | 2 GB | 274 MB | Fast |

### ⚠️ If you DON'T have a GPU:
- Ollama still works on CPU only (slower: 5-15 tok/s for 8B)
- For development, this is fine — scoring doesn't need to be fast
- For production, rent a GPU VPS ( cheapest: ~₹2,000/month on Indian cloud providers like E2E Networks or Lambda Labs)

---

## 5. SERPER.DEV — Google Search for Company Research

### What you'll get:
- `SERPER_API_KEY` — API key for Google search
- 2,500 free queries (one-time, not monthly)
- Used for: company research, finding career pages, discovering job postings

### Step-by-step:

```
STEP 1: Go to https://serper.dev

STEP 2: Click "Sign Up" (top right)
  - Sign up with Google OR email + password

STEP 3: After signup, you'll be on the Dashboard.
  Your API key is right there:

  ┌──────────────────────────────────────────────────┐
  │ API Key                                          │
  │ abc123def456ghi789jkl012mno345...    ← COPY THIS│
  │                                                  │
  │ Free Credits: 2,500                              │
  └──────────────────────────────────────────────────┘

STEP 4: Test it
  Click "API Playground" or use curl:

  curl -X POST "https://google.serper.dev/search" \
    -H "X-API-KEY: YOUR_KEY" \
    -H "Content-Type: application/json" \
    -d '{"q": "Google India careers software engineer"}'
```

### Save in your `.env` file:
```bash
SERPER_API_KEY=abc123def456ghi789jkl012mno345...
```

### Free tier limits:
- 2,500 queries total (not per month — it's one-time)
- After that: $50/50,000 queries (~$0.001/query)
- No credit card needed for free tier

---

## 6. ADZUNA — Additional Job Source (India)

### What you'll get:
- `ADZUNA_APP_ID` — Application ID
- `ADZUNA_APP_KEY` — API key
- Access to job listings in India, UK, and other markets

### Step-by-step:

```
STEP 1: Go to https://developer.adzuna.com

STEP 2: Click "Sign Up" (top right)

STEP 3: Fill in registration form:
  ┌─────────────────────────────────────────────────┐
  │ Name:        Your Name                           │
  │ Email:       your-email@gmail.com                │
  │ Password:    [choose a strong password]           │
  │                                                  │
  │ I want to:   "Access the Adzuna API"             │
  │                                                  │
  │ Click "Create Account"                           │
  └─────────────────────────────────────────────────┘

STEP 4: Verify your email
  Check inbox, click verification link

STEP 5: Create an application
  After login, click "Create a new application"
  
  ┌─────────────────────────────────────────────────┐
  │ Application Name: careerpilot-ai                 │
  │ Description: AI career assistant that searches   │
  │              jobs and matches candidates          │
  │                                                  │
  │ Click "Create"                                   │
  └─────────────────────────────────────────────────┘

STEP 6: Get your credentials
  On the application page, you'll see:

  ┌──────────────────────────────────────────────────┐
  │ Application ID                                    │
  │ 12345                              ← COPY THIS   │
  │                                                    │
  │ Application Key                                   │
  │ abc123def456789                    ← COPY THIS   │
  └──────────────────────────────────────────────────┘
```

### Save in your `.env` file:
```bash
ADZUNA_APP_ID=12345
ADZUNA_APP_KEY=abc123def456789
```

### Quick test:
```bash
curl "https://api.adzuna.com/v1/api/jobs/in/search/1?app_id=YOUR_APP_ID&app_key=YOUR_APP_KEY&what=python%20developer&where=hyderabad"
```

### Free tier limits:
- No strict request limit on free tier
- Fair use policy applies
- Covers India (`/jobs/in/`)

---

## 7. UPSTASH REDIS — Caching + Background Jobs

### What you'll get:
- `REDIS_URL` — Connection string for Redis
- 256 MB storage, 500K commands/month

### Step-by-step:

```
STEP 1: Go to https://upstash.com

STEP 2: Click "Sign Up" (top right)
  - "Continue with GitHub" (RECOMMENDED)
  - Or "Continue with Google"
  - Or email + password

STEP 3: After login, click "+ Create Database"

STEP 4: Fill in the form:
  ┌─────────────────────────────────────────────────────┐
  │ Name:          careerpilot-redis                     │
  │ Type:          Regional                              │
  │ Primary Region: Asia Pacific (Singapore) or          │
  │                 US East (Virginia)                    │
  │ Eviction:      No eviction                           │
  │                                                     │
  │ Click "Create"                                      │
  └─────────────────────────────────────────────────────┘

STEP 5: Get your connection details:
  On the database page, click "Details" tab

  ┌──────────────────────────────────────────────────────┐
  │ Connection Details                                    │
  │                                                       │
  │ Endpoint:  us1-xxxx-xxxxx.upstash.io  ← Note this   │
  │ Port:      33902                                      │
  │ Password:  a1b2c3d4e5f6...             ← COPY THIS  │
  │                                                       │
  │ Redis URL:                                            │
  │ rediss://default:a1b2c3d4e5f6...@us1-xxxx.upstash.io│
  │                               ↑ COPY THE FULL URL    │
  │                                                       │
  │ ⚠️ "rediss://" (with double s) means TLS encrypted  │
  └──────────────────────────────────────────────────────┘
```

### Save in your `.env` file:
```bash
REDIS_URL=rediss://default:a1b2c3d4e5f6...@us1-xxxx-xxxxx.upstash.io:33902
```

### Free tier limits:
- 256 MB storage
- 500,000 commands/month
- 10,000 commands/day soft limit
- No credit card needed
- No expiration

### 💡 ALTERNATIVE: If you prefer self-hosted Redis (truly free, unlimited):
```bash
# Just add this to your docker-compose.yml:
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data

# Then use: REDIS_URL=redis://localhost:6379/0
```

---

## 8. RESEND — Email Notifications

### What you'll get:
- `RESEND_API_KEY` — API key for sending emails
- 3,000 emails/month for free
- Can send from `onboarding@resend.dev` for testing

### Step-by-step:

```
STEP 1: Go to https://resend.com

STEP 2: Click "Sign Up" (top right)
  - "Continue with GitHub" (RECOMMENDED)
  - Or "Continue with Google"
  - Or email + password

STEP 3: After login, you'll see the Dashboard.

STEP 4: Get your API key:
  Click "API Keys" in the left sidebar
  
  ┌──────────────────────────────────────────────────┐
  │ Click "Create API Key"                           │
  │                                                  │
  │ Name: careerpilot-ai                             │
  │ Permission: Full access                          │
  │                                                  │
  │ Click "Add"                                      │
  │                                                  │
  │ API Key: re_abc123def456...        ← COPY THIS   │
  │ ⚠️ This is shown only ONCE! Copy it now!         │
  └──────────────────────────────────────────────────┘

STEP 5: For DEVELOPMENT, you can send emails immediately:
  Resend provides a default sender: onboarding@resend.dev
  This works for testing without domain verification.

STEP 6: For PRODUCTION, add your domain:
  Click "Domains" → "Add Domain"
  Enter your domain (e.g., careerpilot.ai)
  Add the DNS records Resend provides to your domain
  (Do this later when you have a domain)
```

### Save in your `.env` file:
```bash
RESEND_API_KEY=re_abc123def456...
```

### Quick test:
```bash
curl -X POST 'https://api.resend.com/emails' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "onboarding@resend.dev",
    "to": ["your-email@gmail.com"],
    "subject": "CareerPilot AI Test",
    "html": "<p>Hello from CareerPilot AI!</p>"
  }'
```

### Free tier limits:
- 3,000 emails/month
- 100 emails/day
- Can only send to verified emails in development mode
- Must verify domain for production sending

---

## 9. GITHUB — Code Hosting + CI/CD

### What you'll get:
- GitHub account for repository hosting
- GitHub Actions for CI/CD (2,000 minutes/month free)
- GitHub Token for automated workflows

### Step-by-step:

```
STEP 1: Go to https://github.com/signup

STEP 2: Create account:
  ┌─────────────────────────────────────────────────┐
  │ Username:  your-username                         │
  │ Email:     your-email@gmail.com                  │
  │ Password:  [strong password]                     │
  │                                                  │
  │ Click "Create account"                           │
  └─────────────────────────────────────────────────┘

STEP 3: Verify email
  Check inbox, click verification link

STEP 4: Complete profile setup (skip optional ones)

STEP 5: Create a Personal Access Token:
  - Go to https://github.com/settings/tokens
  - Click "Generate new token" → "Generate new token (classic)"
  
  ┌─────────────────────────────────────────────────┐
  │ Note:        careerpilot-ai-ci                   │
  │ Expiration:  90 days                             │
  │ Scopes:      ✅ repo                             │
  │              ✅ workflow                         │
  │              ✅ write:packages                   │
  │                                                  │
  │ Click "Generate token"                           │
  │                                                  │
  │ Token: ghp_abc123def456...        ← COPY THIS   │
  │ ⚠️ Shown only ONCE! Save it now!                 │
  └─────────────────────────────────────────────────┘

STEP 6: Create the repository:
  - Go to https://github.com/new
  - Repository name: careerpilot-ai
  - Description: AI-powered career assistant
  - Private ✅ (or Public if open-source)
  - DON'T initialize with README (we'll push our own)
  - Click "Create repository"
```

### Save in your `.env` file:
```bash
GITHUB_TOKEN=ghp_abc123def456...
```

### Free tier limits:
- Unlimited private repositories
- 2,000 GitHub Actions minutes/month
- 500 MB GitHub Packages storage
- No credit card needed

---

## 10. DOCKER HUB — Container Image Hosting

### What you'll get:
- Docker Hub account for pushing/pulling images
- Unlimited public repositories

### Step-by-step:

```
STEP 1: Go to https://hub.docker.com/signup

STEP 2: Create account:
  ┌─────────────────────────────────────────────────┐
  │ Username:    your-docker-username                │
  │ Email:       your-email@gmail.com                │
  │ Password:    [strong password]                   │
  │                                                  │
  │ Click "Sign Up"                                  │
  └─────────────────────────────────────────────────┘

STEP 3: Verify email

STEP 4: Create an Access Token:
  - Go to https://hub.docker.com/settings/security
  - Click "New Access Token"
  
  ┌─────────────────────────────────────────────────┐
  │ Description: careerpilot-ai-deploy               │
  │ Permissions: Read & Write                        │
  │                                                  │
  │ Click "Generate"                                 │
  │                                                  │
  │ Token: dckr_abc123def456...       ← COPY THIS   │
  └─────────────────────────────────────────────────┘
```

### Save in your `.env` file:
```bash
DOCKERHUB_USERNAME=your-docker-username
DOCKERHUB_TOKEN=dckr_abc123def456...
```

### Free tier limits:
- Unlimited public repositories
- 1 private repository
- 200 pulls / 6 hours (rate limit)

---

## COMPLETE .env FILE

After completing ALL setups above, create this file:

```bash
# ==============================================================
# CareerPilot AI — Environment Variables (FREE TIER)
# ==============================================================
# ⚠️ NEVER commit this file to git! Add .env to .gitignore
# ==============================================================

# --- Supabase (Auth + DB + Storage) ---
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIs...
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.your-project.supabase.co:5432/postgres

# --- JSearch / RapidAPI (Job Search) ---
RAPIDAPI_KEY=ab1234cdef5678ghij9012...
JSEARCH_HOST=jsearch.p.rapidapi.com

# --- Google Gemini (LLM) ---
GOOGLE_API_KEY=AIzaSyB1234567890...

# --- Ollama (Self-hosted LLM) ---
OLLAMA_HOST=http://localhost:11434

# --- Serper.dev (Google Search) ---
SERPER_API_KEY=abc123def456ghi789...

# --- Adzuna (Job Search) ---
ADZUNA_APP_ID=12345
ADZUNA_APP_KEY=abc123def456789

# --- Upstash Redis (Caching) ---
REDIS_URL=rediss://default:password@host.upstash.io:33902
# OR self-hosted: redis://localhost:6379/0

# --- Resend (Email) ---
RESEND_API_KEY=re_abc123def456...

# --- GitHub (CI/CD) ---
GITHUB_TOKEN=ghp_abc123def456...

# --- Docker Hub ---
DOCKERHUB_USERNAME=your-username
DOCKERHUB_TOKEN=dckr_abc123def456...

# --- App Config ---
APP_ENV=development
APP_URL=http://localhost:3000
API_URL=http://localhost:8000
SECRET_KEY=generate-a-random-64-char-string-here
```

### Generate a SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
# Copy the output as your SECRET_KEY
```

---

## VERIFICATION CHECKLIST

After setting up everything, verify each service works:

```bash
# 1. Supabase — Check connection
curl -H "apikey: YOUR_SUPABASE_ANON_KEY" \
     "https://your-project.supabase.co/rest/v1/" 
# Should return: {"message":"Authentication required"} or similar

# 2. JSearch — Search jobs in Hyderabad
curl -X GET "https://jsearch.p.rapidapi.com/search?query=python+developer+in+hyderabad&country=in&num_pages=1" \
  -H "X-RapidAPI-Key: YOUR_KEY" \
  -H "X-RapidAPI-Host: jsearch.p.rapidapi.com"
# Should return: JSON with job listings

# 3. Gemini — Generate text
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
  -H "x-goog-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
# Should return: JSON with generated text

# 4. Ollama — Local LLM
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:8b",
  "prompt": "Hello",
  "stream": false
}'
# Should return: JSON with response

# 5. Serper — Google search
curl -X POST "https://google.serper.dev/search" \
  -H "X-API-KEY: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "TCS careers India"}'
# Should return: JSON with search results

# 6. Adzuna — Job search
curl "https://api.adzuna.com/v1/api/jobs/in/search/1?app_id=YOUR_ID&app_key=YOUR_KEY&what=software"
# Should return: JSON with job listings

# 7. Redis — Cache test
redis-cli -u YOUR_REDIS_URL ping
# Should return: PONG

# 8. Resend — Email test
curl -X POST 'https://api.resend.com/emails' \
  -H 'Authorization: Bearer YOUR_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"from":"onboarding@resend.dev","to":["your-email@gmail.com"],"subject":"Test","html":"<p>Works!</p>"}'
# Should return: JSON with email ID
```

---

## TROUBLESHOOTING COMMON ISSUES

| Problem | Solution |
|---------|----------|
| **Supabase: "Project not found"** | Wait 2 minutes after creation; check URL is correct |
| **JSearch: "401 Unauthorized"** | Make sure you subscribed to the FREE plan first |
| **JSearch: "429 Too Many Requests"** | You hit the 200/month limit. Wait or upgrade. |
| **Gemini: "API key not valid"** | Check key starts with `AIza`. Check restrictions. |
| **Gemini: "User location not supported"** | Use a VPN set to US/India. Some regions are blocked. |
| **Ollama: "Connection refused"** | Run `ollama serve` first in a separate terminal |
| **Ollama: "Out of memory"** | Use a smaller model (qwen3:1.7b instead of 8b) |
| **Serper: "No credits"** | Free credits are one-time. Budget carefully. |
| **Adzuna: "403 Forbidden"** | Verify your email first. Check app_id and app_key. |
| **Redis: "Connection refused"** | Make sure Redis is running. Check URL format. |
| **Resend: "Sender not verified"** | Use `onboarding@resend.dev` for testing only |
| **Resend: "Rate limit"** | Max 100 emails/day on free tier |

---

## COST SUMMARY — ALL FREE

| Service | Monthly Cost | Annual Cost |
|---------|-------------|-------------|
| Supabase | ₹0 | ₹0 |
| JSearch (RapidAPI) | ₹0 (200 req/mo) | ₹0 |
| Google Gemini | ₹0 (500 RPD) | ₹0 |
| Ollama | ₹0 (electricity only) | ₹0 |
| Serper.dev | ₹0 (2,500 one-time) | ₹0 |
| Adzuna | ₹0 | ₹0 |
| Upstash Redis | ₹0 | ₹0 |
| Resend | ₹0 (3K emails/mo) | ₹0 |
| GitHub | ₹0 | ₹0 |
| Docker Hub | ₹0 | ₹0 |
| **TOTAL** | **₹0** | **₹0** |

### When you'll need to start paying:
| Milestone | What to Upgrade | Approx. Cost |
|-----------|----------------|-------------|
| 200+ job searches/month | JSearch Basic plan | ~₹1,200/mo ($15) |
| 500+ LLM calls/day | Gemini paid tier | ~₹500/mo ($6) |
| 3,000+ emails/month | Resend Pro | ~₹1,600/mo ($20) |
| 500K+ Redis commands/month | Upstash Pay-as-you-go | ~₹200/mo ($2) |
| 500MB+ database | Supabase Pro | ~₹2,100/mo ($25) |
| **Full production (1K users)** | **All of above** | **~₹5,600/mo ($67)** |

---

*You now have everything needed to start building. Next: Phase 1 implementation begins!*
