from __future__ import annotations

import logging

from PyQt6.QtCore import QThread, pyqtSignal

from ...core.paths import CREDENTIALS_FILE, USER_TOKEN_FILE, find_credentials

log = logging.getLogger(__name__)

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.readonly",
]


def load_credentials():
    """Return valid Credentials from disk, refreshing if expired. Returns None if not found."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        if not USER_TOKEN_FILE.exists():
            return None

        creds = Credentials.from_authorized_user_file(str(USER_TOKEN_FILE), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_credentials(creds)
        return creds if creds.valid else None
    except Exception as exc:
        log.warning("Could not load saved credentials: %s", exc)
        return None


def save_credentials(creds) -> None:
    try:
        USER_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        USER_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    except Exception as exc:
        log.error("Failed to save credentials: %s", exc)


def clear_credentials() -> None:
    try:
        if USER_TOKEN_FILE.exists():
            USER_TOKEN_FILE.unlink()
    except Exception as exc:
        log.error("Failed to clear credentials: %s", exc)


def fetch_user_profile(credentials) -> "UserProfile":
    from .models import UserProfile
    import httpx

    headers = {"Authorization": f"Bearer {credentials.token}"}
    resp = httpx.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return UserProfile(
        email=data.get("email", ""),
        name=data.get("name", ""),
        given_name=data.get("given_name", ""),
        picture_url=data.get("picture", ""),
    )


class GoogleAuthWorker(QThread):
    authenticated = pyqtSignal(object, object)  # UserProfile, Credentials
    failed = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def run(self) -> None:
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow

            creds_path = find_credentials()
            if creds_path is None:
                self.failed.emit(
                    f"Không tìm thấy file credentials.json tại:\n{CREDENTIALS_FILE}\n\n"
                    "Vui lòng đặt file OAuth credentials của Google vào thư mục trên."
                )
                return

            self.status_update.emit("Đang mở trình duyệt Google...")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            credentials = flow.run_local_server(port=0, open_browser=True)
            save_credentials(credentials)

            self.status_update.emit("Đang lấy thông tin tài khoản...")
            profile = fetch_user_profile(credentials)
            self.authenticated.emit(profile, credentials)

        except Exception as exc:
            log.exception("Google auth failed")
            self.failed.emit(str(exc))
