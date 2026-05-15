"""Push edited config JSONs back to the source repo via the GitHub Contents API.

Requires a PAT with `contents:write` scope on `hoangdangnhatkha/-WGZ-GameUpdater`,
configured in Cài Đặt → GitHub Token.
"""

from __future__ import annotations

import base64
import json
import logging

from PyQt6.QtCore import QThread, pyqtSignal

from ...core.http import client
from ...core.paths import GITHUB_TOKEN_FILE

log = logging.getLogger(__name__)

_OWNER = "hoangdangnhatkha"
_REPO = "-WGZ-GameUpdater"
_BRANCH = "main"
_API = "https://api.github.com"

GAMES_FILE = "CapNhatNightReignMod.json"
THEMES_FILE = "game_themes.json"


def read_github_token() -> str | None:
    if not GITHUB_TOKEN_FILE.exists():
        return None
    try:
        t = GITHUB_TOKEN_FILE.read_text(encoding="utf-8").strip()
        return t or None
    except Exception:
        return None


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_file_sha(token: str, path: str) -> str | None:
    url = f"{_API}/repos/{_OWNER}/{_REPO}/contents/{path}?ref={_BRANCH}"
    resp = client().get(url, headers=_headers(token))
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json().get("sha")


def _put_file(
    token: str, path: str, content_bytes: bytes, sha: str | None, message: str
) -> None:
    url = f"{_API}/repos/{_OWNER}/{_REPO}/contents/{path}"
    payload: dict = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode("ascii"),
        "branch": _BRANCH,
    }
    if sha:
        payload["sha"] = sha
    resp = client().put(url, headers=_headers(token), json=payload)
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("message", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(f"GitHub {resp.status_code}: {detail}")


class PushConfigWorker(QThread):
    """Pushes games + themes JSON in a single commit pair."""

    status = pyqtSignal(str)
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(
        self,
        games_raw: dict,
        themes_raw: dict,
        message: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._games_raw = games_raw
        self._themes_raw = themes_raw
        self._message = message or "chore: update config via WGZ manager"

    def run(self) -> None:
        token = read_github_token()
        if not token:
            self.failed.emit(
                "Chưa cài GitHub Token.\n"
                "Vào Cài Đặt → GitHub Token để nhập PAT có quyền contents:write."
            )
            return
        try:
            self.status.emit("Lấy SHA hiện tại...")
            games_sha = _get_file_sha(token, GAMES_FILE)
            themes_sha = _get_file_sha(token, THEMES_FILE)

            games_bytes = json.dumps(
                self._games_raw, ensure_ascii=False, indent=2
            ).encode("utf-8")
            themes_bytes = json.dumps(
                self._themes_raw, ensure_ascii=False, indent=2
            ).encode("utf-8")

            self.status.emit(f"Đẩy {GAMES_FILE}...")
            _put_file(token, GAMES_FILE, games_bytes, games_sha, self._message)

            self.status.emit(f"Đẩy {THEMES_FILE}...")
            _put_file(token, THEMES_FILE, themes_bytes, themes_sha, self._message)

            self.finished_ok.emit()
        except Exception as exc:
            log.exception("Config push failed")
            self.failed.emit(str(exc))
