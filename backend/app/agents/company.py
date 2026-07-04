"""
CareerPilot AI — Company Research Agent
Uses Gemini Flash (free) to research companies for interview prep.
No SERP API needed — Gemini has built-in web knowledge.
"""

from typing import Optional

from app.config import settings
from app.services.llm import llm_service


# AEM-focused research prompt template
COMPANY_RESEARCH_PROMPT = """Research the company "{company_name}" for an AEM/Adobe Experience Manager developer who is preparing for a job interview.

Focus on:
1. **AEM/Digital Practice**: Do they have a dedicated AEM or digital experience team? How big? What kind of AEM projects do they work on?
2. **India Presence**: Where are their India offices? How many employees in India?
3. **Work Culture**: What's the work culture like? Work-life balance? Hybrid/remote policy?
4. **Salary Range**: What's the typical salary range for Senior AEM Developer / AEM Architect roles at this company in India?
5. **Recent News**: Any recent news about the company? Layoffs? Growth? New projects?
6. **Interview Tips**: What kind of questions do they ask in technical interviews? What do they value?
7. **Adobe Partnership**: Are they an Adobe Partner? What level? Do they work on AEM Sites, AEM Assets, AEM Forms, or EDS?

Format the response as structured sections with bullet points.
If the company is a known AEM hirer (like Accenture, Cognizant, Wipro, TCS, etc.), mention specific AEM project types they typically handle.
If you don't have enough information, say so honestly — don't fabricate details.
"""

COMPANY_RESEARCH_SYSTEM = """You are a career research assistant specializing in the Indian IT job market, 
specifically for Adobe Experience Manager (AEM) and Edge Delivery Services (EDS) roles.
You help AEM developers prepare for interviews by researching companies.
Provide honest, factual information. If you're not sure about something, say so.
Focus on India-specific details: salary in LPA, office locations, notice period expectations.
Always think about what an AEM Senior/Architect candidate would want to know."""


async def research_company(
    company_name: str,
    role: Optional[str] = None,
    location: Optional[str] = None,
) -> dict:
    """
    Research a company using Gemini Flash.
    
    Returns dict with:
        - company_name
        - research (full text)
        - model_used
    """
    prompt = COMPANY_RESEARCH_PROMPT.format(company_name=company_name)
    
    if role:
        prompt += f"\n\nThe candidate is applying for: {role}"
    if location:
        prompt += f"\nLocation: {location}"

    text, model_used = await llm_service.generate(
        prompt=prompt,
        system=COMPANY_RESEARCH_SYSTEM,
        task_type="interactive",  # Uses Gemini Flash (fast, free)
        temperature=0.3,
        max_tokens=2048,
    )

    return {
        "company_name": company_name,
        "research": text,
        "model_used": model_used,
        "source": "gemini_flash",
    }


async def get_interview_tips(
    company_name: str,
    role: str = "AEM Architect",
) -> dict:
    """
    Get AEM-specific interview tips for a company.
    Quick version — just the tips, not full research.
    """
    prompt = f"""Give me 10 likely interview questions and brief suggested answers for a {role} position at {company_name} in India.

Focus on:
- AEM architecture questions (component design, Sling models, OSGi services)
- AEM as Cloud Service vs On-Premise trade-offs
- EDS / Edge Delivery Services questions
- System design questions (multi-site, multi-language setups)
- India-specific: CTC negotiation, notice period, team structure

Format as:
Q1: [question]
A1: [2-3 line suggested answer]
..."""

    text, model_used = await llm_service.generate(
        prompt=prompt,
        system=COMPANY_RESEARCH_SYSTEM,
        task_type="interactive",
        temperature=0.4,
        max_tokens=2048,
    )

    return {
        "company_name": company_name,
        "role": role,
        "questions_and_answers": text,
        "model_used": model_used,
    }


async def get_salary_intel(
    company_name: str,
    role: str = "AEM Architect",
    experience_years: int = 8,
) -> dict:
    """
    Get salary intelligence for a specific company + role.
    """
    prompt = f"""What is the typical salary range for a {role} with {experience_years} years of experience at {company_name} in India?

Provide:
1. Estimated CTC range in LPA
2. Breakdown: base + variable + benefits
3. Monthly in-hand estimate
4. How does this compare to market average?
5. Negotiation tips specific to this company

If you don't have specific data for this company, give the general market range for {role} in India with {experience_years} years experience."""

    text, model_used = await llm_service.generate(
        prompt=prompt,
        system=COMPANY_RESEARCH_SYSTEM,
        task_type="interactive",
        temperature=0.3,
        max_tokens=1024,
    )

    return {
        "company_name": company_name,
        "role": role,
        "experience_years": experience_years,
        "salary_intel": text,
        "model_used": model_used,
    }
