from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QLineEdit, QHBoxLayout,
    QScrollArea, QVBoxLayout, QWidget,
)

from ...core.config import GameTheme
from ...resources.strings_vi import NAV_ACCOUNTS
from ..library.image_loader import ImageLoader

_CARD_W = 210
_CARD_GAP = 14


class GameAccountCard(QFrame):
    clicked = pyqtSignal(str)  # game name

    def __init__(
        self,
        game_name: str,
        count: int,
        image_url: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("GameCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(_CARD_W)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 10)
        layout.setSpacing(4)

        self._img = QLabel(self)
        self._img.setFixedSize(194, 90)
        self._img.setObjectName("HeroImage")
        self._img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._img)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 6, 0, 0)
        name_lbl = QLabel(game_name, self)
        name_lbl.setObjectName("GameCardName")
        name_lbl.setWordWrap(True)
        meta_row.addWidget(name_lbl, 1)
        layout.addLayout(meta_row)

        count_lbl = QLabel(f"{count:02d} ACC", self)
        count_lbl.setObjectName("GameCardMeta")
        layout.addWidget(count_lbl)

        self._game = game_name

        if image_url:
            ImageLoader.instance().request(image_url, self._set_image)

    def _set_image(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            194, 90,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._img.setPixmap(scaled)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._game)
        super().mousePressEvent(event)

    def matches(self, q: str) -> bool:
        return not q or q.lower() in self._game.lower()


class ServiceGridPage(QWidget):
    """Grid of GAME cards for the Accounts tab. Click a game → list of its accounts.

    Renamed conceptually from 'service' to 'game' to match the original app and the
    fact that accounts are grouped by game (e.g., 'Elden Ring Nightreign').
    """

    service_selected = pyqtSignal(str)  # game name (kept signal name for back-compat)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 18, 28, 18)
        outer.setSpacing(12)

        # Header row
        header = QHBoxLayout()
        title = QLabel(NAV_ACCOUNTS, self)
        title.setStyleSheet(
            "font-family:'Bahnschrift','Inter Tight',sans-serif;"
            "font-size:26px;font-weight:700;letter-spacing:1.2px;"
        )
        header.addWidget(title)
        header.addStretch(1)
        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Tìm kiếm game...")
        self._search.setFixedWidth(260)
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._filter)
        header.addWidget(self._search)
        outer.addLayout(header)

        # Subtitle
        sub = QLabel("// CHỌN GAME ĐỂ XEM TÀI KHOẢN ĐÃ LƯU", self)
        sub.setStyleSheet(
            "font-family:'Cascadia Mono',Consolas,monospace;"
            "font-size:10px;color:#5e5e62;letter-spacing:1.2px;"
        )
        outer.addWidget(sub)

        # Scroll area
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(_CARD_GAP)
        self._grid.setContentsMargins(0, 0, 4, 4)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._scroll.setWidget(self._grid_widget)
        outer.addWidget(self._scroll, 1)

        self._cards: list[GameAccountCard] = []
        self._cur_cols = 1

    def populate(
        self,
        accounts_by_game: dict,
        themes: dict[str, GameTheme] | None = None,
    ) -> None:
        """accounts_by_game: {game_name: [account_dict|AccountRecord, ...]}
        themes: theme dict — used to source images and the canonical list of games."""
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        themes = themes or {}
        # Union: every theme key + every game with accounts
        all_games = list(themes.keys())
        for g in accounts_by_game.keys():
            if g not in all_games:
                all_games.append(g)

        # Sort: games with accounts first, then alphabetical
        def sort_key(g: str) -> tuple:
            count = len(accounts_by_game.get(g, []))
            return (0 if count > 0 else 1, g.lower())
        all_games.sort(key=sort_key)

        for game in all_games:
            count = len(accounts_by_game.get(game, []))
            theme = themes.get(game)
            image_url = ""
            if theme:
                image_url = theme.image or (theme.slideshow[0] if theme.slideshow else "")
            card = GameAccountCard(game, count, image_url=image_url, parent=self._grid_widget)
            card.clicked.connect(self.service_selected)
            self._cards.append(card)
        self._relayout()

    def _filter(self, text: str) -> None:
        q = text.strip().lower()
        for c in self._cards:
            c.setVisible(c.matches(q))
        self._relayout(force=True)

    def _columns_for_width(self, width: int) -> int:
        avail = max(0, width - 8)
        return max(1, (avail + _CARD_GAP) // (_CARD_W + _CARD_GAP))

    def _relayout(self, *, force: bool = False) -> None:
        cols = self._columns_for_width(self._scroll.viewport().width())
        if not force and cols == self._cur_cols and self._grid.count() > 0:
            return
        self._cur_cols = cols
        for i in reversed(range(self._grid.count())):
            it = self._grid.takeAt(i)
            if it and it.widget():
                it.widget().setParent(self._grid_widget)
        visible = [c for c in self._cards if not c.isHidden()]
        for idx, card in enumerate(visible):
            self._grid.addWidget(card, idx // cols, idx % cols)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._relayout()
