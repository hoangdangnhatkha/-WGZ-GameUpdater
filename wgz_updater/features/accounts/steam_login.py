"""Steam auto-login worker.

Steam's `-login <user> <pass>` CLI parameter only takes effect when Steam is
NOT already running — if Steam is open, the launcher just signals the existing
instance and the flag is ignored. So this worker force-closes Steam first,
waits for the processes to fully exit, and then relaunches with the flag.
"""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

log = logging.getLogger(__name__)

_KILL_TIMEOUT = 20   # max seconds to wait for Steam processes to exit

# Killing steam.exe with /t (tree) also takes down steamwebhelper.exe children,
# but list both explicitly for safety on older Steam versions.
_STEAM_PROCESSES = [
    "steam.exe",
    "steamwebhelper.exe",
]


class SteamLoginWorker(QThread):
    """Kill any running Steam client, then relaunch with `-login` parameters."""

    status = pyqtSignal(str)
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(
        self,
        username: str,
        password: str,
        steam_exe_path: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._username = username
        self._password = password
        self._steam_exe = Path(steam_exe_path) if steam_exe_path else None

    # ── Main entry ──────────────────────────────────────────────────

    def run(self) -> None:
        try:
            if not self._steam_exe or not self._steam_exe.exists():
                self.failed.emit(
                    "Không tìm thấy Steam.\n"
                    "Vui lòng cài đặt hoặc thiết lập đường dẫn trong Cài Đặt."
                )
                return

            # 1. Force-close Steam; poll until processes are gone
            self.status.emit("Đang đóng Steam...")
            self._kill_steam_processes()
            if self._check_cancelled():
                return

            self.status.emit("Đang đợi Steam đóng hoàn toàn...")
            if not self._wait_until_dead():
                self.failed.emit(
                    f"Steam vẫn đang chạy sau {_KILL_TIMEOUT}s. "
                    "Hãy đóng Steam thủ công và thử lại."
                )
                return
            if self._check_cancelled():
                return

            # 2. Launch Steam with -login parameters
            self.status.emit("Đang khởi động Steam với tài khoản...")
            self._launch_with_login()

            self.status.emit("Steam đang xử lý đăng nhập...")
            self.finished_ok.emit()
        except Exception as exc:
            if self.isInterruptionRequested():
                self.cancelled.emit()
                return
            log.exception("Steam login failed")
            self.failed.emit(str(exc))

    def _check_cancelled(self) -> bool:
        if self.isInterruptionRequested():
            self.cancelled.emit()
            return True
        return False

    # ── Kill ─────────────────────────────────────────────────────────

    def _kill_steam_processes(self) -> None:
        for proc in _STEAM_PROCESSES:
            try:
                subprocess.run(
                    ["taskkill", "/f", "/t", "/im", proc],
                    capture_output=True,
                )
            except Exception:
                pass

    def _wait_until_dead(self) -> bool:
        deadline = time.monotonic() + _KILL_TIMEOUT
        while time.monotonic() < deadline:
            if self.isInterruptionRequested():
                return False
            if not self._steam_running():
                return True
            time.sleep(0.4)
        return False

    def _steam_running(self) -> bool:
        try:
            result = subprocess.run(
                ["tasklist", "/fi", "IMAGENAME eq steam.exe",
                 "/fo", "csv", "/nh"],
                capture_output=True, text=True,
            )
            return "steam.exe" in result.stdout.lower()
        except Exception:
            return False

    # ── Launch ──────────────────────────────────────────────────────

    def _launch_with_login(self) -> None:
        subprocess.Popen(
            [str(self._steam_exe), "-login", self._username, self._password],
            cwd=str(self._steam_exe.parent),
        )
