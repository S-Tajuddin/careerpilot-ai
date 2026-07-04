"""
CareerPilot AI — AI Scoring Service
Two-tier scoring:
  Tier 1 (Quick): Deterministic 6-dimension scoring — instant, no LLM calls
  Tier 2 (Deep):  LLM recommendations + embedding storage — on-demand only

Weights (AEM-optimized):
  skill_match      = 0.30
  experience_match = 0.25
  salary_match     = 0.15
  location_match   = 0.10
  company_quality  = 0.10
  remote_preference= 0.10
"""

import json
import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Job, Profile, Company
from app.services.llm import llm_service
from app.services.embeddings import embedding_service


# ─── AEM Skill Taxonomy ─────────────────────────────────────────────────────

AEM_SKILL_GROUPS = {
    "core_aem": [
        "aem", "adobe experience manager", "cq5", "cq", "aem sites",
        "aem assets", "aem forms", "aem as cloud service",
        "experience manager", "aemaa", "ams", "aem managed services",
    ],
    "eds": [
        "eds", "edge delivery services", "helix", "aem edge delivery",
        "franklin", "aem franklin", "universal editor", "content fusion",
    ],
    "backend": [
        "java", "sling", "osgi", "felix", "jcr", "jackrabbit",
        "sling models", "sling servlets", "sling filters", "aem workflows",
        "aem eventing", "resource resolver", "sling resource merger",
    ],
    "frontend": [
        "htl", "sightly", "aem components", "aem templates",
        "clientlibs", "aem style system", "responsive grid", "core components",
        "aem page editor", "spa editor", "we-retail",
    ],
    "devops": [
        "cloud manager", "aem pipeline", "dispatcher", "replication",
        "aem package manager", "maven", "ci/cd", "jenkins", "git",
        "aem upgrade", "rde", "rapid development environment",
    ],
    "testing": [
        "aem testing", "junit", "mockito", "selenium", "cypress",
        "wcm.io", "aem mock", "sling testing",
    ],
    "architect": [
        "aem architecture", "system design", "aem design patterns",
        "multi-site manager", "msm", "launches", "content architecture",
        "info architecture", "aem security", "aem performance",
        "aem caching", "aem dispatcher rules", "cdn",
    ],
}

SKILL_LOOKUP: dict[str, str] = {}
for group, skills in AEM_SKILL_GROUPS.items():
    for skill in skills:
        SKILL_LOOKUP[skill.lower().strip()] = group


class ScoringService:
    """
    Two-tier scoring:
    - quick_score(): Deterministic only — instant (< 1ms per job)
    - deep_score():  + LLM recommendations + embeddings — on-demand
    """

    def __init__(self):
        self.weights = {
            "skill_match": settings.skill_match_weight,
            "experience_match": settings.experience_match_weight,
            "salary_match": settings.salary_match_weight,
            "location_match": settings.location_match_weight,
            "company_quality": settings.company_quality_weight,
            "remote_preference": settings.remote_preference_weight,
        }
        self.salary_min = settings.expected_salary_min
        self.salary_max = settings.expected_salary_max

    # ══════════════════════════════════════════════════════════════════════
    #  TIER 1: QUICK SCORE — Instant, no LLM, no embeddings
    # ══════════════════════════════════════════════════════════════════════

    def quick_score(self, job: Job, profile: Profile, db: Session) -> dict:
        """
        Deterministic scoring only — NO LLM calls, NO embedding generation.
        Runs in < 1ms per job. Used for auto-scoring on search.
        """
        skill_score = self._score_skills(job, profile)
        exp_score = self._score_experience(job, profile)
        salary_score = self._score_salary(job, profile)
        location_score = self._score_location(job, profile)
        company_score = self._score_company_quality(job, db)
        remote_score = self._score_remote_preference(job, profile)

        overall = (
            skill_score * self.weights["skill_match"]
            + exp_score * self.weights["experience_match"]
            + salary_score * self.weights["salary_match"]
            + location_score * self.weights["location_match"]
            + company_score * self.weights["company_quality"]
            + remote_score * self.weights["remote_preference"]
        )
        overall = round(min(100, max(0, overall)), 1)

        strengths = self._get_strengths(skill_score, exp_score, salary_score, location_score, company_score, remote_score, job, profile)
        weaknesses = self._get_weaknesses(skill_score, exp_score, salary_score, location_score, company_score, remote_score, job, profile)
        recommendations = self._fallback_recommendations(weaknesses)

        return {
            "overall_score": overall,
            "dimension_scores": {
                "skill_match": round(skill_score, 1),
                "experience_match": round(exp_score, 1),
                "salary_match": round(salary_score, 1),
                "location_match": round(location_score, 1),
                "company_quality": round(company_score, 1),
                "remote_preference": round(remote_score, 1),
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "is_deep_scored": False,
        }

    # ══════════════════════════════════════════════════════════════════════
    #  TIER 2: DEEP SCORE — Adds LLM recommendations + embedding
    # ══════════════════════════════════════════════════════════════════════

    async def deep_score(self, job: Job, profile: Profile, db: Session) -> dict:
        """
        Quick score + LLM recommendations + embedding storage.
        Use this when user explicitly requests detailed analysis.
        Takes ~5-15s per job (depends on Ollama speed).
        """
        # Start with quick score
        result = self.quick_score(job, profile, db)

        # Add LLM recommendations
        try:
            llm_recs = await self._llm_recommendations(
                job, profile, result["overall_score"],
                result["strengths"], result["weaknesses"],
            )
            if llm_recs:
                result["recommendations"] = llm_recs
        except Exception as e:
            print(f"LLM recommendations failed (non-critical): {e}")

        # Store embedding for dedup
        try:
            skills_list = job.skills_required_list if hasattr(job, 'skills_required_list') else []
            embedding_id = await embedding_service.store_job_embedding(
                job_id=job.id,
                source=job.source,
                source_id=job.source_id or "",
                title=job.title,
                company_name=job.company_name or "",
                description=job.description or "",
                skills=skills_list,
            )
            result["embedding_id"] = embedding_id
        except Exception as e:
            print(f"Embedding storage failed (non-critical): {e}")

        result["is_deep_scored"] = True
        return result

    # ══════════════════════════════════════════════════════════════════════
    #  BATCH SCORING
    # ══════════════════════════════════════════════════════════════════════

    def quick_score_all_unscored(self, db: Session) -> dict:
        """Quick-score all unscored jobs — instant, no async."""
        profile = db.query(Profile).filter(Profile.id == 1).first()
        if not profile:
            profile = Profile(
                id=1, experience_years=8, current_role="AEM Developer",
                target_role="AEM Architect", expected_salary_min=2_000_000,
                expected_salary_max=3_500_000, location="Hyderabad, India",
                remote_preference="any",
            )

        unscored = db.query(Job).filter(
            Job.is_active == True, Job.match_score.is_(None),
        ).all()

        scored_count = 0
        for job in unscored:
            try:
                result = self.quick_score(job, profile, db)
                job.match_score = result["overall_score"]
                job.match_strengths_list = result["strengths"]
                job.match_weaknesses_list = result["weaknesses"]
                job.match_recommendations_list = result["recommendations"]
                job.updated_at = datetime.now(timezone.utc)
                scored_count += 1
            except Exception as e:
                print(f"Quick-score error for job {job.id}: {e}")

        db.commit()
        return {
            "total_unscored": len(unscored),
            "scored": scored_count,
            "errors": len(unscored) - scored_count,
            "mode": "quick",
        }

    async def deep_score_all_unscored(self, db: Session) -> dict:
        """Deep-score all unscored jobs — includes LLM, takes longer."""
        profile = db.query(Profile).filter(Profile.id == 1).first()
        if not profile:
            profile = Profile(
                id=1, experience_years=8, current_role="AEM Developer",
                target_role="AEM Architect", expected_salary_min=2_000_000,
                expected_salary_max=3_500_000, location="Hyderabad, India",
                remote_preference="any",
            )

        unscored = db.query(Job).filter(
            Job.is_active == True, Job.match_score.is_(None),
        ).all()

        scored_count = 0
        for job in unscored:
            try:
                result = await self.deep_score(job, profile, db)
                job.match_score = result["overall_score"]
                job.match_strengths_list = result["strengths"]
                job.match_weaknesses_list = result["weaknesses"]
                job.match_recommendations_list = result["recommendations"]
                if result.get("embedding_id"):
                    job.embedding_id = result["embedding_id"]
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
                scored_count += 1
                print(f"  ⭐ Deep scored: {job.title} = {result['overall_score']}%")
            except Exception as e:
                print(f"  Deep-score error for job {job.id}: {e}")

        return {
            "total_unscored": len(unscored),
            "scored": scored_count,
            "errors": len(unscored) - scored_count,
            "mode": "deep",
        }

    # ══════════════════════════════════════════════════════════════════════
    #  SCORING DIMENSIONS (same as before — no changes)
    # ══════════════════════════════════════════════════════════════════════

    def _score_skills(self, job: Job, profile: Profile) -> float:
        profile_skills = self._normalize_skills(profile.skills_list if hasattr(profile, 'skills_list') else [])
        if not profile_skills:
            profile_skills = self._normalize_skills([
                "AEM", "Adobe Experience Manager", "EDS", "Java", "Sling",
                "OSGi", "HTL", "AEM as Cloud Service", "Maven", "CI/CD",
            ])
        job_skills = self._normalize_skills(
            job.skills_required_list if hasattr(job, 'skills_required_list') else []
        )
        if not job_skills:
            job_skills = self._extract_skills_from_text(
                f"{job.title} {job.description or ''}"
            )
        if not job_skills:
            return 50.0

        profile_groups = set()
        for skill in profile_skills:
            group = SKILL_LOOKUP.get(skill)
            if group:
                profile_groups.add(group)
            else:
                for g, members in AEM_SKILL_GROUPS.items():
                    if any(skill in m or m in skill for m in members):
                        profile_groups.add(g)
                        break

        job_groups = set()
        for skill in job_skills:
            group = SKILL_LOOKUP.get(skill)
            if group:
                job_groups.add(group)
            else:
                for g, members in AEM_SKILL_GROUPS.items():
                    if any(skill in m or m in skill for m in members):
                        job_groups.add(g)
                        break

        profile_skill_set = set(profile_skills)
        job_skill_set = set(job_skills)
        direct_matches = profile_skill_set & job_skill_set
        group_matches = profile_groups & job_groups if profile_groups and job_groups else set()

        direct_ratio = len(direct_matches) / len(job_skill_set) if job_skill_set else 0
        group_ratio = len(group_matches) / len(job_groups) if job_groups else 0

        score = (direct_ratio * 0.6 + group_ratio * 0.4) * 100
        return min(100, max(0, score))

    def _score_experience(self, job: Job, profile: Profile) -> float:
        user_exp = profile.experience_years or 8.0
        required_exp = self._parse_experience_years(job.experience_required)
        title_lower = (job.title or "").lower()
        if not required_exp:
            if "senior" in title_lower or "lead" in title_lower:
                required_exp = 6.0
            elif "architect" in title_lower or "principal" in title_lower:
                required_exp = 10.0
            elif "junior" in title_lower or "associate" in title_lower:
                required_exp = 2.0
            elif "mid" in title_lower or "ii" in title_lower:
                required_exp = 4.0
            else:
                required_exp = 5.0
        diff = user_exp - required_exp
        if -1 <= diff <= 2: return 100.0
        if -2 <= diff < -1: return 80.0
        if 2 < diff <= 4: return 75.0
        if -3 <= diff < -2: return 60.0
        if 4 < diff <= 6: return 65.0
        if -4 <= diff < -3: return 45.0
        if diff > 6: return 55.0
        return 30.0

    def _score_salary(self, job: Job, profile: Profile) -> float:
        if not job.salary_min and not job.salary_max:
            return 70.0
        target_min = profile.expected_salary_min or self.salary_min
        target_max = profile.expected_salary_max or self.salary_max
        job_min = self._normalize_salary(job.salary_min, job.salary_currency, job.salary_period)
        job_max = self._normalize_salary(job.salary_max, job.salary_currency, job.salary_period)
        if job_min is None and job_max is None:
            return 70.0
        if job_min and job_max:
            if job_min >= target_min and job_max <= target_max: return 100.0
            if job_min >= target_min: return 90.0
            if job_max >= target_min: return 75.0
        job_mid = ((job_min or job_max) + (job_max or job_min)) / 2
        target_mid = (target_min + target_max) / 2
        ratio = job_mid / target_mid if target_mid > 0 else 0
        if 0.8 <= ratio <= 1.5: return 85.0
        if 0.6 <= ratio < 0.8: return 55.0
        if ratio > 1.5: return 80.0
        if ratio < 0.6: return 25.0
        return 50.0

    def _score_location(self, job: Job, profile: Profile) -> float:
        preferred_locs = profile.preferred_locations_list if hasattr(profile, 'preferred_locations_list') else []
        if not preferred_locs:
            preferred_locs = ["Hyderabad", "Remote", "Bangalore", "Pune"]
        job_location = (job.location or "").lower()
        if not job_location:
            return 60.0
        if job.is_remote:
            if profile.remote_preference in ("remote", "any"): return 100.0
            if profile.remote_preference == "hybrid": return 80.0
            return 50.0
        for pref in preferred_locs:
            if pref.lower() in job_location: return 100.0
        user_city = (profile.location or "Hyderabad, India").split(",")[0].strip().lower()
        if user_city and user_city in job_location: return 100.0
        if "india" in job_location or any(c in job_location for c in [
            "hyderabad", "bangalore", "bengaluru", "pune", "mumbai",
            "chennai", "noida", "gurgaon", "delhi", "kolkata"
        ]): return 70.0
        return 35.0

    def _score_company_quality(self, job: Job, db: Session) -> float:
        if job.company_id:
            company = db.query(Company).filter(Company.id == job.company_id).first()
            if company:
                if company.is_aem_hirer: return 100.0
                if company.size == "enterprise": return 85.0
                if company.size == "large": return 80.0
                if company.size == "mid": return 70.0
                if company.size == "startup": return 60.0
        known_aem_companies = {
            "accenture", "infosys", "wipro", "tcs", "tata consultancy",
            "cognizant", "capgemini", "ibm", "deloitte", "adobe",
            "publicis sapient", "sapient", "hcl", "tech mahindra",
            "mindtree", "larsen", "infy", "wipr", "cogni",
        }
        company_lower = (job.company_name or "").lower()
        for known in known_aem_companies:
            if known in company_lower: return 90.0
        return 55.0

    def _score_remote_preference(self, job: Job, profile: Profile) -> float:
        pref = profile.remote_preference or "any"
        if pref == "any": return 80.0
        if pref == "remote":
            return 100.0 if job.is_remote else 40.0
        if pref == "hybrid":
            return 70.0 if job.is_remote else 80.0
        if pref == "onsite":
            return 30.0 if job.is_remote else 100.0
        return 60.0

    # ══════════════════════════════════════════════════════════════════════
    #  STRENGTHS / WEAKNESSES / RECOMMENDATIONS
    # ══════════════════════════════════════════════════════════════════════

    def _get_strengths(self, skill_s, exp_s, salary_s, loc_s, comp_s, remote_s, job, profile) -> list[str]:
        strengths = []
        if skill_s >= 70: strengths.append(f"Strong skill alignment ({skill_s:.0f}%) — your AEM/EDS skills match this role")
        if exp_s >= 80: strengths.append(f"Experience level matches well ({profile.experience_years or 8:.0f} years)")
        if salary_s >= 80: strengths.append("Salary range aligns with your target (₹20-35 LPA)")
        if loc_s >= 80: strengths.append(f"Location match — {job.location or 'Remote'}")
        if comp_s >= 80: strengths.append(f"{job.company_name} is a known AEM employer — strong hiring signal")
        if remote_s >= 80 and job.is_remote: strengths.append("Remote role matches your preference")
        if not strengths: strengths.append("Job found in your search criteria")
        return strengths

    def _get_weaknesses(self, skill_s, exp_s, salary_s, loc_s, comp_s, remote_s, job, profile) -> list[str]:
        weaknesses = []
        if skill_s < 50: weaknesses.append(f"Skill gap detected ({skill_s:.0f}% match) — may need upskilling")
        if exp_s < 50:
            req = job.experience_required or "unspecified"
            weaknesses.append(f"Experience mismatch — job requires {req}, you have {profile.experience_years or 8:.0f} years")
        if salary_s < 50: weaknesses.append("Salary below your target range")
        if loc_s < 50: weaknesses.append(f"Location mismatch — {job.location or 'unknown'} vs your preference")
        if remote_s < 50 and profile.remote_preference == "remote" and not job.is_remote:
            weaknesses.append("This is an onsite role — you prefer remote")
        if comp_s < 50: weaknesses.append(f"{job.company_name} — limited AEM hiring history")
        return weaknesses

    def _fallback_recommendations(self, weaknesses: list[str]) -> list[str]:
        recs = []
        for w in weaknesses:
            if "skill" in w.lower(): recs.append("Consider highlighting transferable skills in your application")
            elif "experience" in w.lower(): recs.append("Emphasize relevant project experience over total years")
            elif "salary" in w.lower(): recs.append("Negotiate based on market rate — use company salary intel tool")
            elif "location" in w.lower(): recs.append("Check if remote or hybrid arrangements are negotiable")
        if not recs: recs.append("Tailor your resume to emphasize AEM-specific experience before applying")
        return recs[:5]

    # ══════════════════════════════════════════════════════════════════════
    #  LLM RECOMMENDATIONS (Deep score only)
    # ══════════════════════════════════════════════════════════════════════

    async def _llm_recommendations(
        self, job: Job, profile: Profile, overall: float,
        strengths: list[str], weaknesses: list[str],
    ) -> list[str]:
        prompt = f"""You are an AEM/EDS career advisor. Analyze this job match and give 3-5 concise, actionable recommendations.

JOB: {job.title} at {job.company_name}
Location: {job.location or 'Not specified'} | Remote: {job.is_remote}
Salary: {job.salary_min or '?'}-{job.salary_max or '?'} {job.salary_currency or ''}
Skills: {', '.join((job.skills_required_list if hasattr(job, 'skills_required_list') else [])[:15]) or 'Not listed'}
Experience Required: {job.experience_required or 'Not specified'}

CANDIDATE PROFILE:
Role: {profile.current_role or 'AEM Developer'} → Target: {profile.target_role or 'AEM Architect'}
Experience: {profile.experience_years or 8} years
Skills: {', '.join((profile.skills_list if hasattr(profile, 'skills_list') else [])[:15])}
Location: {profile.location or 'Hyderabad, India'}
Remote Preference: {profile.remote_preference or 'any'}
Salary Target: ₹{(profile.expected_salary_min or 2000000)//100000}-{(profile.expected_salary_max or 3500000)//100000} LPA

MATCH SCORE: {overall}/100
Strengths: {', '.join(strengths[:5])}
Weaknesses: {', '.join(weaknesses[:5])}

Give 3-5 specific, actionable recommendations. Each 1-2 sentences. Focus on:
- Should they apply? Why/why not?
- How to tailor resume for this role
- What to highlight in interview
- Salary negotiation tips

Output as a JSON array of strings. Example: ["Rec 1", "Rec 2", "Rec 3"]"""

        response, model_used = await llm_service.generate(
            prompt=prompt,
            system="You are an expert AEM/EDS career advisor. Always respond with valid JSON only.",
            task_type="background",
            temperature=0.4,
            max_tokens=1024,
        )

        recommendations = self._parse_json_list(response)
        if not recommendations:
            lines = [l.strip().lstrip('0123456789.-) ') for l in response.split('\n') if l.strip()]
            recommendations = [l for l in lines if len(l) > 10][:5]
        return recommendations[:5] if recommendations else self._fallback_recommendations(weaknesses)

    # ══════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _normalize_skills(skills: list[str]) -> list[str]:
        return [s.lower().strip() for s in skills if s and s.strip()]

    def _extract_skills_from_text(self, text: str) -> list[str]:
        text_lower = text.lower()
        found = []
        for skill_variant in SKILL_LOOKUP:
            if skill_variant in text_lower:
                found.append(skill_variant)
        seen_groups = set()
        result = []
        for skill in found:
            group = SKILL_LOOKUP[skill]
            if group not in seen_groups:
                seen_groups.add(group)
                result.append(skill)
        return result

    @staticmethod
    def _parse_experience_years(exp_str: Optional[str]) -> Optional[float]:
        if not exp_str: return None
        matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:years?)?', exp_str.lower())
        if matches:
            nums = [float(m) for m in matches if m]
            if len(nums) >= 2: return sum(nums) / len(nums)
            return nums[0]
        return None

    @staticmethod
    def _normalize_salary(amount: Optional[int], currency: Optional[str], period: Optional[str]) -> Optional[float]:
        if amount is None: return None
        currency = (currency or "INR").upper()
        period = (period or "yearly").lower()
        if currency == "INR" and period in ("yearly", "year", "annually"): return float(amount)
        if currency == "INR" and period in ("monthly", "month"): return float(amount) * 12
        if currency == "USD":
            usd_amount = float(amount)
            if period in ("yearly", "year", "annually"): return usd_amount * 83
            if period in ("monthly", "month"): return usd_amount * 83 * 12
            if period in ("hourly", "hour"): return usd_amount * 83 * 2080
        return float(amount)

    @staticmethod
    def _parse_json_list(text: str) -> list[str]:
        try:
            result = json.loads(text)
            if isinstance(result, list): return [str(item) for item in result]
        except json.JSONDecodeError: pass
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                if isinstance(result, list): return [str(item) for item in result]
            except json.JSONDecodeError: pass
        return []


# Singleton
scoring_service = ScoringService()
