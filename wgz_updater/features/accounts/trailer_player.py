from __future__ import annotations

import logging

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

log = logging.getLogger(__name__)


class TrailerPlayer(QWidget):
    """In-process trailer player using QWebEngineView (replaces pywebview + multiprocessing)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._view: QWidget | None = None
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            self._view = QWebEngineView(self)
            layout.addWidget(self._view)
        except ImportError:
            log.warning("PyQt6-WebEngine not installed; trailer player disabled")

    def play(self, url: str) -> None:
        if self._view is None or not url:
            return
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
            self._view.setUrl(QUrl(url))
        except Exception:
            log.exception("Failed to load trailer URL")

    def stop(self) -> None:
        if self._view is None:
            return
        try:
            self._view.setUrl(QUrl("about:blank"))
        except Exception:
            pass
