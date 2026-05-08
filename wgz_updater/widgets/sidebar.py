from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class NavItem:
    key: str
    label: str
    icon_glyph: str = ""


class Sidebar(QFrame):
    nav_changed = pyqtSignal(str)

    def __init__(self, items: list[NavItem], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(2)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}

        for item in items:
            btn = QPushButton(f"  {item.icon_glyph}  {item.label}".rstrip(), self)
            btn.setObjectName("NavItem")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            btn.clicked.connect(lambda _checked, k=item.key: self._on_clicked(k))
            self._group.addButton(btn)
            self._buttons[item.key] = btn
            layout.addWidget(btn)

        layout.addStretch(1)

        if items:
            first = items[0].key
            self._buttons[first].setChecked(True)

    def _on_clicked(self, key: str) -> None:
        self.nav_changed.emit(key)

    def select(self, key: str) -> None:
        btn = self._buttons.get(key)
        if btn:
            btn.setChecked(True)
            self.nav_changed.emit(key)
