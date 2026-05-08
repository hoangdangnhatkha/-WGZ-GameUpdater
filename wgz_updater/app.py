from __future__ import annotations

import logging
import sys
import traceback

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from .core.logging_setup import configure_logging
from .core.paths import QSS_DIR, icon as icon_path
from .core.single_instance import SingleInstance
from .main_window import MainWindow
from .resources.strings_vi import APP_TITLE, DIALOG_ERROR_TITLE

log = logging.getLogger(__name__)


def _install_excepthook() -> None:
    def hook(exc_type, exc_value, exc_tb):
        log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
        try:
            QMessageBox.critical(
                None,
                DIALOG_ERROR_TITLE,
                "".join(traceback.format_exception(exc_type, exc_value, exc_tb))[-1500:],
            )
        except Exception:
            pass

    sys.excepthook = hook


def _load_qss(app: QApplication) -> None:
    qss_path = QSS_DIR / "styles.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def _install_app_icon(app: QApplication) -> None:
    ico = icon_path("logo.ico")
    png = icon_path("logo.png")
    if ico.exists():
        app.setWindowIcon(QIcon(str(ico)))
    elif png.exists():
        app.setWindowIcon(QIcon(str(png)))


def main() -> int:
    from .core.local_config import LocalConfig
    from .core.win32_utils import elevate_and_relaunch, is_admin

    # Admin elevation — must happen before QApplication
    if not is_admin():
        launched = elevate_and_relaunch()
        if launched:
            return 0

    configure_logging()
    _install_excepthook()

    # Load persisted settings
    LocalConfig().load()

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setOrganizationName("WGZ")
    app.setFont(QFont("Segoe UI Variable", 10))

    instance = SingleInstance()
    if instance.already_running:
        log.info("Another instance detected — focusing existing window")
        instance.focus_existing()
        return 0

    _install_app_icon(app)
    _load_qss(app)

    window = MainWindow()
    window.show()

    try:
        from .features.library.view import LibraryView
        window.install_view("library", LibraryView(window))
    except Exception:
        log.exception("Library view failed to load")

    try:
        from .features.accounts.view import AccountsView
        window.install_view("accounts", AccountsView(window))
    except Exception:
        log.exception("Accounts view failed to load")

    try:
        from .features.settings.view import SettingsView
        window.install_view("settings", SettingsView(window))
    except Exception:
        log.exception("Settings view failed to load")

    try:
        from .widgets.status_strip import StatusStrip
        window.install_status_strip(StatusStrip(window))
    except Exception:
        log.exception("Status strip failed to load")

    # Background: auto-detect Steam/Riot paths
    try:
        from .core.auto_path import AutoPathWorker
        auto = AutoPathWorker(app)
        auto.steam_found.connect(lambda p: log.info("Steam path set: %s", p))
        auto.riot_found.connect(lambda p: log.info("Riot path set: %s", p))
        auto.start()
    except Exception:
        log.exception("AutoPathWorker failed to start")

    rc = app.exec()
    instance.release()
    return rc


if __name__ == "__main__":
    sys.exit(main())
