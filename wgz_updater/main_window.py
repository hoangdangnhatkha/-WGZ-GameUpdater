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

# enable_mica intentionally not imported; Mica is disabled for lightweight UX.
from .resources.strings_vi import (
    APP_TITLE,
    NAV_ACCOUNTS,
    NAV_LIBRARY,
    NAV_MANAGER,
    NAV_SETTINGS,
)
from .widgets.sidebar import NavItem, Sidebar
from .widgets.title_bar import TitleBar

log = logging.getLogger(__name__)

NAV_KEYS = ("library", "accounts", "manager", "settings")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setFixedSize(1280, 800)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        root = QWidget(self)
        root.setObjectName("MainRoot")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.title_bar = TitleBar(self, show_maximize=False)
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.close_requested.connect(self.close)
        self.title_bar.support_requested.connect(self._on_support_requested)
        outer.addWidget(self.title_bar)

        from .features.support import SupportController
        self._support_controller = SupportController(self)

        # Outer stack: index 0 = login page, index 1 = shell (sidebar + views)
        self.outer_stack = QStackedWidget(self)
        outer.addWidget(self.outer_stack, 1)

        # ── Login page ──────────────────────────────────────────
        from .features.auth.login_page import LoginPage
        self.login_page = LoginPage(self)
        self.login_page.authenticated.connect(self._on_authenticated)
        self.outer_stack.addWidget(self.login_page)

        # ── Shell page ──────────────────────────────────────────
        self.shell = QWidget(self)
        self.shell.setObjectName("MainShell")
        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        shell_body = QHBoxLayout()
        shell_body.setContentsMargins(0, 0, 0, 0)
        shell_body.setSpacing(0)

        self._shell_body_layout = shell_body
        self._shell_outer_layout = shell_layout

        self.stack = QStackedWidget(self.shell)
        shell_body.addWidget(self.stack, 1)
        shell_layout.addLayout(shell_body, 1)

        self.outer_stack.addWidget(self.shell)

        self.sidebar: Sidebar | None = None
        self._views: dict[str, QWidget] = {}
        self.status_strip: QWidget | None = None
        self._auto_path_worker = None

    # ── Page swap helpers ─────────────────────────────────────────

    def show_login(self) -> None:
        self.login_page.reset()
        self.outer_stack.setCurrentWidget(self.login_page)

    def show_shell(self, profile) -> None:
        self._build_shell(profile)
        self.outer_stack.setCurrentWidget(self.shell)

    # ── Shell build / teardown ────────────────────────────────────

    def _build_shell(self, profile) -> None:
        """(Re)build sidebar + views for the given user. Idempotent — tears down first."""
        self._teardown_shell()

        # Sidebar
        self.sidebar = Sidebar(
            [
                NavItem("library", NAV_LIBRARY, "▣"),
                NavItem("accounts", NAV_ACCOUNTS, "◉"),
                NavItem("manager", NAV_MANAGER, "▤"),
                NavItem("settings", NAV_SETTINGS, "⚙"),
            ],
            self.shell,
            user_profile=profile,
        )
        self.sidebar.nav_changed.connect(self._on_nav)
        self.sidebar.logout_requested.connect(self._on_logout)
        self._shell_body_layout.insertWidget(0, self.sidebar)

        # Placeholder views (replaced by install_view)
        self._views = {}
        for key in NAV_KEYS:
            placeholder = QWidget(self.shell)
            self.stack.addWidget(placeholder)
            self._views[key] = placeholder

        self._install_feature_views()
        self._install_status_strip()
        self._start_auto_path_worker()

    def _teardown_shell(self) -> None:
        """Remove sidebar + status strip + views so shell can be rebuilt cleanly."""
        if self.sidebar is not None:
            try:
                self.sidebar.nav_changed.disconnect()
                self.sidebar.logout_requested.disconnect()
            except TypeError:
                pass
            self._shell_body_layout.removeWidget(self.sidebar)
            self.sidebar.deleteLater()
            self.sidebar = None

        if self.status_strip is not None:
            self._shell_outer_layout.removeWidget(self.status_strip)
            self.status_strip.deleteLater()
            self.status_strip = None

        for key, view in list(self._views.items()):
            self.stack.removeWidget(view)
            view.deleteLater()
        self._views.clear()

    def _install_feature_views(self) -> None:
        try:
            from .features.library.view import LibraryView
            self.install_view("library", LibraryView(self.shell))
        except Exception:
            log.exception("Library view failed to load")

        try:
            from .features.accounts.view import AccountsView
            self.install_view("accounts", AccountsView(self.shell))
        except Exception:
            log.exception("Accounts view failed to load")

        try:
            from .features.manager.view import ManagerView
            self.install_view("manager", ManagerView(self.shell))
        except Exception:
            log.exception("Manager view failed to load")

        try:
            from .features.settings.view import SettingsView
            self.install_view("settings", SettingsView(self.shell))
        except Exception:
            log.exception("Settings view failed to load")

    def _install_status_strip(self) -> None:
        try:
            from .widgets.status_strip import StatusStrip
            strip = StatusStrip(self.shell)
            self.status_strip = strip
            self._shell_outer_layout.addWidget(strip)
        except Exception:
            log.exception("Status strip failed to load")

    def _start_auto_path_worker(self) -> None:
        # Run once per process — discovers Steam/Riot install paths.
        if self._auto_path_worker is not None:
            return
        try:
            from .core.auto_path import AutoPathWorker
            from PyQt6.QtWidgets import QApplication
            worker = AutoPathWorker(QApplication.instance())
            worker.steam_found.connect(lambda p: log.info("Steam path set: %s", p))
            worker.riot_found.connect(lambda p: log.info("Riot path set: %s", p))
            worker.start()
            self._auto_path_worker = worker
        except Exception:
            log.exception("AutoPathWorker failed to start")

    # ── View API ──────────────────────────────────────────────────

    def install_view(self, key: str, view: QWidget) -> None:
        old = self._views.get(key)
        if old is not None:
            self.stack.removeWidget(old)
            old.deleteLater()
        self.stack.insertWidget(NAV_KEYS.index(key), view)
        self._views[key] = view
        if key == "library":
            self.stack.setCurrentWidget(view)

    def _on_nav(self, key: str) -> None:
        view = self._views.get(key)
        if view is not None:
            self.stack.setCurrentWidget(view)

    # ── Auth transitions ──────────────────────────────────────────

    def _on_authenticated(self, profile, credentials) -> None:
        from .features.auth.session import AuthSession
        AuthSession.set(profile, credentials)
        self.show_shell(profile)

    def _on_support_requested(self) -> None:
        self._support_controller.request_support()

    def _on_logout(self) -> None:
        # Sidebar already cleared on-disk token + AuthSession before emitting.
        self._teardown_shell()
        self.show_login()

    # ── Window lifecycle ──────────────────────────────────────────

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Mica intentionally disabled: DWM blur adds GPU + memory cost on weak
        # devices for no functional benefit. The window uses a solid background
        # painted by QSS.

    def closeEvent(self, event: QCloseEvent) -> None:
        log.info("Main window closing")
        super().closeEvent(event)
