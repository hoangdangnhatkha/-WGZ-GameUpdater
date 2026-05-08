from __future__ import annotations

import logging
import time
from typing import Iterable

from PyQt6.QtCore import QThread, pyqtSignal

log = logging.getLogger(__name__)


class RiotLoginWorker(QThread):
    """Locate the Riot Client window via UI Automation and type credentials.

    Uses pywinauto, which queries the UI Automation tree by control name/role
    instead of pixel-driven keystrokes. Far more reliable than pyautogui.
    """

    status = pyqtSignal(str)
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(
        self,
        username: str,
        password: str,
        window_titles: Iterable[str] = ("Riot Client",),
        username_ctrl: str = "Edit1",
        password_ctrl: str = "Edit2",
        submit_ctrl: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._username = username
        self._password = password
        self._titles = list(window_titles)
        self._username_ctrl = username_ctrl
        self._password_ctrl = password_ctrl
        self._submit_ctrl = submit_ctrl

    def run(self) -> None:
        try:
            from pywinauto import Application, findwindows  # type: ignore
        except ImportError as exc:
            self.failed.emit(f"pywinauto chưa được cài: {exc}")
            return

        try:
            self.status.emit("Đang tìm cửa sổ Riot Client...")
            handle = self._find_window(findwindows)
            if not handle:
                self.failed.emit("Không tìm thấy cửa sổ Riot Client.")
                return

            app = Application(backend="uia").connect(handle=handle)
            window = app.window(handle=handle)
            window.set_focus()

            self.status.emit("Đang điền tên đăng nhập...")
            self._type_into(window, self._username_ctrl, self._username)

            self.status.emit("Đang điền mật khẩu...")
            self._type_into(window, self._password_ctrl, self._password)

            if self._submit_ctrl:
                self.status.emit("Đang gửi đăng nhập...")
                window.child_window(auto_id=self._submit_ctrl).click_input()

            self.finished_ok.emit()
        except Exception as exc:
            log.exception("Riot login failed")
            self.failed.emit(str(exc))

    def _find_window(self, findwindows) -> int | None:
        for title in self._titles:
            try:
                handles = findwindows.find_windows(title_re=title)
                if handles:
                    return handles[0]
            except Exception:
                continue
        return None

    def _type_into(self, window, control_name: str, text: str) -> None:
        try:
            ctrl = window.child_window(auto_id=control_name)
            ctrl.click_input()
            ctrl.type_keys(text, with_spaces=True, set_foreground=True)
        except Exception:
            window.type_keys(text, with_spaces=True, set_foreground=True)
            time.sleep(0.1)
