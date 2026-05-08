from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from ...core.config import Game
from ...core.win32_utils import prevent_sleep
from ...resources.strings_vi import ACTION_BACK, ACTION_CANCEL, DOWNLOAD_DONE
from .download_worker import DownloadWorker
from .extract_worker import ExtractWorker
from .models import InstallRegistry

log = logging.getLogger(__name__)


class DownloadProgressPage(QWidget):
    """Full-screen download + extraction progress page."""

    finished = pyqtSignal(object, str)    # Game, install_path (on success)
    cancelled = pyqtSignal()              # user cancelled or back after error

    # Forwarded to StatusStrip
    worker_started = pyqtSignal(object)
    worker_message = pyqtSignal(str)
    worker_progress = pyqtSignal(int)
    worker_finished = pyqtSignal()

    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._game: Game | None = None
        self._install_path: Path | None = None
        self._url_list: list[str] = []
        self._url_idx = 0
        self._archive_paths: list[str] = []   # collected archive paths per part
        self._download_worker: DownloadWorker | None = None
        self._extract_worker: ExtractWorker | None = None
        self._sleep_ctx = None
        self.setObjectName("ProgressPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(16)
        layout.addStretch(2)

        # Game name
        self._name_lbl = QLabel(self)
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_lbl.setStyleSheet("font-size:20px;font-weight:600;")
        layout.addWidget(self._name_lbl)

        # Part indicator (hidden for single URL)
        self._part_lbl = QLabel(self)
        self._part_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._part_lbl.setStyleSheet("font-size:13px;color:#888;")
        layout.addWidget(self._part_lbl)

        # Progress bar
        self._bar = QProgressBar(self)
        self._bar.setRange(0, 100)
        layout.addWidget(self._bar)

        # Speed + ETA row
        speed_row = QHBoxLayout()
        self._speed_lbl = QLabel("", self)
        speed_row.addWidget(self._speed_lbl)
        speed_row.addStretch(1)
        self._eta_lbl = QLabel("", self)
        speed_row.addWidget(self._eta_lbl)
        layout.addLayout(speed_row)

        # Status text
        self._status_lbl = QLabel("", self)
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_lbl)

        layout.addStretch(2)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self._cancel_btn = QPushButton(ACTION_CANCEL, self)
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)
        self._back_btn = QPushButton(ACTION_BACK, self)
        self._back_btn.setVisible(False)
        self._back_btn.clicked.connect(self.cancelled)
        btn_row.addWidget(self._back_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

    def start(self, game: Game, install_path: str, url_idx: int) -> None:
        """Begin download for game. url_idx selects which URL to download."""
        self._game = game
        self._install_path = Path(install_path)
        self._archive_paths = []
        self._cancel_btn.setVisible(True)
        self._back_btn.setVisible(False)

        # Build url list: single url or all urls (multi-part)
        if game.urls:
            self._url_list = game.urls
        elif game.url:
            self._url_list = [game.url]
        else:
            self._url_list = []

        # For single-url games, start at url_idx; for multi-part always download all
        if len(self._url_list) > 1:
            self._url_idx = 0   # always start from part 1 for multi-part
        else:
            self._url_idx = url_idx

        self._name_lbl.setText(game.name)
        self._part_lbl.setVisible(len(self._url_list) > 1)

        # Block sleep
        try:
            self._sleep_ctx = prevent_sleep()
            self._sleep_ctx.__enter__()
        except Exception:
            self._sleep_ctx = None

        self._start_next_download()

    def _start_next_download(self) -> None:
        if self._url_idx >= len(self._url_list):
            self._start_extraction()
            return

        url = self._url_list[self._url_idx]
        total = len(self._url_list)
        if total > 1:
            self._part_lbl.setText(f"Phần {self._url_idx + 1}/{total}")
        self._bar.setValue(0)
        self._speed_lbl.setText("")
        self._eta_lbl.setText("")
        self._status_lbl.setText("Đang chuẩn bị tải về...")

        tmp_dir = Path(tempfile.gettempdir()) / "wgz_downloads"
        hint = f"part{self._url_idx + 1}.bin"
        w = DownloadWorker(url, tmp_dir, file_hint=hint, parent=self)
        self._download_worker = w
        w.progress.connect(self._bar.setValue)
        w.progress.connect(self.worker_progress)
        w.speed.connect(self._speed_lbl.setText)
        w.status.connect(self._status_lbl.setText)
        w.status.connect(self.worker_message)
        w.finished_ok.connect(self._on_part_done)
        w.failed.connect(self._on_download_failed)
        self.worker_started.emit(w)
        w.start()

    def _on_part_done(self, archive_path: str) -> None:
        self._archive_paths.append(archive_path)
        self._url_idx += 1
        self._start_next_download()

    def _start_extraction(self) -> None:
        if not self._archive_paths or not self._game or not self._install_path:
            return
        self._status_lbl.setText("Đang giải nén...")
        self._bar.setValue(0)

        # Use the first archive (for multi-part, only extract the first;
        # for single-part, extract the only one)
        archive = Path(self._archive_paths[0])
        w = ExtractWorker(
            archive_path=archive,
            target_dir=self._install_path,
            archive_type=self._game.type,
            password=self._game.password,
            delete_before=self._game.delete_before_extract or [],
            parent=self,
        )
        self._extract_worker = w
        w.progress.connect(self._bar.setValue)
        w.progress.connect(self.worker_progress)
        w.status.connect(self._status_lbl.setText)
        w.status.connect(self.worker_message)
        w.finished_ok.connect(self._on_extract_done)
        w.failed.connect(self._on_extract_failed)
        self.worker_started.emit(w)
        w.start()

    def _on_extract_done(self, target_dir: str) -> None:
        self._status_lbl.setText(DOWNLOAD_DONE)
        self._bar.setValue(100)
        self._cancel_btn.setVisible(False)
        self.worker_finished.emit()
        self._release_sleep()

        # Record install in registry
        if self._game and self._install_path:
            self._registry.record_install(
                self._game.id, self._install_path, self._game.version
            )

        if self._game and self._install_path:
            self.finished.emit(self._game, str(self._install_path))

    def _on_download_failed(self, error: str) -> None:
        self._status_lbl.setText(f"Lỗi tải về: {error}")
        self._cancel_btn.setVisible(False)
        self._back_btn.setVisible(True)
        self.worker_finished.emit()
        self._release_sleep()

    def _on_extract_failed(self, error: str) -> None:
        self._status_lbl.setText(f"Lỗi giải nén: {error}")
        self._cancel_btn.setVisible(False)
        self._back_btn.setVisible(True)
        self.worker_finished.emit()
        self._release_sleep()

    def _on_cancel(self) -> None:
        if self._download_worker and self._download_worker.isRunning():
            self._download_worker.cancel()
        if self._extract_worker and self._extract_worker.isRunning():
            self._extract_worker.requestInterruption()
        self._release_sleep()
        self.cancelled.emit()

    def _release_sleep(self) -> None:
        if self._sleep_ctx:
            try:
                self._sleep_ctx.__exit__(None, None, None)
            except Exception:
                pass
            self._sleep_ctx = None
