from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .core.win32_utils import enable_mica
from .resources.strings_vi import APP_TITLE, NAV_ACCOUNTS, NAV_LIBRARY, NAV_SETTINGS
from .widgets.sidebar import NavItem, Sidebar
from .widgets.title_bar import TitleBar

log = logging.getLogger(__name__)

NAV_KEYS = ("library", "accounts", "settings")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1180, 740)
        self.setMinimumSize(960, 600)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        root = QWidget(self)
        root.setObjectName("MainRoot")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.title_bar = TitleBar(self)
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.maximize_toggled.connect(self._toggle_max)
        self.title_bar.close_requested.connect(self.close)
        outer.addWidget(self.title_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = Sidebar(
            [
                NavItem("library", NAV_LIBRARY, "▣"),
                NavItem("accounts", NAV_ACCOUNTS, "◉"),
                NavItem("settings", NAV_SETTINGS, "⚙"),
            ],
            self,
        )
        self.sidebar.nav_changed.connect(self._on_nav)
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget(self)
        body.addWidget(self.stack, 1)

        outer.addLayout(body, 1)

        self._views: dict[str, QWidget] = {}
        for key in NAV_KEYS:
            placeholder = QWidget(self)
            self.stack.addWidget(placeholder)
            self._views[key] = placeholder

        self.status_strip: QWidget | None = None

    def install_view(self, key: str, view: QWidget) -> None:
        old = self._views.get(key)
        if old is not None:
            idx = self.stack.indexOf(old)
            self.stack.removeWidget(old)
            old.deleteLater()
        self.stack.insertWidget(NAV_KEYS.index(key), view)
        self._views[key] = view
        if key == "library":
            self.stack.setCurrentWidget(view)

    def install_status_strip(self, strip: QWidget) -> None:
        if self.status_strip is not None:
            return
        self.status_strip = strip
        layout = self.centralWidget().layout()
        if isinstance(layout, QVBoxLayout):
            layout.addWidget(strip)

    def _on_nav(self, key: str) -> None:
        view = self._views.get(key)
        if view is not None:
            self.stack.setCurrentWidget(view)

    def _toggle_max(self) -> None:
        if self.isMaximized():
            self.showNormal()
            self.title_bar.set_maximized(False)
        else:
            self.showMaximized()
            self.title_bar.set_maximized(True)

    def showEvent(self, event) -> None:  # noqa: D401
        super().showEvent(event)
        try:
            hwnd = int(self.winId())
            enable_mica(hwnd, dark=True)
        except Exception:
            log.exception("Failed to enable Mica")

    def closeEvent(self, event: QCloseEvent) -> None:
        log.info("Main window closing")
        super().closeEvent(event)
