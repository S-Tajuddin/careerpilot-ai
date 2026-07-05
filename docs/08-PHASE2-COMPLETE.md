# Phase 2 Complete — AI Scoring + Deduplication

## What Was Built

### 🧠 Scoring Engine (`services/scoring.py`)
6-dimensional weighted scoring with AEM-specific tuning:

| Dimension | Weight | What It Measures |
|---|---|---|
| **Skill Match** | 30% | Overlap between job skills and your profile using AEM skill taxonomy (7 groups, 50+ variants) |
| **Experience Match** | 25% | Your years vs required years; seniority inferred from title; sweet-spot detection |
| **Salary Match** | 15% | Alignment with your ₹20-35 LPA target; handles INR monthly→yearly and USD→INR |
| **Location Match** | 10% | Hyderabad, preferred cities, India metro cities, remote detection |
| **Company Quality** | 10% | Known AEM hirers (12+ companies), enterprise vs startup |
| **Remote Preference** | 10% | Your remote/hybrid/onsite/any preference vs job's arrangement |

**Output per job:**
- `overall_score` (0-100)
- `dimension_scores` (breakdown per dimension)
- `strengths[]` (what matches well)
- `weaknesses[]` (gaps to address)
- `recommendations[]` (AI-generated via Ollama — personalized advice)
- `embedding_id` (stored in ChromaDB for dedup)

### 🔄 Deduplication (`services/dedup.py`)
3-tier deduplication:

| Tier | Method | Catches |
|---|---|---|
| 1. Exact | `(source, source_id)` match | Same job from same API |
| 2. Fuzzy | Title + Company normalization | "Sr AEM Developer" = "AEM Developer" |
| 3. Semantic | Embedding similarity (0.85 threshold) | Same job from different sources |

Duplicates are soft-hidden (`is_active=False`) and linked via `canonical_job_id`.

### 🔗 Auto-Scoring in Job Search (`services/job_service.py`)
When jobs are found via search:
1. Jobs are saved to DB
2. **Auto-scored** against your profile using the 6-dimension engine
3. **Deduplicated** against existing jobs
4. Scores appear immediately in search results

### 📡 New API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/jobs/score` | Score a single job |
| POST | `/api/jobs/score/batch` | Score all unscored jobs |
| GET | `/api/jobs/{id}/score-detail` | Full scoring breakdown |
| POST | `/api/jobs/dedup` | Run deduplication pipeline |

### 🎨 Frontend Updates
- **"Score All" button** on Jobs page — scores all unscored jobs in one click
- **"Score This Job" button** on unscored job cards
- **"Score Detail" modal** — shows overall score, strengths, weaknesses, AI recommendations
- **Recommendations section** in expanded job cards

### 🧪 28 New Tests (`tests/test_scoring.py`)
- Scoring weights validation
- AEM skill taxonomy coverage
- Skill match: exact, partial, no overlap
- Experience: sweet spot, under-qualified, seniority inference from title
- Salary: within range, below range, unknown, monthly→yearly conversion
- Location: Hyderabad, remote preference, foreign
- Company quality: known AEM hirer, unknown
- Dedup: group key normalization, title similarity
- JSON parsing: valid, with surrounding text, invalid
- Integration: perfect AEM job (80+), unrelated job (low score)

## Files Created/Modified

### New
- `backend/app/services/scoring.py` — AI scoring engine (350 lines)
- `backend/app/services/dedup.py` — Deduplication service (180 lines)
- `backend/tests/test_scoring.py` — 28 scoring & dedup tests

### Modified
- `backend/app/services/job_service.py` — Auto-score + auto-dedup on search
- `backend/app/routers/jobs.py` — Score, batch-score, score-detail, dedup endpoints
- `frontend/src/app/jobs/page.tsx` — Score All, Score This, Score Detail modal

## How to Test

### 1. Restart backend
```cmd
cd careerpilot-ai\backend
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Search for jobs (auto-scores)
```
http://localhost:8000/api/jobs/search?query=AEM+developer&location=India
```
Jobs are now **automatically scored** on search.

### 3. View scores in frontend
```
http://localhost:3000/jobs
```
Click a job → expand → see match score, strengths, weaknesses, AI recommendations

### 4. Batch score all jobs
Click **"Score All"** button on Jobs page, or:
```
POST http://localhost:8000/api/jobs/score/batch
```

### 5. View score detail
```
GET http://localhost:8000/api/jobs/{job_id}/score-detail
```
Returns full breakdown: overall + 6 dimension scores + strengths/weaknesses/recommendations

## Test Results
```
63 tests passed (35 original + 28 Phase 2)
0 failures
```

## Next: Phase 3 — Resume Tailoring + Cover Letters
