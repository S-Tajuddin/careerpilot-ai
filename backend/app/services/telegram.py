"""
CareerPilot AI — Telegram Notification Service
Sends job alerts, application updates, and daily digests via Telegram bot.
Free, instant, works on phone.
"""

import json
from typing import Optional

import httpx

from app.config import settings


class TelegramService:
    """
    Telegram bot notification service.
    Sends formatted messages about new jobs, scores, and application updates.
    """

    def __init__(self):
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.api_base = "https://api.telegram.org/bot{token}/{method}"

    @property
    def is_configured(self) -> bool:
        """Check if Telegram bot is properly configured."""
        return bool(self.token and self.chat_id)

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message via Telegram bot.
        Uses HTML formatting for rich messages.
        """
        if not self.is_configured:
            print("Telegram not configured — skipping notification")
            return False

        url = self.api_base.format(token=self.token, method="sendMessage")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                })
                if resp.status_code == 200:
                    return True
                else:
                    print(f"Telegram API error: {resp.status_code} — {resp.text[:200]}")
                    return False
        except Exception as e:
            print(f"Telegram send error: {e}")
            return False

    async def send_job_alert(self, jobs: list[dict]) -> bool:
        """
        Send a daily job alert with top matching jobs.
        jobs format: [{"title", "company", "score", "salary", "url", "location"}]
        """
        if not jobs:
            return True

        lines = [
            f"🆕 <b>{len(jobs)} New AEM Jobs Found!</b>",
            "",
        ]

        for i, job in enumerate(jobs[:10], 1):
            title = job.get("title", "Unknown")
            company = job.get("company", "Unknown")
            score = job.get("score", 0)
            salary = job.get("salary", "Not disclosed")
            location = job.get("location", "")
            url = job.get("url", "")

            # Score emoji
            if score >= 80:
                score_icon = "🟢"
            elif score >= 60:
                score_icon = "🟡"
            else:
                score_icon = "🔴"

            lines.append(f"{i}. {score_icon} <b>{title}</b>")
            lines.append(f"   🏢 {company} • 📍 {location}")
            lines.append(f"   💰 {salary} • Match: {score:.0f}%")
            if url:
                lines.append(f"   🔗 <a href=\"{url}\">Apply</a>")
            lines.append("")

        lines.append("— CareerPilot AI")

        return await self.send_message("\n".join(lines))

    async def send_application_update(
        self,
        job_title: str,
        company: str,
        status: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Send notification when application status changes."""
        status_emoji = {
            "applied": "📤",
            "interview_scheduled": "🎤",
            "interview_done": "✅",
            "offer": "🎉",
            "rejected": "❌",
            "withdrawn": "🚫",
        }.get(status, "📋")

        lines = [
            f"{status_emoji} <b>Application Update</b>",
            f"📝 {job_title} at {company}",
            f"Status: <b>{status.replace('_', ' ').title()}</b>",
        ]
        if notes:
            lines.append(f"📝 {notes}")

        return await self.send_message("\n".join(lines))

    async def send_followup_reminder(
        self,
        job_title: str,
        company: str,
        days_since: int,
    ) -> bool:
        """Send a follow-up reminder."""
        return await self.send_message(
            f"⏰ <b>Follow-up Reminder</b>\n"
            f"📝 {job_title} at {company}\n"
            f"Applied {days_since} days ago — consider following up!"
        )

    async def send_daily_digest(
        self,
        new_jobs_count: int,
        top_job: Optional[dict] = None,
        pending_followups: int = 0,
        upcoming_interviews: int = 0,
    ) -> bool:
        """Send a daily summary digest."""
        lines = [
            "📊 <b>Daily Career Digest</b>",
            "",
            f"🆕 New jobs found: {new_jobs_count}",
            f"⏰ Pending follow-ups: {pending_followups}",
            f"🎤 Upcoming interviews: {upcoming_interviews}",
        ]

        if top_job:
            lines.extend([
                "",
                "🏆 <b>Top Match Today:</b>",
                f"   {top_job.get('title', 'N/A')} at {top_job.get('company', 'N/A')}",
                f"   Match: {top_job.get('score', 0):.0f}% • {top_job.get('salary', 'N/A')}",
            ])

        lines.append("\n— CareerPilot AI")
        return await self.send_message("\n".join(lines))

    async def test_connection(self) -> dict:
        """Test Telegram bot connection."""
        if not self.token:
            return {"status": "error", "detail": "TELEGRAM_BOT_TOKEN not configured"}

        url = self.api_base.format(token=self.token, method="getMe")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                data = resp.json()

                if data.get("ok"):
                    bot_info = data.get("result", {})
                    return {
                        "status": "ok",
                        "bot_name": bot_info.get("username", "unknown"),
                        "chat_id_configured": bool(self.chat_id),
                    }
                return {"status": "error", "detail": data.get("description", "Unknown error")}
        except Exception as e:
            return {"status": "error", "detail": str(e)}


# Singleton
telegram_service = TelegramService()
