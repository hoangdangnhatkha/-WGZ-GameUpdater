"""Push edited config JSONs to the wgz-api backend.

Replaces the old GitHub Contents API push. Same public class name and signal
contract (`PushConfigWorker(games_raw, themes_raw, message)`) so the manager
view layer needs no changes.

The legacy `read_github_token()` / `GITHUB_TOKEN_FILE` paths are kept for
backwards-compat but are no longer used by the push flow.
"""
from __future__ import annotations

import logging

from PyQt6.QtCore import QThread, pyqtSignal

from ...core import api_client
from ...core.paths import GITHUB_TOKEN_FILE, find_github_token

log = logging.getLogger(__name__)


def read_github_token() -> str | None:
    """Legacy helper. No longer used by the push flow but kept for compatibility."""
    path = find_github_token()
    if path is None:
        return None
    try:
        t = path.read_text(encoding="utf-8").strip()
        return t or None
    except Exception:
        return None


class PushConfigWorker(QThread):
    """Push games + themes wholesale via `PUT /api/mods/bulk`."""

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
        try:
            self.status.emit("Đang đẩy cấu hình lên server...")
            payload: dict = dict(self._games_raw)
            if isinstance(self._themes_raw, dict) and self._themes_raw:
                payload["game_themes.json"] = self._themes_raw
            api_client.put_config_bulk(payload)
            self.finished_ok.emit()
        except Exception as exc:
            log.exception("Config push failed")
            self.failed.emit(str(exc))
