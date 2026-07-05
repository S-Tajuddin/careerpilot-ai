"""
CareerPilot AI — Scheduler & Settings Router
Manage background scheduler, trigger manual runs, and update settings.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SettingsUpdate, SettingsResponse, MessageResponse
from app.models import Settings as SettingsModel

router = APIRouter()


# ─── Scheduler ──────────────────────────────────────────────────────────────

@router.get("/scheduler/status")
async def scheduler_status():
    """Get scheduler status and scheduled jobs."""
    from app.services.scheduler import scheduler_service

    return {
        "running": scheduler_service.is_running,
        "jobs": scheduler_service.get_jobs_info() if scheduler_service.is_running else [],
    }


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the background scheduler."""
    from app.services.scheduler import scheduler_service

    if scheduler_service.is_running:
        return {"message": "Scheduler already running", "jobs": scheduler_service.get_jobs_info()}

    scheduler_service.start()
    return {"message": "Scheduler started", "jobs": scheduler_service.get_jobs_info()}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the background scheduler."""
    from app.services.scheduler import scheduler_service

    if not scheduler_service.is_running:
        return {"message": "Scheduler not running"}

    scheduler_service.stop()
    return {"message": "Scheduler stopped"}


@router.post("/scheduler/trigger/search")
async def trigger_search():
    """Manually trigger daily job search."""
    from app.services.scheduler import scheduler_service

    if not scheduler_service.is_running:
        raise HTTPException(status_code=400, detail="Scheduler not running")

    result = await scheduler_service.trigger_search()
    return {"message": "Job search triggered", **result}


@router.post("/scheduler/trigger/digest")
async def trigger_digest():
    """Manually trigger Telegram daily digest."""
    from app.services.scheduler import scheduler_service

    if not scheduler_service.is_running:
        raise HTTPException(status_code=400, detail="Scheduler not running")

    result = await scheduler_service.trigger_digest()
    return {"message": "Digest triggered", **result}


@router.post("/scheduler/trigger/sheets-sync")
async def trigger_sheets_sync():
    """Manually trigger Google Sheets sync."""
    from app.services.scheduler import scheduler_service

    result = await scheduler_service.trigger_sheets_sync()
    return {"message": "Sheets sync triggered", **result}


# ─── Settings ───────────────────────────────────────────────────────────────

@router.get("/settings", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """Get current app settings."""
    settings = db.query(SettingsModel).filter(SettingsModel.id == 1).first()
    if not settings:
        # Create default settings
        settings = SettingsModel(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.put("/settings", response_model=SettingsResponse)
def update_settings(updates: SettingsUpdate, db: Session = Depends(get_db)):
    """Update app settings."""
    settings = db.query(SettingsModel).filter(SettingsModel.id == 1).first()
    if not settings:
        settings = SettingsModel(id=1)
        db.add(settings)
        db.flush()

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    from datetime import datetime, timezone
    settings.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(settings)
    return settings


# ─── Google Sheets Status ───────────────────────────────────────────────────

@router.get("/sheets/status")
def sheets_status():
    """Get Google Sheets connection status."""
    from app.services.sheets import sheets_service
    return sheets_service.get_status()


# ─── Telegram Test ──────────────────────────────────────────────────────────

@router.get("/telegram/test")
async def telegram_test():
    """Test Telegram bot connection."""
    from app.services.telegram import telegram_service
    return await telegram_service.test_connection()


@router.post("/telegram/send-test")
async def telegram_send_test():
    """Send a test message via Telegram."""
    from app.services.telegram import telegram_service

    if not telegram_service.is_configured:
        raise HTTPException(status_code=400, detail="Telegram not configured — set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

    success = await telegram_service.send_message(
        "🧪 CareerPilot AI test message — your Telegram notifications are working!"
    )

    if success:
        return {"message": "Test message sent successfully!"}
    raise HTTPException(status_code=500, detail="Failed to send test message — check your TELEGRAM_CHAT_ID")
