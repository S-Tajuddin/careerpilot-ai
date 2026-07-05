"""
CareerPilot AI — Google Sheets Sync Service
One-way sync: SQLite → Google Sheets (view/edit layer on phone).
Uses gspread with service account authentication.

Setup:
1. Go to https://console.cloud.google.com
2. Create a project → Enable Google Sheets API + Google Drive API
3. Create Service Account → Download JSON key file
4. Share your Google Sheet with the service account email
5. Set GOOGLE_SHEETS_CREDENTIALS_FILE and GOOGLE_SHEETS_SPREADSHEET_ID in .env
"""

import json
from datetime import datetime
from typing import Optional

from app.config import settings


class SheetsService:
    """
    One-way sync from SQLite to Google Sheets.
    Your phone can view/edit the sheet — changes are not synced back.
    """

    def __init__(self):
        self.credentials_file = settings.google_sheets_credentials_file
        self.spreadsheet_id = settings.google_sheets_spreadsheet_id
        self._client = None
        self._spreadsheet = None

    @property
    def is_configured(self) -> bool:
        """Check if Google Sheets is properly configured."""
        return bool(self.credentials_file and self.spreadsheet_id)

    @property
    def client(self):
        """Lazy-init gspread client."""
        if self._client is None and self.is_configured:
            try:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]

                creds = Credentials.from_service_account_file(
                    self.credentials_file, scopes=scopes
                )
                self._client = gspread.authorize(creds)
            except Exception as e:
                print(f"Google Sheets auth error: {e}")
                return None
        return self._client

    @property
    def spreadsheet(self):
        """Lazy-init spreadsheet."""
        if self._spreadsheet is None and self.client:
            try:
                self._spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            except Exception as e:
                print(f"Google Sheets open error: {e}")
                return None
        return self._spreadsheet

    def sync_applications(self, rows: list[dict]) -> bool:
        """
        Sync application data to Google Sheets.
        Replaces the 'Applications' sheet with current data.
        """
        if not self.spreadsheet:
            return False

        try:
            # Get or create worksheet
            try:
                ws = self.spreadsheet.worksheet("Applications")
                ws.clear()
            except Exception:
                ws = self.spreadsheet.add_worksheet(
                    title="Applications", rows=1, cols=10
                )

            if not rows:
                return True

            # Header row
            headers = list(rows[0].keys())
            all_data = [headers]

            # Data rows
            for row in rows:
                all_data.append([row.get(h, "") for h in headers])

            # Write all at once
            ws.update(range_name="A1", values=all_data)

            # Auto-resize columns
            try:
                ws.columns_auto_resize(0, len(headers))
            except Exception:
                pass  # Non-critical

            print(f"  📊 Synced {len(rows)} rows to Google Sheets")
            return True

        except Exception as e:
            print(f"Google Sheets sync error: {e}")
            return False

    def sync_jobs(self, rows: list[dict]) -> bool:
        """Sync job data to Google Sheets (Jobs sheet)."""
        if not self.spreadsheet:
            return False

        try:
            try:
                ws = self.spreadsheet.worksheet("Jobs")
                ws.clear()
            except Exception:
                ws = self.spreadsheet.add_worksheet(title="Jobs", rows=1, cols=10)

            if not rows:
                return True

            headers = list(rows[0].keys())
            all_data = [headers]

            for row in rows:
                all_data.append([row.get(h, "") for h in headers])

            ws.update(range_name="A1", values=all_data)

            try:
                ws.columns_auto_resize(0, len(headers))
            except Exception:
                pass

            print(f"  📊 Synced {len(rows)} jobs to Google Sheets")
            return True

        except Exception as e:
            print(f"Google Sheets sync error: {e}")
            return False

    def create_sheet_if_needed(self) -> dict:
        """
        Create a new Google Sheet with proper structure if one doesn't exist.
        Returns spreadsheet info.
        """
        if not self.client:
            return {"status": "error", "detail": "Google Sheets client not initialized"}

        try:
            if self.spreadsheet:
                return {
                    "status": "ok",
                    "spreadsheet_id": self.spreadsheet_id,
                    "title": self.spreadsheet.title,
                    "url": f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}",
                }

            # Create new spreadsheet
            ss = self.client.create("CareerPilot AI - Job Tracker")
            self._spreadsheet = ss

            # Update .env with new spreadsheet ID
            print(f"  📊 Created new Google Sheet: {ss.title}")
            print(f"  Share this sheet with your service account email")

            return {
                "status": "created",
                "spreadsheet_id": ss.id,
                "title": ss.title,
                "url": f"https://docs.google.com/spreadsheets/d/{ss.id}",
            }

        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def get_status(self) -> dict:
        """Get Google Sheets connection status."""
        if not self.is_configured:
            return {
                "configured": False,
                "detail": "Set GOOGLE_SHEETS_CREDENTIALS_FILE and GOOGLE_SHEETS_SPREADSHEET_ID in .env",
            }

        if self.client and self.spreadsheet:
            return {
                "configured": True,
                "connected": True,
                "title": self.spreadsheet.title,
                "url": f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}",
            }

        return {
            "configured": True,
            "connected": False,
            "detail": "Auth failed — check credentials file",
        }


# Singleton
sheets_service = SheetsService()
