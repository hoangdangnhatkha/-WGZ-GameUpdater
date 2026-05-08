from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout


class ProgressCard(QFrame):
    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        self._title = QLabel(title, self)
        self._title.setStyleSheet("font-weight: 600;")
        self._detail = QLabel("", self)
        self._detail.setStyleSheet("color: #b8b8b8; font-size: 12px;")
        self._bar = QProgressBar(self)
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        layout.addWidget(self._title)
        layout.addWidget(self._bar)
        layout.addWidget(self._detail)

    def set_title(self, text: str) -> None:
        self._title.setText(text)

    def set_detail(self, text: str) -> None:
        self._detail.setText(text)

    def set_progress(self, value: int) -> None:
        self._bar.setValue(value)
