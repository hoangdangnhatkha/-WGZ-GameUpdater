"""Modal progress dialog for service auto-login workers (Riot / Steam / ...).

Shows elapsed time, a scrolling log of status messages, and a cancel button.
Blocks all interaction with the main window while the worker is running.

The dialog is service-agnostic: any QThread worker that exposes the four
signals `status(str)`, `finished_ok()`, `failed(str)`, and `cancelled()` plus
`requestInterruption()` (i.e., the QThread protocol) works.
"""

from __future__ import annotations

import time

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)


class LoginProgressDialog(QDialog):
    """Modal progress dialog for an active auto-login worker.

    Owns the worker's lifecycle from start to terminal signal (finished_ok /
    failed / cancelled). Closes itself automatically when any terminal signal
    fires. Cancel button requests worker interruption.
    """

    cancel_requested = pyqtSignal()

    def __init__(
        self,
        worker: QThread,
        service_name: str = "AUTO-LOGIN",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._worker = worker
        self._terminal = False
        self._start_ts = time.monotonic()
        self._service_name = service_name.upper()

        self.setObjectName("RiotLoginDialog")  # reuse Riot QSS styling
        self.setWindowTitle(f"{service_name.title()} Auto-Login")
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setFixedWidth(560)
        self.setMinimumHeight(360)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame(self)
        header.setObjectName("RiotLoginHeader")
        hlay = QVBoxLayout(header)
        hlay.setContentsMargins(22, 18, 22, 16)
        hlay.setSpacing(2)
        title = QLabel(f"// {self._service_name} AUTO-LOGIN", header)
        title.setObjectName("RiotLoginTitle")
        hlay.addWidget(title)
        sub = QLabel(
            "> KHÔNG TƯƠNG TÁC VỚI MÁY TRONG QUÁ TRÌNH ĐĂNG NHẬP",
            header,
        )
        sub.setObjectName("RiotLoginSub")
        hlay.addWidget(sub)
        root.addWidget(header)

        # Timer row
        timer_frame = QFrame(self)
        timer_frame.setObjectName("RiotLoginTimerFrame")
        tlay = QHBoxLayout(timer_frame)
        tlay.setContentsMargins(22, 14, 22, 14)
        tlay.setSpacing(14)
        clock_label = QLabel("⏱  ELAPSED", timer_frame)
        clock_label.setObjectName("RiotLoginClockLabel")
        tlay.addWidget(clock_label)
        self._clock = QLabel("00:00", timer_frame)
        self._clock.setObjectName("RiotLoginClock")
        tlay.addWidget(self._clock)
        tlay.addStretch(1)
        self._state_chip = QLabel("WORKING", timer_frame)
        self._state_chip.setObjectName("RiotLoginStateChip")
        tlay.addWidget(self._state_chip)
        root.addWidget(timer_frame)

        # Log
        log_wrap = QFrame(self)
        log_wrap.setObjectName("RiotLoginLogWrap")
        llay = QVBoxLayout(log_wrap)
        llay.setContentsMargins(22, 12, 22, 12)
        llay.setSpacing(6)
        log_caption = QLabel("// LOG", log_wrap)
        log_caption.setObjectName("RiotLoginLogCaption")
        llay.addWidget(log_caption)
        self._log = QPlainTextEdit(log_wrap)
        self._log.setObjectName("RiotLoginLog")
        self._log.setReadOnly(True)
        self._log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        llay.addWidget(self._log, 1)
        root.addWidget(log_wrap, 1)

        # Footer
        footer = QFrame(self)
        footer.setObjectName("RiotLoginFooter")
        flay = QHBoxLayout(footer)
        flay.setContentsMargins(22, 14, 22, 18)
        flay.setSpacing(10)
        flay.addStretch(1)
        self._cancel_btn = QPushButton("HỦY", footer)
        self._cancel_btn.setObjectName("RiotLoginCancelBtn")
        self._cancel_btn.setFixedHeight(32)
        self._cancel_btn.setMinimumWidth(110)
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)
        flay.addWidget(self._cancel_btn)
        root.addWidget(footer)

        # Wire worker signals (duck-typed — any worker exposing these signals)
        worker.status.connect(self._on_status)
        worker.finished_ok.connect(self._on_finished_ok)
        worker.failed.connect(self._on_failed)
        worker.cancelled.connect(self._on_cancelled)

        # Tick the elapsed clock
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(250)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start()

        self._append_log(f"// {self._service_name} AUTO-LOGIN STARTED")

    # ── Logging helpers ─────────────────────────────────────────────

    def _append_log(self, message: str) -> None:
        stamp = self._elapsed_text()
        self._log.appendPlainText(f"[{stamp}] {message}")
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _elapsed_text(self) -> str:
        elapsed = int(time.monotonic() - self._start_ts)
        return f"{elapsed // 60:02d}:{elapsed % 60:02d}"

    def _tick(self) -> None:
        self._clock.setText(self._elapsed_text())

    # ── Worker signal handlers ──────────────────────────────────────

    def _on_status(self, msg: str) -> None:
        self._append_log(f"> {msg}")

    def _on_finished_ok(self) -> None:
        self._terminal = True
        self._append_log("// SUCCESS — credentials submitted")
        self._state_chip.setText("SUCCESS")
        self._state_chip.setProperty("state", "ok")
        self._restyle(self._state_chip)
        self._tick_timer.stop()
        self._cancel_btn.setText("ĐÓNG")
        self._cancel_btn.setEnabled(True)
        try:
            self._cancel_btn.clicked.disconnect()
        except Exception:
            pass
        self._cancel_btn.clicked.connect(self.accept)
        QTimer.singleShot(800, self.accept)

    def _on_failed(self, msg: str) -> None:
        self._terminal = True
        self._append_log(f"// ERROR — {msg}")
        self._state_chip.setText("ERROR")
        self._state_chip.setProperty("state", "err")
        self._restyle(self._state_chip)
        self._tick_timer.stop()
        self._cancel_btn.setText("ĐÓNG")
        self._cancel_btn.setEnabled(True)
        try:
            self._cancel_btn.clicked.disconnect()
        except Exception:
            pass
        self._cancel_btn.clicked.connect(self.reject)

    def _on_cancelled(self) -> None:
        self._terminal = True
        self._append_log("// CANCELLED")
        self._state_chip.setText("CANCELLED")
        self._state_chip.setProperty("state", "err")
        self._restyle(self._state_chip)
        self._tick_timer.stop()
        self._cancel_btn.setText("ĐÓNG")
        self._cancel_btn.setEnabled(True)
        try:
            self._cancel_btn.clicked.disconnect()
        except Exception:
            pass
        self._cancel_btn.clicked.connect(self.reject)
        QTimer.singleShot(600, self.reject)

    # ── Cancel handling ─────────────────────────────────────────────

    def _on_cancel_clicked(self) -> None:
        if self._terminal:
            self.reject()
            return
        self._append_log("// REQUESTING CANCEL...")
        self._cancel_btn.setEnabled(False)
        self._state_chip.setText("CANCELLING")
        self._state_chip.setProperty("state", "err")
        self._restyle(self._state_chip)
        self.cancel_requested.emit()
        self._worker.requestInterruption()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Block Esc from closing prematurely; only the Cancel button or
        # terminal completion can dismiss this dialog.
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        # Block window-close (X) until worker has reached a terminal state.
        if not self._terminal:
            event.ignore()
            return
        super().closeEvent(event)

    # ── Util ────────────────────────────────────────────────────────

    def _restyle(self, w: QWidget) -> None:
        w.style().unpolish(w)
        w.style().polish(w)
