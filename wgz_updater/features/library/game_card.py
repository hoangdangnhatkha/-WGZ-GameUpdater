from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from ...core.config import Game
from ...resources.strings_vi import ACTION_DOWNLOAD, ACTION_UPDATE, STATUS_INSTALLED
from .image_loader import ImageLoader
from .models import InstallRegistry, InstallStatus

_TAG_COLORS: dict[str, tuple[str, str]] = {
    "HOT":  ("#ff4d4d", "#ffffff"),
    "GOTY": ("#ffd700", "#000000"),
    "NEW":  ("#4cff00", "#000000"),
    "UPD":  ("#4a90e2", "#ffffff"),
    "BEST": ("#9b59b6", "#ffffff"),
    "FIX":  ("#e67e22", "#ffffff"),
}


class GameCard(QFrame):
    clicked = pyqtSignal(object)  # emits list[Game] (variants of same game)

    def __init__(
        self,
        entries: list[Game],
        registry: InstallRegistry,
        display_name: str = "",
        image_url: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        if not entries:
            raise ValueError("GameCard requires at least one Game entry")
        self._entries = entries
        self._game = entries[0]
        self._display_name = display_name or self._game.game or self._game.name
        self._registry = registry
        self.setObjectName("GameCard")
        self.setFixedWidth(210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Image
        self._img_label = QLabel(self)
        self._img_label.setFixedSize(194, 90)
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setObjectName("HeroImage")
        layout.addWidget(self._img_label)

        # Tag badge — use first entry that has a tag
        tag = ""
        for e in entries:
            if (e.tag or "").upper() in _TAG_COLORS:
                tag = e.tag.upper()
                break
        if tag:
            bg, fg = _TAG_COLORS[tag]
            self._tag = QLabel(f"[ {tag} ]", self)
            self._tag.setStyleSheet(
                f"background:transparent;color:{bg};"
                f"font-family:'Cascadia Mono', Consolas, monospace;"
                f"font-size:10px;font-weight:700;letter-spacing:1.2px;"
                f"padding:0;"
            )
            layout.addWidget(self._tag)

        # Name + variant count
        name_lbl = QLabel(self._display_name, self)
        name_lbl.setObjectName("GameCardName")
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        if len(entries) > 1:
            count_lbl = QLabel(f"{len(entries):02d} BẢN", self)
            count_lbl.setObjectName("GameCardMeta")
            layout.addWidget(count_lbl)

        # Action button
        self._btn = QPushButton(self)
        self._btn.clicked.connect(lambda: self.clicked.emit(self._entries))
        layout.addWidget(self._btn)

        self._refresh_button()

        if image_url:
            ImageLoader.instance().request(image_url, self._set_image)

    def _refresh_button(self) -> None:
        # Aggregate status: INSTALLED if any installed, else UPDATE if any needs update, else NOT_INSTALLED
        statuses = [self._registry.status_for(g) for g in self._entries]
        if any(s == InstallStatus.INSTALLED for s in statuses):
            status = InstallStatus.INSTALLED
        elif any(s == InstallStatus.UPDATE for s in statuses):
            status = InstallStatus.UPDATE
        else:
            status = InstallStatus.NOT_INSTALLED

        if status == InstallStatus.NOT_INSTALLED:
            self._btn.setText(ACTION_DOWNLOAD)
            self._btn.setObjectName("")
        elif status == InstallStatus.UPDATE:
            self._btn.setText(ACTION_UPDATE)
            self._btn.setObjectName("Accent")
        else:
            self._btn.setText("✓ " + STATUS_INSTALLED)
            self._btn.setObjectName("")
        self._btn.style().unpolish(self._btn)
        self._btn.style().polish(self._btn)

    def _set_image(self, pixmap: QPixmap) -> None:
        try:
            scaled = pixmap.scaled(
                194, 90,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._img_label.setPixmap(scaled)
        except RuntimeError:
            pass

    def refresh(self) -> None:
        self._refresh_button()

    @property
    def display_name(self) -> str:
        return self._display_name

    def matches(self, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        if q in self._display_name.lower():
            return True
        return any(q in (e.name or "").lower() or q in (e.game or "").lower() for e in self._entries)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._entries)
        super().mousePressEvent(event)
