"""
CareerPilot AI — Configuration
All settings loaded from .env file with sensible defaults.
Single user — no auth, no RBAC, no billing.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma"
RESUMES_DIR = DATA_DIR / "resumes"
COVER_LETTERS_DIR = DATA_DIR / "cover_letters"
EXPORTS_DIR = DATA_DIR / "exports"


class Settings(BaseSettings):
    """Application settings — loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_env: str = "development"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    secret_key: str = "change-me-in-production"
    database_path: str = str(DATA_DIR / "careerpilot.db")

    # --- LLM ---
    ollama_host: str = "http://localhost:11434"
    google_api_key: Optional[str] = None

    # --- Job Search APIs ---
    rapidapi_key: Optional[str] = None
    jsearch_host: str = "jsearch.p.rapidapi.com"
    jsearch_direct_key: Optional[str] = None  # Direct OpenWeb Ninja key (preferred over RapidAPI)
    adzuna_app_id: Optional[str] = None
    adzuna_app_key: Optional[str] = None

    # --- Company Research ---
    serper_api_key: Optional[str] = None

    # --- Notifications ---
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # --- Google Sheets Sync ---
    google_sheets_credentials_file: Optional[str] = None
    google_sheets_spreadsheet_id: Optional[str] = None

    # --- AEM-specific matching weights ---
    skill_match_weight: float = 0.30
    experience_match_weight: float = 0.25
    salary_match_weight: float = 0.15
    location_match_weight: float = 0.10
    company_quality_weight: float = 0.10
    remote_preference_weight: float = 0.10

    # --- Job Search Defaults ---
    default_search_queries: list[str] = Field(
        default=[
            "AEM developer",
            "Adobe Experience Manager developer",
            "AEM architect",
            "EDS developer",
            "AEM Sites developer",
        ]
    )
    default_location: str = "Hyderabad, India"
    default_country: str = "in"

    # --- Salary Targets (INR, yearly) ---
    expected_salary_min: int = 2_000_000   # 20 LPA
    expected_salary_max: int = 3_500_000   # 35 LPA

    # --- LLM Provider Selection ---
    # "ollama" for background tasks, "gemini" for interactive tasks, "auto" for smart routing
    llm_provider: str = "auto"  # auto = ollama for bg, gemini for interactive

    # --- Ollama Model Names ---
    ollama_chat_model: str = "qwen3:8b"
    ollama_embedding_model: str = "nomic-embed-text"

    # --- Gemini Model Name ---
    gemini_model: str = "gemini-2.5-flash"

    # --- Embedding Dimensions (nomic-embed-text) ---
    embedding_dimensions: int = 768

    # --- Job Search Limits ---
    max_jobs_per_search: int = 50
    job_dedup_similarity_threshold: float = 0.85

    @property
    def database_url(self) -> str:
        """SQLAlchemy connection URL for SQLite."""
        return f"sqlite:///{self.database_path}"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def ensure_data_dirs(self) -> None:
        """Create data directories if they don't exist."""
        for d in [DATA_DIR, CHROMA_DIR, RESUMES_DIR, COVER_LETTERS_DIR, EXPORTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)


# Singleton settings instance
settings = Settings()
