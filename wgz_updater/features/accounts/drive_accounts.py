from __future__ import annotations

import io
import json
import logging

from ...core.paths import CREDENTIALS_FILE, TOKEN_FILE, find_credentials

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]
ACCOUNTS_FILENAME = "wgz_user_accounts.json"
GOOGLE_DRIVE_FOLDER_ID = "1lO7qc485mhdLpirFgyhqMGKXAQvHoQYA"


class DriveAccountsService:
    """Read/write `wgz_user_accounts.json` in a Google Drive folder.

    File format (matches the original tkinter app):
        {
          "<game_name>": [
            {"nickname": "...", "username": "...", "password": "...",
             "type": "steam|riot|...", "game": "<game_name>"},
            ...
          ]
        }
    """

    def __init__(self, folder_id: str = GOOGLE_DRIVE_FOLDER_ID) -> None:
        self._folder_id = folder_id
        self._service = None
        self._file_id: str | None = None

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
                creds_path = find_credentials()
                if creds_path is None:
                    raise FileNotFoundError(f"Missing {CREDENTIALS_FILE}")
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)
            try:
                TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            except Exception:
                log.exception("Writing token")

        self._service = build("drive", "v3", credentials=creds)
        return self._service

    def _find_file(self) -> str | None:
        if self._file_id:
            return self._file_id
        svc = self._ensure_service()
        q = (
            f"name = '{ACCOUNTS_FILENAME}' and "
            f"'{self._folder_id}' in parents and trashed = false"
        )
        result = svc.files().list(q=q, spaces="drive", fields="files(id,name)").execute()
        files = result.get("files", [])
        if files:
            self._file_id = files[0]["id"]
        return self._file_id

    def fetch(self) -> dict[str, list[dict]]:
        svc = self._ensure_service()
        file_id = self._find_file()
        if not file_id:
            return {}
        from googleapiclient.http import MediaIoBaseDownload

        request = svc.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _status, done = downloader.next_chunk()
        try:
            data = json.loads(buf.getvalue().decode("utf-8"))
        except Exception:
            log.exception("Failed parsing accounts file")
            return {}
        if not isinstance(data, dict):
            return {}
        return data

    def push(self, data: dict[str, list[dict]]) -> None:
        svc = self._ensure_service()
        from googleapiclient.http import MediaIoBaseUpload

        body_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        media = MediaIoBaseUpload(
            io.BytesIO(body_bytes), mimetype="application/json", resumable=False
        )
        file_id = self._find_file()
        if file_id:
            svc.files().update(fileId=file_id, media_body=media).execute()
        else:
            metadata = {
                "name": ACCOUNTS_FILENAME,
                "parents": [self._folder_id],
                "mimeType": "application/json",
            }
            created = svc.files().create(
                body=metadata, media_body=media, fields="id"
            ).execute()
            self._file_id = created.get("id")
