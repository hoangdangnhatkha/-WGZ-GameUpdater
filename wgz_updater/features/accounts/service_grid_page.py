from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from ...resources.strings_vi import LABEL_ACCOUNTS_COUNT, NAV_ACCOUNTS

_MAX_COLS = 5


class ServiceCard(QFrame):
    clicked = pyqtSignal(str)  # service name

    def __init__(self, service_name: str, count: int, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ServiceCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(4)

        icon_lbl = QLabel(self)
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setText(service_name[0].upper())
        icon_lbl.setStyleSheet(
            "background:#0078d4;border-radius:20px;color:#fff;font-size:18px;font-weight:700;"
        )
        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        name_lbl = QLabel(service_name, self)
        name_lbl.setObjectName("ServiceCardName")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        count_lbl = QLabel(LABEL_ACCOUNTS_COUNT.format(count=count), self)
        count_lbl.setObjectName("ServiceCardCount")
        count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(count_lbl)

        self._service = service_name

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._service)
        super().mousePressEvent(event)


class ServiceGridPage(QWidget):
    service_selected = pyqtSignal(str)  # service name

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(10)

        title = QLabel(NAV_ACCOUNTS, self)
        title.setStyleSheet("font-size:22px;font-weight:600;")
        outer.addWidget(title)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(10)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._grid_widget)
        outer.addWidget(scroll, 1)

    def populate(self, accounts_data: dict) -> None:
        """accounts_data: {service_name: [AccountRecord, ...]}"""
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        services = sorted(accounts_data.keys())
        priority = ["Steam", "Riot"]
        ordered = [s for s in priority if s in services] + [
            s for s in services if s not in priority
        ]
        for s in priority:
            if s not in ordered:
                ordered.insert(priority.index(s), s)
        ordered = list(dict.fromkeys(ordered))  # deduplicate preserving order

        for i, service_name in enumerate(ordered):
            count = len(accounts_data.get(service_name, []))
            card = ServiceCard(service_name, count, self._grid_widget)
            card.clicked.connect(self.service_selected)
            self._grid.addWidget(card, i // _MAX_COLS, i % _MAX_COLS)
