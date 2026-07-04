"""
CareerPilot AI — Database Connection
SQLite with SQLAlchemy async-compatible session.
WAL mode for concurrent reads + single writer.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base — all models inherit from this."""
    pass


# SQLite engine — WAL mode for better concurrent read performance
engine = create_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False},  # SQLite: allow cross-thread usage
)


# Enable WAL mode and foreign keys on every connection
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")  # 5s timeout for write locks
    cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes, still safe with WAL
    cursor.close()


# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Session:
    """Dependency that provides a database session.
    Use with FastAPI's Depends() for route handlers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist. Called on app startup."""
    # Import all models so they register with Base.metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Ensure FTS5 virtual table exists
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts USING fts5(
                title, company_name, location, description, skills_required,
                content=jobs, content_rowid=id
            )
        """))
        conn.commit()

    # Ensure data directories exist
    settings.ensure_data_dirs()
