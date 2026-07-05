"""
CareerPilot AI — FastAPI Application
Personal AEM/EDS Career Assistant
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # ── Startup ──
    init_db()
    print(f"🚀 CareerPilot AI backend running at {settings.api_url}")
    print(f"   Environment: {settings.app_env}")
    print(f"   Database: {settings.database_path}")
    print(f"   Ollama: {settings.ollama_host}")

    # Start scheduler
    try:
        from app.services.scheduler import scheduler_service
        scheduler_service.start()
    except Exception as e:
        print(f"⚠️  Scheduler failed to start: {e}")

    yield

    # ── Shutdown ──
    try:
        from app.services.scheduler import scheduler_service
        scheduler_service.stop()
    except Exception:
        pass
    print("👋 CareerPilot AI backend shutting down")


app = FastAPI(
    title="CareerPilot AI",
    description="Personal AEM/EDS Career Assistant — Job search, scoring, resume tailoring, and application tracking",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/")
async def root():
    """Root redirect — points to Swagger docs."""
    return {
        "app": "CareerPilot AI",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "profile": "/api/profile",
            "jobs": "/api/jobs",
            "applications": "/api/applications",
            "company": "/api/company",
            "scheduler": "/scheduler/status",
            "settings": "/scheduler/settings",
        },
    }

# CORS — allow the Next.js frontend (personal tool, open CORS is fine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_url, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──
from app.routers import profile, jobs, applications, health, company, scheduler  # noqa: E402

app.include_router(health.router, tags=["Health"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(company.router, prefix="/api/company", tags=["Company Research"])
app.include_router(scheduler.router, tags=["Scheduler & Settings"])
