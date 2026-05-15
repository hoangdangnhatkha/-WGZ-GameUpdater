"""TheaterRail — left-side vertical list of games (theaters).

Each entry shows a thumbnail, game name, service tags, and asset count.
The currently selected theater is highlighted with the acid-lime accent.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ...core.config import GameTheme
from ..library.image_loader import ImageLoader

_THUMB_W = 56
_THUMB_H = 36


class TheaterEntry(QFrame):
    clicked = pyqtSignal(str)

    def __init__(
        self,
        game_name: str,
        count: int,
        services: list[str],
        image_url: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("TheaterEntry")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("active", False)
        self._game = game_name
        self._image_url = image_url
        self._pixmap: QPixmap | None = None

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)

        # Thumb
        self._thumb = QLabel(self)
        self._thumb.setObjectName("TheaterThumb")
        self._thumb.setFixedSize(_THUMB_W, _THUMB_H)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self._thumb)

        # Text col
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(2)

        self._name = QLabel(game_name.upper(), self)
        self._name.setObjectName("TheaterName")
        col.addWidget(self._name)

        svc_text = " · ".join(s.upper() for s in services[:3]) if services else "—"
        self._svc = QLabel(svc_text, self)
        self._svc.setObjectName("TheaterServices")
        col.addWidget(self._svc)
        row.addLayout(col, 1)

        # Count badge
        self._count = QLabel(f"{count:02d}", self)
        self._count.setObjectName("TheaterCount")
        self._count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count.setFixedWidth(34)
        row.addWidget(self._count)

        if image_url:
            ImageLoader.instance().request(image_url, self._on_image)

    def _on_image(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        try:
            scaled = pixmap.scaled(
                _THUMB_W, _THUMB_H,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._thumb.setPixmap(scaled)
        except RuntimeError:
            pass

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def update_count(self, count: int) -> None:
        self._count.setText(f"{count:02d}")

    def update_services(self, services: list[str]) -> None:
        text = " · ".join(s.upper() for s in services[:3]) if services else "—"
        self._svc.setText(text)

    @property
    def game(self) -> str:
        return self._game

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._game)
        super().mousePressEvent(event)

    def matches(self, q: str) -> bool:
        return not q or q.lower() in self._game.lower()


class TheaterRail(QWidget):
    """Vertical scrollable list of TheaterEntry. Emits selected(game_name)."""

    selected = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("TheaterRail")
        self._entries: list[TheaterEntry] = []
        self._active: str = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QFrame(self)
        header.setObjectName("RailHeader")
        hlay = QVBoxLayout(header)
        hlay.setContentsMargins(14, 12, 14, 10)
        hlay.setSpacing(6)

        title = QLabel("THEATERS", header)
        title.setObjectName("RailTitle")
        hlay.addWidget(title)

        self._search = QLineEdit(header)
        self._search.setObjectName("CommandInput")
        self._search.setPlaceholderText("> filter...")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._filter)
        hlay.addWidget(self._search)

        outer.addWidget(header)

        # List
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._list = QWidget()
        self._list.setObjectName("RailList")
        self._list_lay = QVBoxLayout(self._list)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(0)
        self._list_lay.addStretch(1)
        self._scroll.setWidget(self._list)
        outer.addWidget(self._scroll, 1)

        # Empty state
        self._empty = QLabel(
            "CHƯA CÓ TÀI KHOẢN\n// TẢI TỪ DRIVE ĐỂ NẠP", self
        )
        self._empty.setObjectName("RailEmpty")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setWordWrap(True)
        self._empty.hide()
        outer.addWidget(self._empty)

    def populate(
        self,
        accounts_by_game: dict,
        themes: dict[str, GameTheme] | None = None,
    ) -> None:
        # Clear
        while self._list_lay.count() > 1:
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._entries.clear()

        themes = themes or {}

        # Only show games that have at least 1 account
        all_games = sorted(
            [g for g in accounts_by_game if accounts_by_game.get(g)],
            key=lambda g: g.lower(),
        )

        if not all_games:
            self._empty.show()
            self._scroll.hide()
            return
        self._empty.hide()
        self._scroll.show()

        for game in all_games:
            recs = accounts_by_game.get(game, [])
            services = sorted({r.service for r in recs if hasattr(r, "service") and r.service})
            theme = themes.get(game)
            image_url = ""
            if theme:
                image_url = theme.image or (theme.slideshow[0] if theme.slideshow else "")
            entry = TheaterEntry(
                game, len(recs), services, image_url, parent=self._list
            )
            entry.clicked.connect(self._on_entry_clicked)
            self._entries.append(entry)
            self._list_lay.insertWidget(self._list_lay.count() - 1, entry)

        # Keep current selection if still present, otherwise pick first
        if self._active and any(e.game == self._active for e in self._entries):
            self._refresh_active()
        elif self._entries:
            self.set_active(self._entries[0].game, emit=True)

    def _on_entry_clicked(self, game: str) -> None:
        self.set_active(game, emit=True)

    def set_active(self, game: str, emit: bool = False) -> None:
        if game == self._active and not emit:
            return
        self._active = game
        self._refresh_active()
        if emit:
            self.selected.emit(game)

    def _refresh_active(self) -> None:
        for e in self._entries:
            e.set_active(e.game == self._active)

    def update_entry(self, game: str, count: int, services: list[str]) -> None:
        for e in self._entries:
            if e.game == game:
                e.update_count(count)
                e.update_services(services)
                return

    def _filter(self, text: str) -> None:
        q = text.strip().lower()
        for e in self._entries:
            e.setVisible(e.matches(q))

    @property
    def active_game(self) -> str:
        return self._active
