from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Iterable

from PyQt6.QtCore import QThread, pyqtSignal

log = logging.getLogger(__name__)

_KILL_TIMEOUT = 15      # max seconds to wait for Riot processes to exit
_LOGIN_TIMEOUT = 120    # max seconds to wait for the login window to appear

_RIOT_PROCESSES = [
    "RiotClientServices.exe",
    "RiotClientCrashHandler.exe",
]

_SESSION_FILE = Path(
    os.environ.get("LOCALAPPDATA", ""),
    "Riot Games", "Riot Client", "Data", "RiotGamesPrivateSettings.yaml",
)


class RiotLoginWorker(QThread):
    """Kill any running Riot Client, clear the login session, relaunch, and
    auto-fill credentials once the login screen appears.
    """

    status = pyqtSignal(str)
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(
        self,
        username: str,
        password: str,
        riot_exe_path: str | None = None,
        window_titles: Iterable[str] = ("Riot Client",),
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._username = username
        self._password = password
        self._riot_exe = Path(riot_exe_path) if riot_exe_path else None
        self._titles = list(window_titles)

    # ── Main entry ──────────────────────────────────────────────────

    def run(self) -> None:
        try:
            from pywinauto import Application, findwindows  # type: ignore
        except ImportError as exc:
            self.failed.emit(f"pywinauto chưa được cài: {exc}")
            return

        try:
            # 1. Force-close all Riot processes; poll until they're gone
            self.status.emit("Đang đóng Riot Client...")
            self._kill_riot_processes()
            if self._check_cancelled():
                return

            # 2. Delete session file so Riot shows the login screen on relaunch
            self.status.emit("Đang xoá phiên đăng nhập cũ...")
            self._clear_login_session()
            if self._check_cancelled():
                return

            # 3. Launch Riot Client
            if not self._launch_riot():
                return  # failed already emitted
            if self._check_cancelled():
                return

            # 4. Poll all candidate windows until one shows the login form
            self.status.emit("Đang đợi màn hình đăng nhập...")
            found = self._wait_for_login_window(findwindows, Application)
            if self._check_cancelled():
                return
            if not found:
                self.failed.emit(
                    f"Không tìm thấy màn hình đăng nhập Riot Client "
                    f"trong {_LOGIN_TIMEOUT}s."
                )
                return
            app, window = found
            try:
                window.set_focus()
            except Exception:
                pass

            # 5. Fill credentials
            self.status.emit("Đang điền tên đăng nhập...")
            self._type_into(window, "username", self._username)
            if self._check_cancelled():
                return

            self.status.emit("Đang điền mật khẩu...")
            self._type_into(window, "password", self._password)
            if self._check_cancelled():
                return

            self.status.emit("Đang tích 'Ghi nhớ đăng nhập'...")
            self._toggle_remember_me(window)
            if self._check_cancelled():
                return

            self.status.emit("Đang đăng nhập...")
            self._click_sign_in(window)

            self.finished_ok.emit()
        except Exception as exc:
            if self.isInterruptionRequested():
                self.cancelled.emit()
                return
            log.exception("Riot login failed")
            self.failed.emit(str(exc))

    def _check_cancelled(self) -> bool:
        if self.isInterruptionRequested():
            self.cancelled.emit()
            return True
        return False

    # ── Kill & clear ─────────────────────────────────────────────────

    def _kill_riot_processes(self) -> None:
        for proc in _RIOT_PROCESSES:
            try:
                subprocess.run(
                    ["taskkill", "/f", "/im", proc],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            except Exception:
                pass
        # Poll until all Riot processes are confirmed dead
        deadline = time.monotonic() + _KILL_TIMEOUT
        while time.monotonic() < deadline:
            if self.isInterruptionRequested():
                return
            if not self._riot_processes_running():
                return
            time.sleep(0.4)

    def _riot_processes_running(self) -> bool:
        try:
            result = subprocess.run(
                ["tasklist", "/fi", "IMAGENAME eq RiotClientServices.exe",
                 "/fo", "csv", "/nh"],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return "RiotClientServices.exe" in result.stdout
        except Exception:
            return False

    def _clear_login_session(self) -> None:
        try:
            if _SESSION_FILE.exists():
                _SESSION_FILE.unlink()
                log.info("Deleted Riot session file: %s", _SESSION_FILE)
        except Exception as exc:
            log.warning("Could not delete Riot session file: %s", exc)

    # ── Window discovery ────────────────────────────────────────────

    def _get_riot_pids(self) -> list[int]:
        """Return PIDs of running RiotClientServices.exe processes via tasklist."""
        try:
            result = subprocess.run(
                ["tasklist", "/fi", "IMAGENAME eq RiotClientServices.exe",
                 "/fo", "csv", "/nh"],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            pids: list[int] = []
            for line in result.stdout.strip().splitlines():
                parts = line.strip('"').split('","')
                if len(parts) >= 2:
                    try:
                        pids.append(int(parts[1]))
                    except ValueError:
                        pass
            return pids
        except Exception:
            return []

    def _candidate_handles(self, findwindows) -> list[int]:
        """Return all plausible Riot window handles to inspect, deduplicated."""
        seen: set[int] = set()
        handles: list[int] = []

        def _add(h: int | None) -> None:
            if h and h not in seen:
                seen.add(h)
                handles.append(h)

        # Title-matched windows
        for title in self._titles:
            try:
                for h in findwindows.find_windows(title_re=title):
                    _add(h)
            except Exception:
                continue

        # Windows owned by any Riot process
        for pid in self._get_riot_pids():
            try:
                for h in findwindows.find_windows(process=pid):
                    _add(h)
            except Exception:
                continue

        # Fuzzy title scan across all top-level visible windows
        try:
            for h in findwindows.find_windows(active_only=False):
                try:
                    text = (findwindows.element_info_class(h).name or "").lower()
                    if any(t.lower() in text for t in self._titles):
                        _add(h)
                except Exception:
                    continue
        except Exception:
            pass

        return handles

    def _launch_riot(self) -> bool:
        if not self._riot_exe or not self._riot_exe.exists():
            self.failed.emit(
                "Không tìm thấy Riot Client.\n"
                "Vui lòng cài đặt hoặc thiết lập đường dẫn trong Cài Đặt."
            )
            return False
        self.status.emit("Đang khởi động Riot Client...")
        try:
            subprocess.Popen(
                [str(self._riot_exe)],
                cwd=str(self._riot_exe.parent),
            )
            return True
        except Exception as exc:
            self.failed.emit(f"Không thể khởi động Riot Client: {exc}")
            return False

    # ── Login window detection ───────────────────────────────────────

    def _wait_for_login_window(self, findwindows, Application):
        """Poll all candidate windows until one shows the login form.

        Returns (app, window) on success, None on timeout. Combines window
        discovery and login-screen detection — necessary because Riot Client
        spawns multiple windows and only one of them hosts the login form.
        """
        deadline = time.monotonic() + _LOGIN_TIMEOUT
        while time.monotonic() < deadline:
            if self.isInterruptionRequested():
                return None
            for handle in self._candidate_handles(findwindows):
                try:
                    app = Application(backend="uia").connect(handle=handle)
                    window = app.window(handle=handle)
                    if self._is_login_screen(window):
                        return app, window
                except Exception:
                    continue
            time.sleep(0.7)
        return None

    def _is_login_screen(self, window) -> bool:
        try:
            return window.child_window(auto_id="username").exists()
        except Exception:
            return False

    # ── Checkbox & submit ────────────────────────────────────────────

    def _toggle_remember_me(self, window) -> None:
        try:
            cb = window.child_window(auto_id="remember-me")
            if cb.exists():
                cb.click_input()
        except Exception:
            pass

    def _click_sign_in(self, window) -> None:
        try:
            pwd = window.child_window(auto_id="password")
            pwd.click_input()
            time.sleep(0.05)
        except Exception:
            pass
        window.type_keys("{ENTER}", set_foreground=True)

    # ── Field input ─────────────────────────────────────────────────

    def _type_into(self, window, auto_id: str, text: str) -> None:
        try:
            ctrl = window.child_window(auto_id=auto_id)
            ctrl.click_input()
            time.sleep(0.08)
            ctrl.type_keys("^a", set_foreground=True)
            time.sleep(0.04)
            ctrl.type_keys(text, with_spaces=True, set_foreground=True)
            time.sleep(0.1)
        except Exception:
            if auto_id == "username":
                window.type_keys("^a", set_foreground=True)
                time.sleep(0.04)
                window.type_keys(text, with_spaces=True, set_foreground=True)
            elif auto_id == "password":
                window.type_keys("{TAB}", set_foreground=True)
                time.sleep(0.08)
                window.type_keys("^a", set_foreground=True)
                time.sleep(0.04)
                window.type_keys(text, with_spaces=True, set_foreground=True)
            time.sleep(0.1)
