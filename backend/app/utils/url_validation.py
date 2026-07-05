"""
CareerPilot AI — URL Validation Utility
Filters out fake, placeholder, and non-genuine job URLs
so that the "Apply" button only shows for real job listings.

Examples of URLs we REJECT:
  - https://example.com/...
  - http://example.org/...
  - https://placeholder.com/...
  - https://test.com/...
  - https://localhost/...
  - https://127.0.0.1/...
  - about:blank
  - javascript:...
  - Empty strings
  - URLs with no TLD (e.g. "not-a-url")

Examples of URLs we ACCEPT:
  - https://www.linkedin.com/jobs/view/12345
  - https://in.indeed.com/viewjob?jk=abc
  - https://www.naukri.com/jobapi/...
  - https://careers.accenture.com/...
  - https://jobs.smartrecruiters.com/...
  - https://www.glassdoor.com/...
"""

import re
from urllib.parse import urlparse
from typing import Optional


# ─── Domains that are NEVER real job listing URLs ─────────────────────────────

FAKE_DOMAINS = {
    # Placeholder/example domains (RFC 2606 + common patterns)
    "example.com", "example.org", "example.net",
    "www.example.com", "www.example.org", "www.example.net",
    "placeholder.com", "placeholder.org",
    "test.com", "test.org", "test.net",
    "sample.com", "sample.org",
    "fake.com", "fake.org",
    "dummy.com", "dummy.org",
    "localhost", "localhost.com",
    "yourdomain.com", "yourcompany.com",
    "company.com", "domain.com",
    "mysite.com", "website.com",
    # Generic/template domains often seen in API test data
    "apply.example.com", "jobs.example.com",
    "careers.example.com",
}

# ─── URL pattern red flags ────────────────────────────────────────────────────

FAKE_PATTERNS = [
    r'^https?://(www\.)?example\.',
    r'^https?://(www\.)?placeholder\.',
    r'^https?://(www\.)?test\.',
    r'^https?://(www\.)?sample\.',
    r'^https?://(www\.)?fake\.',
    r'^https?://(www\.)?dummy\.',
    r'^https?://(www\.)?your(domain|company|site)',
    r'^https?://localhost',
    r'^https?://127\.',
    r'^https?://10\.',
    r'^https?://192\.168\.',
    r'^https?://172\.(1[6-9]|2[0-9]|3[01])\.',
    r'^about:',
    r'^javascript:',
    r'^data:',
    r'^mailto:',
    r'^file:',
    r'^ftp:',
]

# ─── Known legitimate job board domains ───────────────────────────────────────

LEGITIMATE_JOB_DOMAINS = {
    # Major global job boards
    "linkedin.com", "www.linkedin.com",
    "indeed.com", "in.indeed.com", "www.indeed.com",
    "glassdoor.com", "www.glassdoor.com",
    "naukri.com", "www.naukri.com",
    "monster.com", "www.monster.com", "monsterindia.com",
    "ziprecruiter.com", "www.ziprecruiter.com",
    "simplyhired.com", "www.simplyhired.com",
    "careerbuilder.com", "www.careerbuilder.com",
    "dice.com", "www.dice.com",
    "angel.co", "wellfound.com", "www.wellfound.com",
    # Company career pages (common ATS platforms)
    "smartrecruiters.com", "jobs.smartrecruiters.com",
    "greenhouse.io", "boards.greenhouse.io",
    "lever.co", "jobs.lever.co",
    "icims.com", "careers.icims.com",
    "taleo.net", "careers.taleo.net",
    "workday.com", "myworkdayjobs.com", "wd1.myworkday.com",
    "brassring.com", "krb-sjobs.brassring.com",
    "jobvite.com", "careers.jobvite.com",
    "ultimate.com", "careers.ultimatesoftware.com",
    "successfactors.com", "careers.successfactors.com",
    "recruitee.com", "careers.recruitee.com",
    "ashbyhq.com", "jobs.ashbyhq.com",
    # Indian job boards
    "freshersworld.com", "www.freshersworld.com",
    "shine.com", "www.shine.com",
    "timesjobs.com", "www.timesjobs.com",
    "foundit.in", "www.foundit.in",
    "internshala.com", "internshala.com",
    "cutshort.io", "cutshort.io",
    "hirect.in", "hirect.in",
    # Tech-specific
    "wellfound.com", "ycombinator.com",
    "remote.co", "weworkremotely.com",
    "remoteok.com", "remotive.com",
    # Direct company career pages (top AEM employers)
    "careers.accenture.com", "accenture.com",
    "careers.infosys.com", "infosys.com",
    "careers.wipro.com", "wipro.com",
    "careers.tcs.com", "tcs.com",
    "careers.cognizant.com", "cognizant.com",
    "careers.capgemini.com", "capgemini.com",
    "careers.ibm.com", "ibm.com",
    "careers.deloitte.com", "deloitte.com",
    "careers.adobe.com", "adobe.com",
    "careers.publicissapient.com", "publicissapient.com",
    "careers.hcltech.com", "hcltech.com",
    "careers.techmahindra.com", "techmahindra.com",
}

# Compile fake patterns regex once
_FAKE_REGEX = re.compile('|'.join(FAKE_PATTERNS), re.IGNORECASE)


def is_valid_job_url(url: Optional[str]) -> bool:
    """
    Validate if a URL is a genuine job listing URL.
    
    Returns True if the URL is legitimate, False if it's fake/placeholder.
    
    A URL is considered INVALID if:
    1. It's None, empty, or whitespace
    2. It matches a known fake domain (example.com, placeholder.com, etc.)
    3. It matches a fake URL pattern (localhost, private IPs, about:blank)
    4. It has no valid TLD
    5. It's not an http/https URL
    """
    if not url:
        return False
    
    url = url.strip()
    
    if not url:
        return False
    
    # Must start with http:// or https://
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Check against fake patterns
    if _FAKE_REGEX.match(url):
        return False
    
    # Parse the URL
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    
    hostname = (parsed.hostname or '').lower()
    
    if not hostname:
        return False
    
    # Check against known fake domains
    if hostname in FAKE_DOMAINS:
        return False
    
    # Check if hostname ends with a known fake domain
    for fake in FAKE_DOMAINS:
        if hostname.endswith('.' + fake) or hostname == fake:
            return False
    
    # Must have a valid TLD (at least 2 chars after last dot)
    parts = hostname.split('.')
    if len(parts) < 2:
        return False
    
    tld = parts[-1].lower()
    if len(tld) < 2:
        return False
    
    # Reject numeric-only TLDs (IP addresses)
    if tld.isdigit():
        return False
    
    # Hostname must have at least one alphabetic character
    if not any(c.isalpha() for c in hostname):
        return False
    
    return True


def is_legitimate_job_domain(url: Optional[str]) -> bool:
    """
    Check if the URL belongs to a known legitimate job board or ATS.
    This is a STRONGER check than is_valid_job_url — it confirms the
    domain is a well-known job source.
    
    Returns:
      True  — domain is in our known-good list
      False — domain is unknown (not necessarily bad, just not verified)
    """
    if not is_valid_job_url(url):
        return False
    
    try:
        parsed = urlparse(url.strip())
        hostname = (parsed.hostname or '').lower()
    except Exception:
        return False
    
    # Check exact match
    if hostname in LEGITIMATE_JOB_DOMAINS:
        return True
    
    # Check parent domain match (e.g. careers.accenture.com → accenture.com)
    for legit in LEGITIMATE_JOB_DOMAINS:
        if hostname == legit or hostname.endswith('.' + legit):
            return True
    
    return False


def sanitize_source_url(url: Optional[str]) -> Optional[str]:
    """
    Clean up and validate a source URL.
    Returns the URL if valid, or None if fake/invalid.
    
    Use this in connectors when normalizing job data.
    """
    if not url:
        return None
    
    url = url.strip()
    
    if not is_valid_job_url(url):
        return None
    
    return url


def get_apply_label(url: Optional[str]) -> str:
    """
    Get a human-readable label for the apply button based on the URL domain.
    Returns something like "LinkedIn", "Naukri", "Indeed", "Company Site", etc.
    """
    if not is_valid_job_url(url):
        return ""
    
    try:
        parsed = urlparse(url.strip())
        hostname = (parsed.hostname or '').lower()
    except Exception:
        return "Apply"
    
    # Known domain labels
    domain_labels = {
        "linkedin.com": "LinkedIn",
        "indeed.com": "Indeed",
        "glassdoor.com": "Glassdoor",
        "naukri.com": "Naukri",
        "monster.com": "Monster",
        "ziprecruiter.com": "ZipRecruiter",
        "simplyhired.com": "SimplyHired",
        "careerbuilder.com": "CareerBuilder",
        "dice.com": "Dice",
        "wellfound.com": "Wellfound",
        "angel.co": "AngelList",
        "smartrecruiters.com": "SmartRecruiters",
        "greenhouse.io": "Company Site",
        "lever.co": "Company Site",
        "icims.com": "Company Site",
        "workday.com": "Company Site",
        "myworkdayjobs.com": "Company Site",
        "weworkremotely.com": "WeWorkRemotely",
        "remoteok.com": "RemoteOK",
        "freshersworld.com": "Freshersworld",
        "shine.com": "Shine",
        "timesjobs.com": "TimesJobs",
        "foundit.in": "Foundit",
        "internshala.com": "Internshala",
        "cutshort.io": "Cutshort",
        "adobe.com": "Adobe Careers",
        "accenture.com": "Accenture Careers",
        "infosys.com": "Infosys Careers",
        "wipro.com": "Wipro Careers",
        "tcs.com": "TCS Careers",
        "cognizant.com": "Cognizant Careers",
        "capgemini.com": "Capgemini Careers",
        "ibm.com": "IBM Careers",
        "deloitte.com": "Deloitte Careers",
        "hcltech.com": "HCL Careers",
        "techmahindra.com": "Tech Mahindra Careers",
        "publicissapient.com": "Publicis Sapient",
    }
    
    # Check exact match first
    if hostname in domain_labels:
        return domain_labels[hostname]
    
    # Check parent domain
    for domain, label in domain_labels.items():
        if hostname.endswith('.' + domain):
            return label
    
    # Generic: extract company-like name from subdomain
    # e.g. careers.company.com → "Company"
    parts = hostname.split('.')
    if len(parts) >= 3:
        # Use the second-level domain (e.g. "accenture" from "careers.accenture.com")
        company = parts[-2]
        if company not in ("co", "com", "org", "in", "io", "net"):
            return company.title() + " Careers"
    
    return "Apply"
