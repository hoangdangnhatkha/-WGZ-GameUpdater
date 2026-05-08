from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class StatusStrip(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusStrip")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(16)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(2)
        self._title = QLabel("Sẵn sàng", self)
        self._title.setObjectName("StatusStripTitle")
        self._detail = QLabel("", self)
        self._detail.setObjectName("StatusStripDetail")
        text_box.addWidget(self._title)
        text_box.addWidget(self._detail)
        layout.addLayout(text_box, 1)

        self._progress = QProgressBar(self)
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedWidth(280)
        layout.addWidget(self._progress)

        if parent is not None and hasattr(parent, "stack"):
            parent_lib = getattr(parent, "_views", {}).get("library") if hasattr(parent, "_views") else None
            if parent_lib is not None:
                self._wire_to_view(parent_lib)

    def _wire_to_view(self, view) -> None:
        if hasattr(view, "worker_started"):
            view.worker_started.connect(lambda _w: self._on_started())
        if hasattr(view, "worker_message"):
            view.worker_message.connect(self._on_message)
        if hasattr(view, "worker_progress"):
            view.worker_progress.connect(self._progress.setValue)
        if hasattr(view, "worker_finished"):
            view.worker_finished.connect(self._on_finished)

    def _on_started(self) -> None:
        self._progress.setValue(0)

    def _on_message(self, msg: str) -> None:
        if msg:
            if any(ch.isdigit() for ch in msg) and ("/s" in msg or "%" in msg):
                self._detail.setText(msg)
            else:
                self._title.setText(msg)

    def _on_finished(self) -> None:
        self._title.setText("Hoàn tất")
        self._detail.setText("")
        self._progress.setValue(100)
