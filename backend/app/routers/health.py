"""
CareerPilot AI — Health Check Router
Simple endpoint to verify backend is running and dependencies are available.
"""

from fastapi import APIRouter

import httpx

from app.config import settings
from app.database import engine
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check backend health, database connection, and LLM availability."""
    # Check SQLite
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {e}"

    # Check Ollama
    ollama_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_host}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                has_qwen = any("qwen3" in m for m in model_names)
                has_embed = any("nomic" in m for m in model_names)
                if has_qwen and has_embed:
                    ollama_status = "ready"
                elif has_qwen or has_embed:
                    ollama_status = "partial"
                else:
                    ollama_status = "no_models"
            else:
                ollama_status = f"error_{resp.status_code}"
    except httpx.ConnectError:
        ollama_status = "offline"
    except Exception as e:
        ollama_status = f"error: {type(e).__name__}"

    # Check Gemini
    gemini_status = "unknown"
    if settings.google_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            models_list = list(genai.list_models())
            gemini_status = "ready" if models_list else "no_models"
        except Exception:
            gemini_status = "error"
    else:
        gemini_status = "no_key"

    return HealthResponse(
        status="ok",
        version="0.1.0",
        database=db_status,
        ollama=ollama_status,
        gemini=gemini_status,
    )
