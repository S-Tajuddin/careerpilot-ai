# CareerPilot AI — Pre-Implementation Brainstorm & Risk Analysis

> **Document Purpose:** Identify showstoppers, legal risks, technical blockers, required accounts/keys, and enhancement opportunities BEFORE writing a single line of code.
>
> **Date:** 2026-07-04
> **Status:** Pre-Phase 1 — Decision Gate

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Showstoppers — Things That Could Kill the Project](#2-showstoppers)
3. [Critical Legal & Compliance Risks](#3-critical-legal--compliance-risks)
4. [Technical Blockers & Hard Problems](#4-technical-blockers--hard-problems)
5. [Required Accounts, API Keys & Secrets](#5-required-accounts-api-keys--secrets)
6. [Cost Estimation at Scale](#6-cost-estimation-at-scale)
7. [Recommended Enhancements](#7-recommended-enhancements)
8. [Architecture Reconsiderations](#8-architecture-reconsiderations)
9. [Connector-by-Connector Feasibility](#9-connector-by-connector-feasibility)
10. [Mitigation Strategies](#10-mitigation-strategies)
11. [Go / No-Go Decision Matrix](#11-go--no-go-decision-matrix)
12. [Recommended Phase 0 Tasks](#12-recommended-phase-0-tasks)

---

## 1. Executive Summary

CareerPilot AI is an ambitious, multi-agent career assistant platform. The concept is sound and the market need is real. However, **several areas carry existential risk** if not addressed upfront:

- **Legal exposure from job scraping** (CFAA, TOS violations, GDPR)
- **No public API for Workday, Oracle, SAP, iCIMS** — these require scraping or paid aggregators
- **LLM cost at scale** — each user generating tailored resumes, cover letters, and match scores across dozens of jobs could cost $2-5/month in LLM tokens alone
- **Browser extension limitations under Manifest V3** — reduces automation capabilities
- **LinkedIn/Indeed data is effectively inaccessible** without legal risk
- **Data freshness & deduplication** is a significantly harder problem than it appears

The project **IS feasible** but requires strategic decisions on data sourcing, cost management, and legal boundaries before implementation begins.

---

## 2. Showstoppers

### 🔴 SHOWSTOPPER #1: LinkedIn & Indeed Data Access

| Factor | Detail |
|--------|--------|
| **Risk** | LinkedIn explicitly prohibits scraping in its TOS. Indeed has pursued legal action against scrapers. |
| **Legal Precedent** | hiQ v. LinkedIn (2022 settlement) — public data scraping may not violate CFAA, but creating fake accounts does. TOS violations remain a breach-of-contract risk. |
| **Practical Reality** | LinkedIn aggressively blocks scraping: CAPTCHAs, IP bans, behavioral analysis. At scale, it's unworkable without massive proxy infrastructure. |
| **Impact** | These two platforms represent ~60-70% of all job listings. Without them, coverage is significantly reduced. |
| **Verdict** | ⚠️ **Cannot scrape directly. Must use aggregator APIs or skip these sources entirely.** |

### 🔴 SHOWSTOPPER #2: Workday, Oracle, iCIMS, SAP — No Public Job APIs

| ATS | Public API? | Access Method |
|-----|-------------|---------------|
| Greenhouse | ✅ Yes | `GET /v1/boards/{token}/jobs?content=true` — no auth needed |
| Lever | ✅ Yes | `GET /v0/postings/{site}?mode=json` — no auth needed |
| Ashby | ✅ Yes | `GET /posting-api/job-board/{name}?includeCompensation=true` |
| Workable | ✅ Yes | `GET /api/accounts/{subdomain}?details=true` |
| Recruitee | ✅ Yes | `GET /api/offers/` |
| Personio | ✅ Yes (XML) | `GET /xml?language=en` |
| **Workday** | ❌ No | Requires per-tenant authenticated API or sitemap.xml scraping |
| **iCIMS** | ❌ No | No public API; requires scraping career pages |
| **SAP SuccessFactors** | ❌ No | Has hidden XML sitemap (`/sitemal.xml`) but needs per-tenant CSRF token handling |
| **Oracle Taleo** | ❌ No | Legacy system; career page scraping only |
| **SmartRecruiters** | ⚠️ Partial | Has a public career site API but limited filtering |

**Impact:** Workday alone is used by ~40% of Fortune 500 companies. Not supporting it means missing a huge segment of enterprise job postings.

**Verdict:** ⚠️ **For closed ATS platforms, must either (a) scrape public career pages carefully, (b) use paid aggregator APIs, or (c) accept coverage gaps.**

### 🔴 SHOWSTOPPER #3: LLM Cost at Scale

Estimated token usage per user per month:

| Feature | Calls/Month | Tokens/Call | Monthly Tokens |
|---------|-------------|-------------|----------------|
| Job Match Scoring | 100 | 2,000 | 200,000 |
| Resume Tailoring | 10 | 4,000 | 40,000 |
| Cover Letter Generation | 10 | 3,000 | 30,000 |
| Company Research | 20 | 3,000 | 60,000 |
| Interview Prep | 5 | 3,000 | 15,000 |
| **Total** | | | **~345,000** |

At GPT-4o pricing (~$2.50/$10 per 1M tokens, avg $5/M blended):
- **Per user/month:** ~$1.73
- **At 1,000 users:** ~$1,730/month
- **At 10,000 users:** ~$17,300/month

Using cheaper models (Gemini Flash-Lite at $0.10/$0.40 per 1M tokens):
- **Per user/month:** ~$0.09
- **At 10,000 users:** ~$900/month

**Verdict:** ⚠️ **Must implement tiered model selection. Use cheap models for scoring/summarization, expensive models only for resume tailoring and cover letters. Budget for this from day one.**

### 🟡 SHOWSTOPPER #4: Browser Extension Manifest V3 Limitations

| Limitation | Impact |
|------------|--------|
| No persistent background pages | Extension can't maintain long-lived connections to backend |
| Service workers timeout after 30s of inactivity | Job detection becomes unreliable on slow-loading pages |
| Stricter content security policies | Injected autofill scripts may be blocked |
| `chrome.webRequest` blocking removed | Can't intercept/modify form submissions |
| Permissions auto-revoked if unused | Users may lose extension access silently |
| Chrome Web Store review process | ~1-3 day review for each update; can be rejected |

**Verdict:** ⚠️ **Manifest V3 is workable for read-only detection + autofill assistance, but full automation (auto-submit applications) is severely limited. This is actually a feature, not a bug — keeps user in control.**

### 🟡 SHOWSTOPPER #5: Data Freshness & Deduplication

| Problem | Detail |
|---------|--------|
| Job postings change constantly | A job posted today may close tomorrow |
| Same job appears on multiple sources | Company site + Greenhouse + LinkedIn + Indeed — same role |
| Salary info is often missing | Makes salary matching unreliable |
| Remote/hybrid classification is inconsistent | "Remote" could mean fully remote, hybrid, or remote-with-relocation |
| Job descriptions are unstructured | Every ATS formats them differently |

**Verdict:** ⚠️ **Deduplication is a hard NLP problem. Budget significant engineering time for this. Consider using embedding similarity (threshold ~0.92) + title/location heuristics.**

---

## 3. Critical Legal & Compliance Risks

### 3.1 CFAA (Computer Fraud & Abuse Act) — USA

| Activity | Risk Level |
|----------|------------|
| Scraping public job pages (no login required) | 🟢 Low — Protected by hiQ v. LinkedIn precedent |
| Scraping behind login walls | 🔴 High — CFAA violation |
| Creating fake accounts to access data | 🔴 High — hiQ settlement explicitly banned this |
| Bypassing CAPTCHAs | 🔴 High — Technical barrier circumvention |
| Respecting robots.txt | 🟡 Optional — Not legally binding, but best practice |

### 3.2 GDPR (EU) & CCPA (California)

| Concern | Detail |
|---------|--------|
| User resume data | Contains PII — must be stored, processed, and deleted on request |
| Job posting data | May contain recruiter PII (name, email) |
| AI profiling | GDPR Article 22 gives users right not to be subject to automated decisions |
| Data retention | Must define and enforce retention periods |
| Cross-border data transfer | If using US-based LLM APIs with EU user data |

**Required:** Privacy policy, cookie consent, data processing agreements, right-to-deletion endpoint, DPA with LLM providers.

### 3.3 Terms of Service Violations

| Platform | Stance | Risk |
|----------|--------|------|
| LinkedIn | Explicitly prohibits scraping | Account ban + potential lawsuit |
| Indeed | Prohibits scraping; has pursued legal action | Cease-and-desist likely |
| Glassdoor | Prohibits automated access | Account ban |
| Google | CSE API closed to new customers (2025); $5/1K queries for existing | Cost barrier |
| Greenhouse | Public API explicitly provided | 🟢 Safe |
| Lever | Public API explicitly provided | 🟢 Safe |
| Ashby | Public API explicitly provided | 🟢 Safe |

### 3.4 AI-Specific Regulations

| Regulation | Status |
|------------|--------|
| EU AI Act (2025) | Classifies career recommendation as "high-risk" if it affects access to employment |
| NYC Local Law 144 | Requires bias audits for automated employment decision tools |
| Colorado AI Act | Similar to EU AI Act, takes effect 2026 |

**Required:** Bias audit documentation, transparency reports, opt-out mechanisms for AI decisions.

---

## 4. Technical Blockers & Hard Problems

### 4.1 Resume Parsing Accuracy

| Challenge | Detail |
|-----------|--------|
| Format diversity | PDF, DOCX, RTF, HTML, plain text — each with sub-variations |
| Layout parsing | Two-column resumes, tables, graphics, headers/footers |
| Multilingual resumes | CareerPilot may serve non-English users |
| Accuracy requirement | A single misparsed skill or job title cascades into bad matching |

**Recommendation:** Don't build from scratch. Use established libraries (resume-parser, pyresparser) or commercial APIs (LoopCV, Affinda, HireAbility). Build a validation layer on top.

### 4.2 Embedding Similarity for Job Matching

| Challenge | Detail |
|-----------|--------|
| Model selection | BAAI/bge-small is fast but less accurate; nomic-embed is better but slower |
| Dimension mismatch | Switching models means re-embedding everything |
| Cold start | New jobs have no click data to reinforce matching |
| Threshold calibration | What similarity score = "good match"? Varies by role |

### 4.3 Real-Time Search at Scale

| Challenge | Detail |
|-----------|--------|
| Search latency | User expects results in <2 seconds |
| Index freshness | New jobs must appear within minutes, not hours |
| Filtering complexity | Skills + location + salary + remote + experience + keywords = complex query |
| ChromaDB/Qdrant limits | Vector DBs handle similarity search well but struggle with combined scalar + vector filtering |

### 4.4 Application Autofill

| Challenge | Detail |
|-----------|--------|
| Form diversity | Every ATS has different form fields, names, and structures |
| Dynamic forms | Greenhouse custom questions vary per job |
| File uploads | Resume uploads need proper MIME type handling |
| Captcha on submit | Can't bypass these legally |
| User consent | Must confirm before submission |

---

## 5. Required Accounts, API Keys & Secrets

### 5.1 Authentication & Storage

| Service | Account Type | Free Tier | Secrets Required |
|---------|-------------|-----------|-----------------|
| **Supabase** | Cloud project | 500MB DB, 1GB storage, 50K MAU | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` |
| **Supabase Auth** | Included | Social OAuth providers, MFA | OAuth client IDs/secrets for Google, GitHub, etc. |

### 5.2 Database & Caching

| Service | Account Type | Free Tier | Secrets Required |
|---------|-------------|-----------|-----------------|
| **PostgreSQL** | Managed (Supabase) or self-hosted | 500MB on Supabase free | `DATABASE_URL` |
| **Redis** | Managed (Upstash) or self-hosted | 10K commands/day on Upstash | `REDIS_URL` |
| **ChromaDB** | Self-hosted only | N/A | No auth in OSS version; use network isolation |

### 5.3 LLM Providers (Choose One or More)

| Provider | Free Tier | Paid Pricing | Secrets Required |
|----------|-----------|-------------|-----------------|
| **OpenAI** | None (pay-as-you-go) | GPT-4o: $2.50/$10 per 1M tokens | `OPENAI_API_KEY` |
| **Anthropic** | None (pay-as-you-go) | Claude Sonnet: $3/$15 per 1M tokens | `ANTHROPIC_API_KEY` |
| **Google Gemini** | 1,500 RPD (Flash only) | Flash: $0.50/$3 per 1M tokens | `GOOGLE_API_KEY` |
| **Ollama** | Free (self-hosted) | Hardware cost only | No API key; needs GPU server |
| **LiteLLM** | Open-source proxy | N/A | Routes to above providers |

**Recommendation:** Start with Gemini Flash (cheapest + free tier) for scoring/summarization. Use GPT-4o or Claude only for resume tailoring and cover letters where quality matters most.

### 5.4 Search & Job Aggregation

| Service | Account Type | Free Tier | Secrets Required |
|---------|-------------|-----------|-----------------|
| **Google Custom Search** | ⚠️ Closed to new customers (2025) | N/A | `GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_CX` |
| **Serper.dev** | API key | 2,500 free queries | `SERPER_API_KEY` |
| **JSearch (RapidAPI)** | RapidAPI account | 500 req/month free | `RAPIDAPI_KEY`, `JSEARCH_HOST` |
| **Adzuna** | API key | Free tier available | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` |
| **Remotive** | API key | Free | `REMOTIVE_API_KEY` |
| **LoopCV** | API key | Free tier + paid | `LOOPCV_API_KEY` |
| **Apify** | API token | $5 free credits/month | `APIFY_API_TOKEN` |

**Recommendation:** Use Serper.dev for Google search + JSearch + Adzuna + Remotive for initial coverage. Add LoopCV or Apify for broader ATS coverage.

### 5.5 Notification Services

| Service | Account Type | Free Tier | Secrets Required |
|---------|-------------|-----------|-----------------|
| **Resend** (Email) | API key | 3,000 emails/month | `RESEND_API_KEY` |
| **Telegram Bot** | BotFather | Free | `TELEGRAM_BOT_TOKEN` |
| **Slack** | App + Bot Token | Free | `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET` |
| **Web Push** | VAPID keys | Free | `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` |

### 5.6 Infrastructure

| Service | Account Type | Free Tier | Secrets Required |
|---------|-------------|-----------|-----------------|
| **Docker Hub** | Account | Free for public images | `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` |
| **GitHub** | Repository | Free | `GITHUB_TOKEN` (for CI/CD) |
| **Prometheus + Grafana** | Self-hosted | Free | No external secrets |

### 5.7 Browser Extension

| Requirement | Detail |
|-------------|--------|
| **Chrome Web Store Developer Account** | One-time $5 registration fee |
| **Extension signing key** | Must be kept secure for updates |
| **Manifest V3** | Required for Chrome Web Store listing |
| **Firefox Add-on Developer Account** | Free |
| **Domain verification** | Required for `externally_connectable` in manifest |

---

## 6. Cost Estimation at Scale

### Monthly Costs at Different User Tiers

| Cost Category | 100 Users | 1,000 Users | 10,000 Users |
|---------------|-----------|-------------|--------------|
| **LLM API (Gemini Flash)** | $9 | $90 | $900 |
| **LLM API (GPT-4o for premium features)** | $5 | $50 | $500 |
| **Job search APIs (Serper + JSearch)** | $10 | $50 | $300 |
| **Supabase (Pro plan)** | $0 (free) | $25 | $25 |
| **Redis (Upstash)** | $0 (free) | $10 | $50 |
| **Server hosting** | $20 | $50 | $200 |
| **Email (Resend)** | $0 (free) | $0 (free) | $20 |
| **Domain + SSL** | $1 | $1 | $1 |
| **Embedding storage (ChromaDB)** | $0 (self-hosted) | $0 | $20 (disk) |
| **Monitoring (Grafana Cloud)** | $0 (free) | $0 (free) | $29 |
| **TOTAL** | **~$45/mo** | **~$276/mo** | **~$2,020/mo** |

### Revenue Required for Break-Even

| Model | At 1,000 users | At 10,000 users |
|-------|----------------|-----------------|
| Free tier + Premium ($10/mo, 10% conversion) | $1,000/mo ✅ | $10,000/mo ✅ |
| Freemium ($5/mo, 20% conversion) | $1,000/mo ✅ | $10,000/mo ✅ |

**Verdict:** The unit economics work if you can convert 10-20% of users to paid plans at $5-10/month.

---

## 7. Recommended Enhancements

### 7.1 High-Value Enhancements (Add to Roadmap)

| Enhancement | Why | Phase |
|-------------|-----|-------|
| **Salary Estimation Engine** | Most job postings lack salary data; users desperately need this | Phase 5 |
| **Skills Gap Analysis** | "You match 72%, but you're missing X, Y, Z skills" | Phase 5 |
| **Career Path Mapping** | "From Senior Dev → Staff Engineer, here's what you need" | Phase 9 |
| **Application Deadline Tracking** | "This job closes in 2 days" — creates urgency | Phase 4 |
| **Multi-language Support** | Huge market in non-English regions; India, EU, LatAm | Phase 6 |
| **Mobile-Responsive Dashboard** | Many users will access on mobile | Phase 6 |
| **Chrome + Firefox Extension** | Firefox still has significant developer market share | Phase 8 |
| **Job Alert Scheduling** | Daily/weekly digest instead of real-time notifications | Phase 6 |

### 7.2 Architectural Enhancements (Add to Design)

| Enhancement | Why |
|-------------|-----|
| **Event-Driven Architecture** | Decouple agents via message queue (Redis Streams) instead of direct HTTP calls |
| **Caching Layer for LLM Responses** | Similar job descriptions produce similar match scores; cache with content-hash key |
| **Connector Health Dashboard** | APIs go down; need real-time visibility into which connectors are working |
| **Rate Limit Budget per Connector** | Each API has different limits; need a token-bucket per source |
| **User Feedback Loop** | "Was this match helpful?" — feeds back into ranking model |
| **Explainable AI** | Every match score must have a human-readable explanation (not just a number) |
| **Graceful Degradation** | If LLM is down, still show basic keyword matching + ATS jobs |
| **API Gateway** | Rate limiting, auth, and request routing before hitting backend services |

### 7.3 Nice-to-Have Enhancements (Future)

| Enhancement | Why |
|-------------|-----|
| **Networking Suggestions** | "You have 3 connections at this company" |
| **Interview Scheduling** | Calendly-like integration |
| **Referral Request Templates** | "Ask your connection for a referral" |
| **Job Market Analytics** | "React demand is up 15% this quarter in your area" |
| **Resume A/B Testing** | Generate two versions, track which gets more responses |
| **Application Follow-up Reminders** | "You applied 5 days ago, consider following up" |
| **GitLab/Bitbucket Portfolio Import** | Auto-extract project skills from code repos |
| **Open Source Contribution Analysis** | Weight GitHub activity in profile scoring |

---

## 8. Architecture Reconsiderations

### 8.1 Monorepo: Keep or Split?

**Current plan:** Monorepo with `apps/`, `services/`, `agents/`, `connectors/`, `packages/`

| Option | Pros | Cons |
|--------|------|------|
| **Monorepo** (current) | Shared types, atomic commits, easier refactoring | Complex CI, deployment coupling, large repo |
| **Polyrepo** | Independent deployment, clear ownership | Dependency management hell, type drift |

**Recommendation:** ✅ **Keep monorepo** but use Turborepo or Nx for build orchestration. Deploy services independently via Docker.

### 8.2 Agent Communication Pattern

**Current plan:** Implicit (agents call each other)

| Option | Pros | Cons |
|--------|------|------|
| **Direct HTTP calls** | Simple, low latency | Tight coupling, hard to retry/debug |
| **Redis Streams / Event bus** | Decoupled, replayable, observable | Eventual consistency, more complex |
| **Celery task queue** | Simple, built-in retry | Tight coupling to Celery, harder to test |

**Recommendation:** ✅ **Redis Streams for inter-agent communication.** Each agent subscribes to relevant streams. This gives replayability, observability, and decoupling.

### 8.3 Embedding Strategy

**Current plan:** BAAI/bge-small or nomic-embed

| Model | Dimensions | Speed | Quality | Cost |
|-------|-----------|-------|---------|------|
| bge-small-en-v1.5 | 384 | Fast | Good | Free (self-hosted) |
| nomic-embed-text-v1.5 | 768 | Medium | Better | Free (self-hosted) |
| Gemini Embedding | 768 | Fast | Best | $0.20/1M tokens |
| OpenAI text-embedding-3-small | 1536 | Fast | Good | $0.02/1M tokens |

**Recommendation:** ✅ **Start with nomic-embed-text (self-hosted via Ollama).** It's free, high-quality, and 768 dimensions is a good balance. If cost isn't a concern later, switch to OpenAI's embedding-3-small for the best quality/cost ratio.

### 8.4 Vector Database Choice

| Option | Pros | Cons |
|--------|------|------|
| **ChromaDB** | Easy setup, Python-native, good for prototyping | Not production-hardened, limited filtering |
| **Qdrant** | Production-grade, rich filtering, horizontal scaling | More complex setup |
| **pgvector** (PostgreSQL extension) | No new infrastructure, ACID transactions | Slower than dedicated vector DBs at scale |

**Recommendation:** ✅ **Start with pgvector on Supabase's PostgreSQL.** One less service to manage. If performance becomes an issue, migrate to Qdrant.

---

## 9. Connector-by-Connector Feasibility

### Tier 1: Ready to Implement (Public APIs)

| Connector | API Endpoint | Auth | Data Quality | Effort |
|-----------|-------------|------|-------------|--------|
| Greenhouse | `boards-api.greenhouse.io/v1/boards/{token}/jobs` | None | Excellent | Low |
| Lever | `api.lever.co/v0/postings/{site}` | None | Excellent | Low |
| Ashby | `api.ashbyhq.com/posting-api/job-board/{name}` | None | Excellent + salary | Low |
| Workable | `www.workable.com/api/accounts/{subdomain}` | None | Good | Low |
| Recruitee | `{company}.recruitee.com/api/offers/` | None | Good | Low |
| Personio | `{company}.jobs.personio.de/xml` | None | Good (XML) | Medium |

### Tier 2: Requires Scraping (No Public API)

| Connector | Method | Difficulty | Legal Risk |
|-----------|--------|------------|------------|
| Workday | Scrape career pages + sitemap.xml | High (JS-rendered) | 🟢 Low (public pages) |
| iCIMS | Scrape career pages | High (complex HTML) | 🟢 Low (public pages) |
| SAP SuccessFactors | CSRF-protected internal API + HTML parsing | Very High | 🟡 Medium (CSRF token extraction) |
| Oracle Taleo | Scrape career pages | High (legacy HTML) | 🟢 Low (public pages) |
| SmartRecruiters | Partial API + career page scraping | Medium | 🟢 Low |

### Tier 3: Use Aggregator APIs

| Source | Recommended API | Cost |
|--------|----------------|------|
| Google Search results for jobs | Serper.dev | $50/50K queries |
| LinkedIn (no direct access) | LoopCV aggregator | Free tier + paid |
| Indeed (no direct access) | JSearch (RapidAPI) | Free tier + $0.01/query |
| Glassdoor (no direct access) | LoopCV aggregator | Included |
| Adzuna | Direct API (free) | Free |
| Remotive | Direct API (free) | Free |
| RemoteOK | Direct API (free) | Free |

### Recommended Data Source Strategy

```
┌─────────────────────────────────────────────────────┐
│                  PRIMARY SOURCES                     │
│  (Free, direct API access, no legal risk)           │
│                                                     │
│  Greenhouse ──── Lever ──── Ashby                   │
│  Workable ───── Recruitee ── Personio               │
│  Adzuna ─────── Remotive ─── RemoteOK               │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              SECONDARY SOURCES                       │
│  (Aggregator APIs, low cost, broad coverage)        │
│                                                     │
│  JSearch (RapidAPI) ── LoopCV ── Serper.dev         │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              TERTIARY SOURCES                        │
│  (Scraping required, high effort, medium risk)      │
│                                                     │
│  Workday ── iCIMS ── SAP SF ── Oracle ── SR        │
└─────────────────────────────────────────────────────┘
```

---

## 10. Mitigation Strategies

### 10.1 Legal Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| CFAA violation | **Only scrape public pages. Never use fake accounts. Never bypass CAPTCHAs.** |
| TOS violations | **Don't scrape platforms with explicit anti-scraping TOS (LinkedIn, Indeed). Use aggregator APIs instead.** |
| GDPR compliance | **Implement right-to-deletion. Store EU data in EU region. Add data processing agreements.** |
| AI bias | **Document model decisions. Add fairness checks. Allow users to override AI recommendations.** |
| Data retention | **Auto-delete job postings older than 30 days. User resumes deleted on account deletion.** |

### 10.2 Cost Mitigation

| Risk | Mitigation |
|------|-----------|
| LLM API costs | **Tiered model strategy: Flash for scoring, GPT-4o only for premium features. Cache aggressively.** |
| Search API costs | **Cache search results for 1 hour. Deduplicate before re-querying.** |
| Embedding costs | **Self-host nomic-embed via Ollama. Zero marginal cost.** |
| Storage costs | **Compress old job data. Archive to S3 after 30 days.** |

### 10.3 Technical Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Resume parsing errors | **Use commercial parser for initial extraction + human review step** |
| Job deduplication errors | **Multi-signal dedup: title similarity + location + company + date + embedding** |
| Browser extension breakage | **Integration tests against live ATS pages. Weekly compatibility checks.** |
| Service downtime | **Health checks + circuit breakers + graceful degradation** |
| LLM hallucination in resumes | **Strict prompt engineering: "NEVER fabricate experience." Human review before export.** |

---

## 11. Go / No-Go Decision Matrix

| Decision Point | Status | Notes |
|---------------|--------|-------|
| Legal: Can we scrape job data? | ✅ GO | Public ATS APIs + aggregator APIs provide sufficient coverage without CFAA risk |
| Legal: Can we use AI for career decisions? | ⚠️ GO WITH CAUTION | Must implement transparency, opt-out, and bias documentation |
| Technical: Can we parse resumes accurately? | ✅ GO | Use established libraries + validation |
| Technical: Can we match jobs semantically? | ✅ GO | Embeddings + LLM reasoning is proven |
| Technical: Can we build the browser extension? | ✅ GO | MV3 supports detection + autofill assistance |
| Financial: Is it cost-viable? | ✅ GO | $0.09-1.73/user/month with tiered model strategy |
| Coverage: Can we get enough job listings? | ⚠️ GO WITH GAPS | No LinkedIn/Indeed direct access; aggregator APIs partially fill this |
| Compliance: Can we meet GDPR? | ✅ GO | Supabase supports EU regions; implement deletion APIs |

### Overall Verdict: ✅ **GO — with the following conditions:**

1. **Do NOT scrape LinkedIn or Indeed directly.** Use aggregator APIs.
2. **Implement tiered LLM strategy from day one.**
3. **Start with Tier 1 connectors only (Greenhouse, Lever, Ashby, Workable).** Add Tier 2 later.
4. **Add a "Data Sources" transparency page** showing where jobs come from.
5. **Implement bias audit documentation** before any public launch.
6. **Budget $200-300/month for API costs** during development.

---

## 12. Recommended Phase 0 Tasks (Before Phase 1)

Before we write production code, we should complete these tasks:

| # | Task | Why | Time |
|---|------|-----|------|
| 1 | **Register all required accounts** (Supabase, Serper.dev, JSearch, Adzuna, Gemini API, Resend) | Can't develop without API keys | 2 hours |
| 2 | **Create environment variable template** (.env.example) | Security baseline | 30 min |
| 3 | **Test Greenhouse API with 3 companies** (e.g., Stripe, Airbnb, Notion) | Validate data quality and structure | 1 hour |
| 4 | **Test Lever API with 3 companies** | Validate data quality | 1 hour |
| 5 | **Test Serper.dev for job search queries** | Validate Google search coverage | 1 hour |
| 6 | **Test resume parsing with 5 sample resumes** | Validate parser accuracy | 2 hours |
| 7 | **Draft privacy policy and TOS** | Legal compliance baseline | 4 hours |
| 8 | **Define subscription tiers and pricing** | Product strategy | 2 hours |
| 9 | **Create detailed data flow diagrams** | Architecture clarity | 3 hours |
| 10 | **Set up development environment** (Docker, VS Code config, linting) | Engineering velocity | 2 hours |

---

## Appendix A: Alternative Data Sources to Consider

| Source | Type | Coverage | Cost |
|--------|------|----------|------|
| **JSearch (RapidAPI)** | Aggregator API | LinkedIn, Indeed, Glassdoor, ZipRecruiter | Free 500/mo, then $0.01/query |
| **Adzuna** | Job board API | UK, US, EU, India, Australia | Free tier available |
| **Remotive** | Remote jobs API | Remote-only jobs globally | Free |
| **RemoteOK** | Remote jobs API | Remote tech jobs | Free |
| **LoopCV** | Aggregator + resume parser | 30+ sources | Free tier + paid |
| **Apify** | Scraping platform | Any website | $5 free credits/mo |
| **Arbeitnow** | Job board API | EU-focused | Free |
| **HigherEdJobs** | Education sector | US universities | Scrape only |
| **Wellfound (AngelList)** | Startup jobs | Startups | No API; scrape only |

## Appendix B: Competitor Landscape

| Competitor | Features | Pricing | Differentiator |
|-----------|----------|---------|---------------|
| **LoopCV** | Job search, auto-apply | €14.99/mo | Auto-apply focus |
| **Teal HQ** | Job tracker, resume builder | $9/week | Resume focus |
| **Sonara** | AI job matching | $19.99/mo | Matching focus |
| **Jobscan** | Resume optimization | $49.95/mo | ATS optimization |
| **Kickresume** | Resume + cover letter | $5/mo | Template focus |
| **Careerflow** | AI career copilot | Free + $10/mo | Chrome extension |

**CareerPilot's unique value:** End-to-end career AI — from search to offer, with multi-agent intelligence, transparent matching, and user control.

---

## Appendix C: Key Design Decisions to Confirm

Before starting Phase 1, confirm these decisions:

1. **Data sourcing strategy:** Aggregator-first (recommended) or scrape-first?
2. **LLM provider:** Gemini Flash primary + GPT-4o for premium? Or Ollama-only (self-hosted)?
3. **Vector DB:** pgvector (simpler) or Qdrant (more scalable)?
4. **Background job system:** Celery (Python-native, more complex) or Dramatiq (simpler, less mature)?
5. **Monorepo tooling:** Turborepo or Nx?
6. **Deployment target:** Self-hosted Docker or cloud-managed (Fly.io, Railway, AWS)?
7. **Browser extension scope:** Chrome-only or Chrome + Firefox from day one?
8. **Subscription model:** Freemium or free-only for initial launch?
9. **Geographic focus:** Global or India-first (given your location)?
10. **Open-source or proprietary codebase?**

---

*This document should be reviewed and approved before any implementation begins. Decisions made here will fundamentally shape the architecture and feasibility of the entire project.*
