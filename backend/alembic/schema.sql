-- CareerPilot AI — Database Schema (SQLite)
-- Personal AEM Career Tool
-- Run: sqlite3 data/careerpilot.db < schema.sql

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- Your profile (single row — you're the only user)
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY DEFAULT 1,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    location TEXT DEFAULT 'Hyderabad, India',
    summary TEXT,
    skills TEXT,                    -- JSON array: ["AEM", "Java", "Sling", ...]
    experience_years REAL,
    current_role TEXT DEFAULT 'AEM Developer',
    target_role TEXT DEFAULT 'AEM Architect',
    expected_salary_min INTEGER DEFAULT 2000000,    -- 20 LPA in INR
    expected_salary_max INTEGER DEFAULT 3500000,    -- 35 LPA in INR
    preferred_locations TEXT,       -- JSON array: ["Hyderabad", "Remote", "Bangalore"]
    remote_preference TEXT DEFAULT 'any',  -- 'remote', 'hybrid', 'onsite', 'any'
    notice_period TEXT DEFAULT '60_days',
    resume_text TEXT,               -- Parsed resume full text
    resume_file_path TEXT,          -- Path to latest resume file
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Companies
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    website TEXT,
    industry TEXT,
    size TEXT,                      -- 'startup', 'mid', 'large', 'enterprise'
    location TEXT,
    description TEXT,
    research_notes TEXT,            -- AI-generated research summary
    is_aem_hirer BOOLEAN DEFAULT FALSE,  -- Known to hire AEM devs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name)
);

-- Jobs (from all sources, deduplicated)
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,           -- 'jsearch', 'adzuna', 'greenhouse', 'lever', 'ashby', 'manual'
    source_id TEXT,                 -- ID from the source
    source_url TEXT,                -- URL to original listing
    title TEXT NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    company_name TEXT NOT NULL,
    location TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT DEFAULT 'INR',
    salary_period TEXT DEFAULT 'yearly',  -- 'yearly', 'monthly'
    job_type TEXT,                  -- 'full_time', 'part_time', 'contract', 'internship'
    is_remote BOOLEAN DEFAULT FALSE,
    description TEXT,
    requirements TEXT,              -- Extracted requirements
    skills_required TEXT,           -- JSON array of skills
    experience_required TEXT,
    posted_date TIMESTAMP,
    expiry_date TIMESTAMP,
    match_score REAL,              -- AI score 0-100
    match_strengths TEXT,          -- JSON array
    match_weaknesses TEXT,         -- JSON array
    match_recommendations TEXT,    -- JSON array
    embedding_id TEXT,             -- ChromaDB document ID
    is_active BOOLEAN DEFAULT TRUE,
    canonical_job_id INTEGER,      -- Links duplicate jobs together
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, source_id)
);

-- Create FTS index for job search
CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts USING fts5(
    title, company_name, location, description, skills_required,
    content=jobs, content_rowid=id
);

-- Applications (your tracking sheet)
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'not_applied',
    applied_at TIMESTAMP,
    resume_version TEXT,           -- Which resume version was sent
    cover_letter_path TEXT,        -- Path to cover letter file
    notes TEXT,                    -- Your personal notes
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    next_followup DATE,
    followup_count INTEGER DEFAULT 0,
    response_notes TEXT,           -- Notes from recruiter response
    response_type TEXT,            -- 'auto_reply', 'recruiter_email', 'interview_invite', 'rejection', 'offer'
    response_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id)
);

-- Cover Letters (generated)
CREATE TABLE IF NOT EXISTS cover_letters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    file_path TEXT,
    model_used TEXT,               -- 'ollama:qwen3:8b' or 'gemini:flash'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interview Prep
CREATE TABLE IF NOT EXISTS interview_prep (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id),
    questions TEXT NOT NULL,       -- JSON array of questions + suggested answers
    tips TEXT,                     -- JSON: preparation tips
    salary_negotiation_tips TEXT,
    model_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search History
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    filters TEXT,                  -- JSON: location, salary, remote, etc.
    results_count INTEGER,
    source TEXT,                   -- Which connector found the results
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity Log
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,          -- 'job_found', 'job_scored', 'application_sent', etc.
    entity_type TEXT,              -- 'job', 'application', 'resume', 'cover_letter'
    entity_id INTEGER,
    details TEXT,                  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Settings
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    telegram_chat_id TEXT,
    telegram_bot_token TEXT,
    default_search_queries TEXT,   -- JSON array of search queries
    default_location TEXT DEFAULT 'Hyderabad, India',
    min_salary INTEGER DEFAULT 2000000,
    remote_only BOOLEAN DEFAULT FALSE,
    job_alerts_enabled BOOLEAN DEFAULT TRUE,
    alert_frequency TEXT DEFAULT 'daily',
    auto_score_jobs BOOLEAN DEFAULT TRUE,
    llm_provider TEXT DEFAULT 'ollama',  -- 'ollama' or 'gemini'
    google_sheets_sync BOOLEAN DEFAULT FALSE,
    google_sheets_spreadsheet_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default profile for AEM Developer
INSERT OR IGNORE INTO profile (id, full_name, current_role, target_role, location,
    skills, experience_years, remote_preference, notice_period,
    expected_salary_min, expected_salary_max, preferred_locations)
VALUES (1, 'Your Name', 'AEM Developer', 'AEM Architect', 'Hyderabad, India',
    '["AEM", "Adobe Experience Manager", "EDS", "Edge Delivery Services", "Java", "Sling", "OSGi", "HTL", "AEM as Cloud Service", "Maven", "CI/CD"]',
    8, 'any', '60_days', 2000000, 3500000,
    '["Hyderabad", "Remote", "Bangalore", "Pune"]');

-- Insert default settings
INSERT OR IGNORE INTO settings (id, default_search_queries, default_location, alert_frequency)
VALUES (1, '["AEM developer", "Adobe Experience Manager developer", "AEM architect", "EDS developer", "AEM Sites developer"]',
    'Hyderabad, India', 'daily');

-- Insert known AEM hiring companies
INSERT OR IGNORE INTO companies (name, industry, size, is_aem_hirer) VALUES
    ('Accenture', 'Consulting', 'enterprise', 1),
    ('Cognizant', 'Consulting', 'enterprise', 1),
    ('Wipro', 'IT Services', 'enterprise', 1),
    ('TCS', 'IT Services', 'enterprise', 1),
    ('Capgemini', 'Consulting', 'enterprise', 1),
    ('Adobe', 'Technology', 'large', 1),
    ('IBM', 'Technology', 'enterprise', 1),
    ('Deloitte', 'Consulting', 'enterprise', 1),
    ('Infosys', 'IT Services', 'enterprise', 1),
    ('HCL Technologies', 'IT Services', 'enterprise', 1),
    ('Publicis Sapient', 'Digital Agency', 'large', 1),
    ('EPAM Systems', 'Technology', 'large', 1),
    ('Tech Mahindra', 'IT Services', 'enterprise', 1),
    ('Virtusa', 'IT Services', 'large', 1),
    ('Atos', 'IT Services', 'enterprise', 1),
    ('SAP', 'Technology', 'enterprise', 1),
    ('Oracle', 'Technology', 'enterprise', 1),
    ('Mindtree', 'IT Services', 'large', 1),
    ('Mphasis', 'IT Services', 'large', 1),
    ('Hexaware', 'IT Services', 'large', 1);

-- Create useful indexes
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_posted ON jobs(posted_date DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(is_remote);
CREATE INDEX IF NOT EXISTS idx_jobs_canonical ON jobs(canonical_job_id);

CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_followup ON applications(next_followup);

CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_log(action);
CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_companies_aem ON companies(is_aem_hirer);
