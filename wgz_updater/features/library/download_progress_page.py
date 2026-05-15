from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit,
    QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from ...core.config import Game
from ...core.win32_utils import prevent_sleep
from ...resources.strings_vi import ACTION_BACK, DOWNLOAD_DONE
from .download_worker import DownloadWorker
from .extract_worker import ExtractWorker
from .image_loader import ImageLoader
from .models import InstallRegistry

log = logging.getLogger(__name__)


class DownloadProgressPage(QWidget):
    """Cinematic operation-briefing download + extraction progress page."""

    finished = pyqtSignal(object, str)     # Game, install_path (on success)
    cancelled = pyqtSignal()               # user cancelled or back after error

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
        self._archive_paths: list[str] = []
        self._download_worker: DownloadWorker | None = None
        self._extract_worker: ExtractWorker | None = None
        self._sleep_ctx = None
        self._pixmap: QPixmap | None = None
        self._start_time: float = 0.0
        self.setObjectName("OpsPage")

        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._tick_elapsed)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(44, 30, 36, 30)
        outer.setSpacing(36)

        # ── LEFT COLUMN ───────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(0)
        left.setContentsMargins(0, 0, 0, 0)

        # Top strip: back btn (hidden by default) + op ID
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(0)
        self._back_btn = QPushButton("◄  QUAY LẠI", self)
        self._back_btn.setObjectName("BackButton")
        self._back_btn.setVisible(False)
        self._back_btn.clicked.connect(self.cancelled)
        hdr_row.addWidget(self._back_btn)
        hdr_row.addStretch(1)
        op_id = QLabel("// DEPLOY · ACTIVE", self)
        op_id.setObjectName("OpsOpId")
        hdr_row.addWidget(op_id)
        left.addLayout(hdr_row)

        left.addSpacing(20)

        # Banner
        banner = QLabel("◢  ACTIVE DEPLOYMENT", self)
        banner.setObjectName("OpsBanner")
        left.addWidget(banner)

        left.addSpacing(8)
        rule1 = self._make_hrule()
        left.addWidget(rule1)
        left.addSpacing(22)

        # Game title
        self._name_lbl = QLabel("", self)
        self._name_lbl.setObjectName("OpsGameTitle")
        self._name_lbl.setWordWrap(True)
        left.addWidget(self._name_lbl)

        left.addSpacing(8)

        # Phase label
        self._phase_lbl = QLabel("PHASE 01/02  ·  INITIALIZING", self)
        self._phase_lbl.setObjectName("OpsPhaseLabel")
        left.addWidget(self._phase_lbl)

        left.addSpacing(32)

        # ── Progress box ──────────────────────────────────────────
        prog_box = QFrame(self)
        prog_box.setObjectName("OpsProgressBox")
        prog_inner = QVBoxLayout(prog_box)
        prog_inner.setContentsMargins(22, 18, 22, 18)
        prog_inner.setSpacing(12)

        prog_hdr = QLabel("▌  TRANSFER STATUS", self)
        prog_hdr.setObjectName("OpsProgressHeader")
        prog_inner.addWidget(prog_hdr)

        self._bar = QProgressBar(self)
        self._bar.setObjectName("OpsBar")
        self._bar.setRange(0, 100)
        self._bar.setFixedHeight(20)
        self._bar.setTextVisible(False)
        prog_inner.addWidget(self._bar)

        # Metrics row
        metrics = QHBoxLayout()
        metrics.setSpacing(0)
        self._speed_val = self._metric_col("SPEED", "—", metrics)
        self._vsep(metrics)
        self._elapsed_val = self._metric_col("ELAPSED", "00:00", metrics)
        self._vsep(metrics)
        self._pct_val = self._metric_col("COMPLETED", "0%", metrics)
        metrics.addStretch(1)
        prog_inner.addLayout(metrics)

        left.addWidget(prog_box)
        left.addSpacing(14)

        # Status text
        self._status_lbl = QLabel("Đang khởi động...", self)
        self._status_lbl.setObjectName("OpsStatusText")
        left.addWidget(self._status_lbl)

        left.addStretch(1)

        # Action row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self._cancel_btn = QPushButton("◼  ABORT OPERATION", self)
        self._cancel_btn.setObjectName("AbortButton")
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)
        btn_row.addStretch(1)
        left.addLayout(btn_row)

        outer.addLayout(left, 6)

        # ── RIGHT COLUMN — terminal log ───────────────────────────
        right = QVBoxLayout()
        right.setSpacing(0)
        right.setContentsMargins(0, 0, 0, 0)

        log_hdr = QLabel("// OPERATION LOG", self)
        log_hdr.setObjectName("OpsLogHeader")
        right.addWidget(log_hdr)

        right.addSpacing(8)
        rule2 = self._make_hrule()
        right.addWidget(rule2)
        right.addSpacing(12)

        self._log_view = QPlainTextEdit(self)
        self._log_view.setObjectName("OpsLog")
        self._log_view.setReadOnly(True)
        self._log_view.setPlaceholderText("// awaiting operation...")
        right.addWidget(self._log_view, 1)

        outer.addLayout(right, 4)

    # ── helpers ───────────────────────────────────────────────────

    def _make_hrule(self) -> QFrame:
        r = QFrame(self)
        r.setFrameShape(QFrame.Shape.HLine)
        r.setObjectName("OpsRule")
        r.setFixedHeight(1)
        return r

    def _metric_col(self, label: str, value: str, layout: QHBoxLayout) -> QLabel:
        col = QVBoxLayout()
        col.setSpacing(3)
        col.setContentsMargins(0, 8, 32, 8)
        h = QLabel(label, self)
        h.setObjectName("OpsMetricLabel")
        col.addWidget(h)
        v = QLabel(value, self)
        v.setObjectName("OpsMetricValue")
        col.addWidget(v)
        layout.addLayout(col)
        return v

    def _vsep(self, layout: QHBoxLayout) -> None:
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setObjectName("OpsMetricSep")
        sep.setFixedWidth(1)
        layout.addWidget(sep)
        layout.addSpacing(20)

    # ── paint ─────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = self.rect()

        painter.fillRect(rect, QColor("#07070a"))

        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaledToHeight(
                rect.height(),
                Qt.TransformationMode.SmoothTransformation,
            )
            img_rect = scaled.rect()
            img_rect.moveRight(rect.right())
            img_rect.moveTop(0)
            painter.setOpacity(0.14)
            painter.drawPixmap(img_rect, scaled)
            painter.setOpacity(1.0)

            # Gradient fade left → transparent right
            grad = QLinearGradient(0, 0, rect.width(), 0)
            grad.setColorAt(0.0,  QColor(7, 7, 10, 255))
            grad.setColorAt(0.4,  QColor(7, 7, 10, 240))
            grad.setColorAt(0.65, QColor(7, 7, 10, 180))
            grad.setColorAt(1.0,  QColor(7, 7, 10, 80))
            painter.fillRect(rect, grad)

        # Scan-line texture
        pen = QPen(QColor(7, 7, 10, 30))
        pen.setWidth(1)
        painter.setPen(pen)
        for y in range(0, rect.height(), 3):
            painter.drawLine(0, y, rect.width(), y)

        # Lime top accent bar
        painter.fillRect(0, 0, rect.width(), 2, QColor("#d8ff3a"))

        # Corner bracket (top-right)
        painter.setPen(QPen(QColor("#d8ff3a"), 1))
        r = rect
        painter.drawLine(r.right() - 30, r.top() + 1, r.right() - 1, r.top() + 1)
        painter.drawLine(r.right() - 1, r.top() + 1, r.right() - 1, r.top() + 30)

        # Corner bracket (bottom-left)
        painter.drawLine(r.left() + 1, r.bottom() - 30, r.left() + 1, r.bottom() - 1)
        painter.drawLine(r.left() + 1, r.bottom() - 1, r.left() + 30, r.bottom() - 1)

        painter.end()

    # ── public ───────────────────────────────────────────────────

    def start(
        self,
        game: Game,
        install_path: str,
        url_idx: int,
        image_url: str = "",
    ) -> None:
        self._game = game
        self._install_path = Path(install_path)
        self._archive_paths = []
        self._cancel_btn.setVisible(True)
        self._back_btn.setVisible(False)
        self._log_view.clear()
        self._start_time = time.monotonic()
        self._elapsed_timer.start()
        self._pixmap = None
        self.update()

        if image_url:
            ImageLoader.instance().request(image_url, self._set_image)

        if game.urls:
            self._url_list = game.urls
        elif game.url:
            self._url_list = [game.url]
        else:
            self._url_list = []

        if len(self._url_list) > 1:
            self._url_idx = 0
        else:
            self._url_idx = url_idx

        self._name_lbl.setText((game.game or game.name or "").upper())
        self._bar.setValue(0)
        self._pct_val.setText("0%")
        self._speed_val.setText("—")

        try:
            self._sleep_ctx = prevent_sleep()
            self._sleep_ctx.__enter__()
        except Exception:
            self._sleep_ctx = None

        self._log_entry("Khởi động tiến trình...")
        self._start_next_download()

    # ── internals ────────────────────────────────────────────────

    def _set_image(self, pixmap: QPixmap) -> None:
        try:
            self._pixmap = pixmap
            self.update()
        except RuntimeError:
            pass

    def _log_entry(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_view.appendPlainText(f"[{ts}]  {msg}")

    def _tick_elapsed(self) -> None:
        elapsed = int(time.monotonic() - self._start_time)
        m, s = divmod(elapsed, 60)
        self._elapsed_val.setText(f"{m:02d}:{s:02d}")

    def _set_phase(self, text: str) -> None:
        self._phase_lbl.setText(text)

    def _set_status(self, msg: str) -> None:
        self._status_lbl.setText(msg)

    def _start_next_download(self) -> None:
        if self._url_idx >= len(self._url_list):
            self._start_extraction()
            return

        url = self._url_list[self._url_idx]
        total = len(self._url_list)
        if total > 1:
            self._set_phase(
                f"PHASE  01/02  ·  PHẦN  {self._url_idx + 1:02d} / {total:02d}  ·  DOWNLOADING"
            )
        else:
            self._set_phase("PHASE  01/02  ·  DOWNLOADING")

        self._bar.setValue(0)
        self._pct_val.setText("0%")
        self._speed_val.setText("—")
        self._set_status("Đang chuẩn bị tải về...")
        self._log_entry(f"Bắt đầu tải phần {self._url_idx + 1}/{total}...")

        w = DownloadWorker(url, self._install_path, parent=self)
        self._download_worker = w
        w.progress.connect(self._on_progress)
        w.progress.connect(self.worker_progress)
        w.speed.connect(self._on_speed)
        w.status.connect(self._on_dl_status)
        w.status.connect(self.worker_message)
        w.finished_ok.connect(self._on_part_done)
        w.failed.connect(self._on_download_failed)
        self.worker_started.emit(w)
        w.start()

    def _on_progress(self, pct: int) -> None:
        self._bar.setValue(pct)
        self._pct_val.setText(f"{pct}%")

    def _on_speed(self, speed_str: str) -> None:
        self._speed_val.setText(speed_str)

    def _on_dl_status(self, msg: str) -> None:
        self._set_status(msg)
        self._log_entry(msg)

    def _on_part_done(self, archive_path: str) -> None:
        self._archive_paths.append(archive_path)
        self._log_entry(f"✓  {Path(archive_path).name}")
        self._url_idx += 1
        self._start_next_download()

    def _start_extraction(self) -> None:
        if not self._archive_paths or not self._game or not self._install_path:
            return
        self._set_phase("PHASE  02/02  ·  EXTRACTING")
        self._set_status("Đang giải nén...")
        self._log_entry("Bắt đầu giải nén...")
        self._bar.setValue(0)
        self._pct_val.setText("0%")

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
        w.progress.connect(self._on_progress)
        w.progress.connect(self.worker_progress)
        w.status.connect(self._on_extract_status)
        w.status.connect(self.worker_message)
        w.finished_ok.connect(self._on_extract_done)
        w.failed.connect(self._on_extract_failed)
        self.worker_started.emit(w)
        w.start()

    def _on_extract_status(self, msg: str) -> None:
        self._set_status(msg)
        self._log_entry(msg)

    def _on_extract_done(self, target_dir: str) -> None:
        self._set_phase("OPERATION COMPLETE  ·  SUCCESS")
        self._set_status(DOWNLOAD_DONE)
        self._bar.setValue(100)
        self._pct_val.setText("100%")
        self._cancel_btn.setVisible(False)
        self._elapsed_timer.stop()
        self._log_entry("✓  Hoàn thành! Triển khai thành công.")
        self.worker_finished.emit()
        self._release_sleep()

        if self._game and self._install_path:
            self._registry.record_install(
                self._game.id, self._install_path, self._game.version
            )
        if self._game and self._install_path:
            self.finished.emit(self._game, str(self._install_path))

    def _on_download_failed(self, error: str) -> None:
        self._set_phase("OPERATION FAILED  ·  DOWNLOAD ERROR")
        self._set_status(f"Lỗi tải về: {error}")
        self._log_entry(f"✗  Lỗi: {error}")
        self._cancel_btn.setVisible(False)
        self._back_btn.setVisible(True)
        self._elapsed_timer.stop()
        self.worker_finished.emit()
        self._release_sleep()

    def _on_extract_failed(self, error: str) -> None:
        self._set_phase("OPERATION FAILED  ·  EXTRACT ERROR")
        self._set_status(f"Lỗi giải nén: {error}")
        self._log_entry(f"✗  Lỗi giải nén: {error}")
        self._cancel_btn.setVisible(False)
        self._back_btn.setVisible(True)
        self._elapsed_timer.stop()
        self.worker_finished.emit()
        self._release_sleep()

    def _on_cancel(self) -> None:
        if self._download_worker and self._download_worker.isRunning():
            self._download_worker.cancel()
        if self._extract_worker and self._extract_worker.isRunning():
            self._extract_worker.requestInterruption()
        self._elapsed_timer.stop()
        self._release_sleep()
        self.cancelled.emit()

    def _release_sleep(self) -> None:
        if self._sleep_ctx:
            try:
                self._sleep_ctx.__exit__(None, None, None)
            except Exception:
                pass
            self._sleep_ctx = None
