"""
CareerPilot AI — Company Research Router
Uses Gemini Flash for company research (no SERP API needed).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company
from app.schemas import MessageResponse

router = APIRouter()


@router.get("/research")
async def research_company(
    company_name: str = Query(..., min_length=2, description="Company name to research"),
    role: str = Query("AEM Architect", description="Role you're targeting"),
    location: str = Query("Hyderabad, India", description="Location context"),
):
    """
    Research a company using Gemini Flash.
    Returns AEM-focused research: practice size, salary range, interview tips, etc.
    """
    from app.agents.company import research_company as do_research

    result = await do_research(
        company_name=company_name,
        role=role,
        location=location,
    )

    if not result.get("research"):
        raise HTTPException(status_code=503, detail="Company research failed — check if Gemini API key is configured")

    return result


@router.get("/interview-tips")
async def interview_tips(
    company_name: str = Query(..., min_length=2, description="Company name"),
    role: str = Query("AEM Architect", description="Role you're targeting"),
):
    """
    Get AEM-specific interview questions and tips for a company.
    """
    from app.agents.company import get_interview_tips

    result = await get_interview_tips(
        company_name=company_name,
        role=role,
    )

    if not result.get("questions_and_answers"):
        raise HTTPException(status_code=503, detail="Interview tips failed — check Gemini API key")

    return result


@router.get("/salary-intel")
async def salary_intel(
    company_name: str = Query(..., min_length=2, description="Company name"),
    role: str = Query("AEM Architect", description="Role"),
    experience_years: int = Query(8, ge=1, le=30, description="Years of experience"),
):
    """
    Get salary intelligence for a company + role combination.
    """
    from app.agents.company import get_salary_intel

    result = await get_salary_intel(
        company_name=company_name,
        role=role,
        experience_years=experience_years,
    )

    if not result.get("salary_intel"):
        raise HTTPException(status_code=503, detail="Salary intel failed — check Gemini API key")

    return result


@router.get("/aem-hirers")
def list_aem_hirers(db: Session = Depends(get_db)):
    """List known AEM hiring companies from our database."""
    companies = db.query(Company).filter(Company.is_aem_hirer == True).all()
    return {
        "total": len(companies),
        "companies": [
            {
                "id": c.id,
                "name": c.name,
                "industry": c.industry,
                "size": c.size,
                "website": c.website,
            }
            for c in companies
        ],
    }
