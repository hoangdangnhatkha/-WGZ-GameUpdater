from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from ...core.config import AppConfig, Game
from ...resources.strings_vi import ACTION_REFRESH, NAV_LIBRARY
from .game_card import GameCard
from .models import InstallRegistry

log = logging.getLogger(__name__)
_COLS = 3


class GameGridPage(QWidget):
    game_selected = pyqtSignal(object)   # Game
    refresh_requested = pyqtSignal()

    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._cards: list[GameCard] = []
        self._config: AppConfig | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(10)

        # Header row
        header = QHBoxLayout()
        title = QLabel(NAV_LIBRARY, self)
        title.setStyleSheet("font-size:22px;font-weight:600;")
        header.addWidget(title)
        header.addStretch(1)
        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Tìm kiếm game...")
        self._search.setClearButtonEnabled(True)
        self._search.setFixedWidth(240)
        self._search.textChanged.connect(self._filter)
        header.addWidget(self._search)
        refresh_btn = QPushButton(ACTION_REFRESH, self)
        refresh_btn.clicked.connect(self.refresh_requested)
        header.addWidget(refresh_btn)
        outer.addLayout(header)

        # Scroll area with grid
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(10)
        self._grid.setContentsMargins(0, 0, 4, 4)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._scroll.setWidget(self._grid_widget)
        outer.addWidget(self._scroll, 1)

    def populate(self, config: AppConfig) -> None:
        self._config = config
        self._render(config.games)

    @staticmethod
    def _group(games: list[Game]) -> list[tuple[str, list[Game]]]:
        """Group games by canonical key (game.game, falling back to game.name).
        Preserves first-seen order."""
        order: list[str] = []
        groups: dict[str, list[Game]] = {}
        for g in games:
            key = (g.game or g.name or "").strip() or g.id
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(g)
        return [(k, groups[k]) for k in order]

    def _render(self, games: list[Game]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        for i, (key, entries) in enumerate(self._group(games)):
            image_url = ""
            if self._config:
                theme = self._config.themes.get(key)
                if theme is None:
                    for e in entries:
                        theme = (
                            self._config.themes.get(e.game)
                            or self._config.themes.get(e.name)
                        )
                        if theme:
                            break
                if theme:
                    image_url = theme.image or (theme.slideshow[0] if theme.slideshow else "")
            card = GameCard(
                entries, self._registry,
                display_name=key, image_url=image_url, parent=self._grid_widget,
            )
            card.clicked.connect(self.game_selected)
            self._grid.addWidget(card, i // _COLS, i % _COLS)
            self._cards.append(card)

    def _filter(self, text: str) -> None:
        q = text.strip().lower()
        for card in self._cards:
            card.setVisible(card.matches(q))

    def refresh_cards(self) -> None:
        """Refresh all card button states (call after install/update)."""
        for card in self._cards:
            card.refresh()
