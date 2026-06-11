from __future__ import annotations

import logging
import os
import sys
import traceback

# QtWebEngine compatibility flags — must be set BEFORE QApplication / any
# QtWebEngine import so the embedded Chromium picks them up. Keeps the
# trailer popup working on machines with stale GPU drivers, in VMs, or
# under restrictive sandbox policies.
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu-driver-bug-workarounds --disable-features=UseChromeOSDirectVideoDecoder",
)
# Ensure QtWebEngineProcess.exe is found inside the PyInstaller bundle.
if getattr(sys, "frozen", False):
    _qt_bin = os.path.join(sys._MEIPASS, "PyQt6", "Qt6", "bin")
    _qt_proc = os.path.join(_qt_bin, "QtWebEngineProcess.exe")
    if os.path.exists(_qt_proc):
        os.environ.setdefault("QTWEBENGINEPROCESS_PATH", _qt_proc)
    _qt_resources = os.path.join(sys._MEIPASS, "PyQt6", "Qt6", "resources")
    if os.path.isdir(_qt_resources):
        os.environ.setdefault("QTWEBENGINE_RESOURCES_PATH", _qt_resources)
    _qt_locales = os.path.join(sys._MEIPASS, "PyQt6", "Qt6", "translations", "qtwebengine_locales")
    if os.path.isdir(_qt_locales):
        os.environ.setdefault("QTWEBENGINE_LOCALES_PATH", _qt_locales)

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from .core.logging_setup import configure_logging
from .core.paths import QSS_DIR, icon as icon_path
from .core.single_instance import SingleInstance
from .resources.strings_vi import APP_TITLE, DIALOG_ERROR_TITLE
from .widgets.loading_dialog import LoadingDialog


class _StartupWorker(QThread):
    """Resolve auth credentials + user profile off the GUI thread."""

    done = pyqtSignal(object, object)  # profile_or_None, creds_or_None

    def run(self) -> None:
        from .features.auth.google_auth import fetch_user_profile, load_credentials

        try:
            creds = load_credentials()
        except Exception:
            creds = None
        profile = None
        if creds:
            try:
                profile = fetch_user_profile(creds)
            except Exception:
                log.warning("Profile fetch failed — forcing re-auth")
                creds = None
        self.done.emit(profile, creds)


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

    configure_logging()
    _install_excepthook()
    LocalConfig().load()

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    # QtWebEngine (trailer popup) requires shared OpenGL contexts; must be
    # set BEFORE QApplication construction or QWebEngineView creation fails.
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
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

    # ── Resolve credentials before showing the window ─────────────
    from .features.auth.session import AuthSession

    splash = LoadingDialog(None)
    startup = _StartupWorker()
    startup_result: dict = {"profile": None, "creds": None}

    def _on_startup_done(profile, creds) -> None:
        startup_result["profile"] = profile
        startup_result["creds"] = creds
        splash.hide()
        splash.accept()

    startup.done.connect(_on_startup_done)
    startup.start()
    splash.exec()
    startup.wait()

    profile = startup_result["profile"]
    creds = startup_result["creds"]
    if profile and creds:
        AuthSession.set(profile, creds)

    # ── Single window, dual-page (login + shell) ─────────────────
    from .main_window import MainWindow
    window = MainWindow()
    window.show()

    if creds and profile:
        window.show_shell(profile)
    else:
        window.show_login()

    rc = app.exec()
    instance.release()
    return rc


if __name__ == "__main__":
    sys.exit(main())
