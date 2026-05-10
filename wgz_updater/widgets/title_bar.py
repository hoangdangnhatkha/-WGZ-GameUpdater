from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QMouseEvent, QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ..core.paths import icon as icon_path
from ..resources.strings_vi import APP_TITLE


class TitleBar(QWidget):
    minimize_requested = pyqtSignal()
    maximize_toggled = pyqtSignal()
    close_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(0)

        self._icon = QLabel(self)
        logo = icon_path("logo.png")
        if logo.exists():
            pix = QPixmap(str(logo)).scaled(
                18, 18,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._icon.setPixmap(pix)
        self._icon.setFixedWidth(28)
        layout.addWidget(self._icon)

        self._title = QLabel(APP_TITLE.upper(), self)
        self._title.setObjectName("TitleBarLabel")
        layout.addWidget(self._title)

        self._subtitle = QLabel("// SYSTEM ONLINE", self)
        self._subtitle.setObjectName("TitleBarSubtitle")
        layout.addWidget(self._subtitle)

        layout.addStretch(1)

        self._btn_min = self._make_button("–", on_click=self.minimize_requested.emit)
        self._btn_max = self._make_button("☐", on_click=self.maximize_toggled.emit)
        self._btn_close = self._make_button("✕", on_click=self.close_requested.emit, close=True)
        for b in (self._btn_min, self._btn_max, self._btn_close):
            layout.addWidget(b)

        self._drag_active = False

    def _make_button(self, label: str, on_click, close: bool = False) -> QPushButton:
        b = QPushButton(label, self)
        b.setObjectName("TitleBarClose" if close else "TitleBarButton")
        b.setFlat(True)
        b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        b.setFixedSize(QSize(46, 32))
        b.clicked.connect(on_click)
        return b

    def set_title(self, text: str) -> None:
        self._title.setText(text)

    def set_maximized(self, maximized: bool) -> None:
        self._btn_max.setText("❐" if maximized else "☐")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                self._drag_active = True
                handle.startSystemMove()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximize_toggled.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
