"""
CareerPilot AI — Scheduler Service
Automated daily job search + Telegram alerts + Google Sheets sync.
Uses APScheduler for background scheduling.
"""

from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Job, Application, Profile, Settings, ActivityLog
from app.services.scoring import scoring_service
import json


class SchedulerService:
    """
    Background scheduler for CareerPilot AI.
    - Daily job search (configurable time)
    - Quick-score new jobs
    - Telegram daily digest
    - Follow-up reminders
    - Google Sheets sync
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
        self._running = False

    def start(self):
        """Start the scheduler with default jobs."""
        if self._running:
            return

        # Daily job search at 9:00 AM IST
        self.scheduler.add_job(
            self.daily_job_search,
            CronTrigger(hour=9, minute=0, timezone="Asia/Kolkata"),
            id="daily_job_search",
            name="Daily AEM Job Search",
            replace_existing=True,
        )

        # Daily digest at 9:30 AM IST
        self.scheduler.add_job(
            self.daily_digest,
            CronTrigger(hour=9, minute=30, timezone="Asia/Kolkata"),
            id="daily_digest",
            name="Daily Telegram Digest",
            replace_existing=True,
        )

        # Follow-up reminders at 10:00 AM IST
        self.scheduler.add_job(
            self.followup_reminders,
            CronTrigger(hour=10, minute=0, timezone="Asia/Kolkata"),
            id="followup_reminders",
            name="Follow-up Reminders",
            replace_existing=True,
        )

        # Google Sheets sync every 2 hours
        self.scheduler.add_job(
            self.sheets_sync,
            CronTrigger(hour="*/2", minute=15, timezone="Asia/Kolkata"),
            id="sheets_sync",
            name="Google Sheets Sync",
            replace_existing=True,
        )

        self.scheduler.start()
        self._running = True
        print("📅 Scheduler started — 4 jobs scheduled")

    def stop(self):
        """Stop the scheduler."""
        if self._running:
            self.scheduler.shutdown(wait=False)
            self._running = False
            print("📅 Scheduler stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    def get_jobs_info(self) -> list[dict]:
        """Get info about all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger),
            })
        return jobs

    # ══════════════════════════════════════════════════════════════════════
    #  SCHEDULED TASKS
    # ══════════════════════════════════════════════════════════════════════

    async def daily_job_search(self):
        """
        Search all default queries across sources.
        Quick-scores new jobs automatically.
        """
        print(f"🔍 [{datetime.now(timezone.utc).isoformat()}] Daily job search started")

        db = SessionLocal()
        try:
            from app.services.job_service import job_service

            queries = settings.default_search_queries
            total_new = 0

            for query in queries:
                try:
                    jobs = await job_service.search_all_sources(
                        query=query,
                        location=settings.default_location,
                        country=settings.default_country,
                        max_results=15,
                        db=db,
                    )
                    total_new += len(jobs)
                    print(f"  Searched '{query}': {len(jobs)} results")
                except Exception as e:
                    print(f"  Search error for '{query}': {e}")

            # Quick-score any unscored jobs
            stats = scoring_service.quick_score_all_unscored(db)
            print(f"  Quick-scored {stats['scored']} new jobs")

            # Send Telegram alert if new jobs found
            if total_new > 0:
                await self._send_job_alert(db, total_new)

            # Log activity
            self._log_activity(db, "daily_search", "scheduler", 0, {
                "total_new": total_new,
                "scored": stats["scored"],
            })

            print(f"🔍 Daily search complete: {total_new} new jobs found")

        except Exception as e:
            print(f"❌ Daily job search error: {e}")
        finally:
            db.close()

    async def daily_digest(self):
        """Send daily Telegram digest with stats and top jobs."""
        print(f"📊 [{datetime.now(timezone.utc).isoformat()}] Sending daily digest")

        db = SessionLocal()
        try:
            from app.services.telegram import telegram_service

            if not telegram_service.is_configured:
                print("  Telegram not configured — skipping digest")
                return

            # Get stats
            total_active = db.query(Job).filter(Job.is_active == True).count()
            total_scored = db.query(Job).filter(
                Job.is_active == True, Job.match_score.isnot(None)
            ).count()

            # Top job today
            top_job = db.query(Job).filter(
                Job.is_active == True, Job.match_score.isnot(None)
            ).order_by(Job.match_score.desc()).first()

            top_job_dict = None
            if top_job:
                top_job_dict = {
                    "title": top_job.title,
                    "company": top_job.company_name,
                    "score": top_job.match_score,
                    "salary": top_job.salary_display(),
                }

            # Follow-up count
            pending_followups = db.query(Application).filter(
                Application.next_followup.isnot(None),
                Application.next_followup <= datetime.now(timezone.utc),
                Application.status.in_(["applied", "interview_scheduled"]),
            ).count()

            # Upcoming interviews
            upcoming = db.query(Application).filter(
                Application.status == "interview_scheduled"
            ).count()

            await telegram_service.send_daily_digest(
                new_jobs_count=total_active,
                top_job=top_job_dict,
                pending_followups=pending_followups,
                upcoming_interviews=upcoming,
            )

            print("📊 Daily digest sent")

        except Exception as e:
            print(f"❌ Daily digest error: {e}")
        finally:
            db.close()

    async def followup_reminders(self):
        """Send Telegram follow-up reminders for applications needing attention."""
        print(f"⏰ [{datetime.now(timezone.utc).isoformat()}] Checking follow-ups")

        db = SessionLocal()
        try:
            from app.services.telegram import telegram_service

            if not telegram_service.is_configured:
                return

            overdue = db.query(Application).filter(
                Application.next_followup.isnot(None),
                Application.next_followup <= datetime.now(timezone.utc),
                Application.status.in_(["applied", "interview_scheduled"]),
            ).all()

            for app in overdue[:5]:  # Max 5 reminders
                if app.job:
                    days_since = (datetime.now(timezone.utc) - (app.applied_at or app.created_at)).days
                    await telegram_service.send_followup_reminder(
                        job_title=app.job.title,
                        company=app.job.company_name,
                        days_since=days_since,
                    )

            if overdue:
                print(f"⏰ Sent {len(overdue[:5])} follow-up reminders")

        except Exception as e:
            print(f"❌ Follow-up reminder error: {e}")
        finally:
            db.close()

    async def sheets_sync(self):
        """Sync applications data to Google Sheets."""
        print(f"📊 [{datetime.now(timezone.utc).isoformat()}] Google Sheets sync")

        db = SessionLocal()
        try:
            from app.services.sheets import sheets_service

            if not sheets_service.is_configured:
                print("  Google Sheets not configured — skipping sync")
                return

            apps = db.query(Application).order_by(Application.updated_at.desc()).limit(200).all()
            rows = []
            for app in apps:
                job = app.job
                rows.append({
                    "Job Title": job.title if job else "Unknown",
                    "Company": job.company_name if job else "Unknown",
                    "Location": job.location if job else "",
                    "Salary": job.salary_display() if job else "",
                    "Match Score": f"{job.match_score}%" if job and job.match_score else "",
                    "Status": app.status,
                    "Applied At": str(app.applied_at or ""),
                    "Notes": app.notes or "",
                    "Rating": str(app.rating or ""),
                })

            sheets_service.sync_applications(rows)
            print(f"📊 Synced {len(rows)} applications to Google Sheets")

        except ImportError:
            print("  Google Sheets service not available — skipping")
        except Exception as e:
            print(f"❌ Sheets sync error: {e}")
        finally:
            db.close()

    # ══════════════════════════════════════════════════════════════════════
    #  MANUAL TRIGGERS
    # ══════════════════════════════════════════════════════════════════════

    async def trigger_search(self) -> dict:
        """Manually trigger a job search (same as daily)."""
        await self.daily_job_search()
        return {"triggered": "daily_job_search"}

    async def trigger_digest(self) -> dict:
        """Manually trigger a Telegram digest."""
        await self.daily_digest()
        return {"triggered": "daily_digest"}

    async def trigger_sheets_sync(self) -> dict:
        """Manually trigger Google Sheets sync."""
        await self.sheets_sync()
        return {"triggered": "sheets_sync"}

    # ══════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════

    async def _send_job_alert(self, db: Session, count: int):
        """Send Telegram alert for newly found jobs."""
        try:
            from app.services.telegram import telegram_service

            if not telegram_service.is_configured:
                return

            # Get top 5 new jobs
            top_jobs = db.query(Job).filter(
                Job.is_active == True, Job.match_score.isnot(None)
            ).order_by(Job.match_score.desc()).limit(5).all()

            job_list = []
            for job in top_jobs:
                job_list.append({
                    "title": job.title,
                    "company": job.company_name,
                    "score": job.match_score,
                    "salary": job.salary_display(),
                    "location": job.location or "",
                    "url": job.source_url or "",
                })

            await telegram_service.send_job_alert(job_list)

        except Exception as e:
            print(f"  Telegram alert error: {e}")

    @staticmethod
    def _log_activity(db: Session, action: str, entity_type: str, entity_id: int, details: dict = None):
        try:
            entry = ActivityLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=json.dumps(details) if details else None,
            )
            db.add(entry)
            db.commit()
        except Exception:
            pass


# Singleton
scheduler_service = SchedulerService()
