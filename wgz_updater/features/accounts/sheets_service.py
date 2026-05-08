from __future__ import annotations

import logging
from pathlib import Path

from ...core.paths import CREDENTIALS_FILE, TOKEN_FILE
from .models import AccountRecord

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsService:
    def __init__(self, spreadsheet_id: str, range_name: str = "Sheet1!A:D") -> None:
        self._spreadsheet_id = spreadsheet_id
        self._range = range_name
        self._service = None

    def _ensure_service(self):
        if self._service is not None:
            return self._service
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError(f"Google API client not installed: {exc}") from exc

        creds = None
        if TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            except Exception:
                log.exception("Reading token")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    log.exception("Refreshing token")
                    creds = None
            if not creds:
                if not CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(f"Missing {CREDENTIALS_FILE}")
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                creds = flow.run_local_server(port=0)
            try:
                TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            except Exception:
                log.exception("Writing token")

        self._service = build("sheets", "v4", credentials=creds)
        return self._service

    def fetch_accounts(self) -> list[AccountRecord]:
        service = self._ensure_service()
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=self._spreadsheet_id, range=self._range)
            .execute()
        )
        rows = result.get("values", [])
        return [AccountRecord.from_row(r) for r in rows if r]

    def write_accounts(self, records: list[AccountRecord]) -> None:
        service = self._ensure_service()
        body = {"values": [r.to_row() for r in records]}
        service.spreadsheets().values().clear(
            spreadsheetId=self._spreadsheet_id, range=self._range
        ).execute()
        service.spreadsheets().values().update(
            spreadsheetId=self._spreadsheet_id,
            range=self._range,
            valueInputOption="RAW",
            body=body,
        ).execute()
