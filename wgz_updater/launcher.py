from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from .core.http import get_json
from .core.logging_setup import configure_logging
from .core.paths import (
    APP_DIR,
    GITHUB_JSON_URL,
    INSTALL_ROOT,
    MAIN_EXE_NAME,
    QSS_DIR,
    VERSION_FILE,
    ensure_user_dirs,
    icon as icon_path,
)
from .core.updater import is_remote_newer, set_local_version
from .core.win32_utils import enable_mica
from .resources.strings_vi import (
    SPLASH_BOOTING,
    SPLASH_CHECKING_VERSION,
    SPLASH_DONE,
    SPLASH_DOWNLOADING,
    SPLASH_EXTRACTING,
    SPLASH_OFFLINE,
)

log = logging.getLogger(__name__)


class BootstrapWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    ready_to_launch = pyqtSignal()

    def run(self) -> None:
        try:
            ensure_user_dirs()
            self.status.emit(SPLASH_CHECKING_VERSION)
            self.progress.emit(10)

            try:
                cfg = get_json(GITHUB_JSON_URL, cachebust=True)
            except Exception as exc:
                log.warning("Network failed: %s", exc)
                self.status.emit(SPLASH_OFFLINE)
                time.sleep(1)
                self.ready_to_launch.emit()
                return

            updater = cfg.get("updater", {}) or {}
            remote_version = updater.get("latest_version", "0.0.0")
            download_url = updater.get("base_url") or updater.get("download_url")
            main_exe = APP_DIR / MAIN_EXE_NAME

            if not is_remote_newer(remote_version) and main_exe.exists():
                self.progress.emit(100)
                self.ready_to_launch.emit()
                return

            if not download_url:
                self.error.emit("Không tìm thấy link tải.")
                return

            try:
                import gdown
            except ImportError:
                self.error.emit("gdown chưa được cài đặt.")
                return

            tmp = Path(tempfile.gettempdir()) / "wgz_base_update.zip"
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass

            self.status.emit(SPLASH_DOWNLOADING.format(percent=0))
            try:
                output = gdown.download(download_url, str(tmp), quiet=True, fuzzy=True, resume=True)
            except Exception as exc:
                self.error.emit(f"Lỗi tải: {exc}")
                return
            if not output or not tmp.exists():
                self.error.emit("Tải thất bại.")
                return

            self.status.emit(SPLASH_EXTRACTING)
            self.progress.emit(85)

            if APP_DIR.exists():
                try:
                    shutil.rmtree(APP_DIR)
                except Exception:
                    log.warning("Could not clear %s", APP_DIR)

            with zipfile.ZipFile(tmp, "r") as zf:
                zf.extractall(INSTALL_ROOT)

            set_local_version(remote_version)
            try:
                tmp.unlink()
            except OSError:
                pass

            self.progress.emit(100)
            self.status.emit(SPLASH_DONE)
            time.sleep(0.5)
            self.ready_to_launch.emit()
        except Exception as exc:
            log.exception("Bootstrap failed")
            self.error.emit(str(exc))


class SplashWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WGZ Launcher")
        self.setFixedSize(380, 240)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        frame = QFrame(self)
        frame.setObjectName("MainRoot")
        frame.setStyleSheet(
            "QFrame#MainRoot { background: rgba(32, 32, 32, 0.95);"
            " border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; }"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        logo = icon_path("logo.png")
        if logo.exists():
            label = QLabel(self)
            pix = QPixmap(str(logo)).scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            label.setPixmap(pix)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)

        title = QLabel("WGZ Game Updater", self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #f3f3f3; font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        self.status_label = QLabel(SPLASH_BOOTING, self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #d8d8d8;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(
            "QProgressBar { background: rgba(255,255,255,0.08); border: none;"
            " border-radius: 4px; height: 6px; }"
            "QProgressBar::chunk { background: #0078d4; border-radius: 4px; }"
        )
        layout.addWidget(self.progress)

        self._center()

    def _center(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    def showEvent(self, event) -> None:
        super().showEvent(event)
        try:
            enable_mica(int(self.winId()), dark=True)
        except Exception:
            pass


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)

    qss = QSS_DIR / "styles.qss"
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))

    splash = SplashWindow()
    splash.show()

    worker = BootstrapWorker()
    worker.progress.connect(splash.progress.setValue)
    worker.status.connect(splash.status_label.setText)

    def on_error(msg: str) -> None:
        QMessageBox.critical(splash, "Lỗi", msg)
        app.quit()

    def on_ready() -> None:
        exe = APP_DIR / MAIN_EXE_NAME
        if exe.exists():
            try:
                subprocess.Popen([str(exe)], cwd=str(exe.parent))
            except Exception as exc:
                QMessageBox.critical(splash, "Lỗi", f"Không thể khởi động: {exc}")
        else:
            QMessageBox.critical(splash, "Lỗi", f"Không tìm thấy: {exe}")
        app.quit()

    worker.error.connect(on_error)
    worker.ready_to_launch.connect(on_ready)
    worker.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
