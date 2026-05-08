from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class DropZone(QFrame):
    folder_dropped = pyqtSignal(str)

    def __init__(self, label: str = "Kéo thả thư mục vào đây", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)
        layout = QVBoxLayout(self)
        self._label = QLabel(label, self)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if Path(url.toLocalFile()).is_dir():
                    self.setObjectName("DropZoneActive")
                    self.style().unpolish(self)
                    self.style().polish(self)
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setObjectName("DropZone")
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local and Path(local).is_dir():
                self.folder_dropped.emit(local)
                break
        self.setObjectName("DropZone")
        self.style().unpolish(self)
        self.style().polish(self)
        event.acceptProposedAction()
