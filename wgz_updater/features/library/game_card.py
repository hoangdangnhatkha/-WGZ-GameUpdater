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
    clicked = pyqtSignal(object)  # emits Game

    def __init__(
        self,
        game: Game,
        registry: InstallRegistry,
        image_url: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._game = game
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

        # Tag badge
        tag = (game.tag or "").upper()
        if tag in _TAG_COLORS:
            bg, fg = _TAG_COLORS[tag]
            self._tag = QLabel(tag, self)
            self._tag.setStyleSheet(
                f"background:{bg};color:{fg};border-radius:3px;"
                f"padding:1px 5px;font-size:9px;font-weight:700;"
            )
            layout.addWidget(self._tag)

        # Name
        name_lbl = QLabel(game.name, self)
        name_lbl.setObjectName("GameCardName")
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        # Action button
        self._btn = QPushButton(self)
        self._btn.clicked.connect(lambda: self.clicked.emit(self._game))
        layout.addWidget(self._btn)

        self._refresh_button()

        if image_url:
            ImageLoader.instance().request(image_url, self._set_image)

    def _refresh_button(self) -> None:
        status = self._registry.status_for(self._game)
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
        scaled = pixmap.scaled(
            194, 90,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._img_label.setPixmap(scaled)

    def refresh(self) -> None:
        """Call after install status changes."""
        self._refresh_button()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._game)
        super().mousePressEvent(event)
