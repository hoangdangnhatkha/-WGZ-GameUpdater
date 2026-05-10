from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from ...core.config import AppConfig, Game
from ...resources.strings_vi import ACTION_REFRESH, NAV_LIBRARY
from .featured_hero import FeaturedHero
from .game_row import GameRow
from .models import InstallRegistry, InstallStatus

log = logging.getLogger(__name__)


class GameGridPage(QWidget):
    """Library landing — featured hero + dense manifest of games."""

    game_selected = pyqtSignal(object)   # list[Game]
    refresh_requested = pyqtSignal()

    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._config: AppConfig | None = None
        self._rows: list[GameRow] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 16, 28, 14)
        outer.setSpacing(10)

        # ── Header row ──────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(8)
        title_col = QVBoxLayout()
        title_col.setSpacing(0)

        title = QLabel(NAV_LIBRARY.upper(), self)
        title.setObjectName("PageTitle")
        title_col.addWidget(title)

        self._sub = QLabel("// CATALOG · LOADING…", self)
        self._sub.setObjectName("PageSub")
        title_col.addWidget(self._sub)

        header.addLayout(title_col, 1)

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("›  search catalog")
        self._search.setObjectName("CommandInput")
        self._search.setClearButtonEnabled(True)
        self._search.setFixedWidth(280)
        self._search.textChanged.connect(self._filter)
        header.addWidget(self._search)

        refresh_btn = QPushButton(ACTION_REFRESH.upper(), self)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_requested)
        header.addWidget(refresh_btn)

        outer.addLayout(header)

        # ── Featured hero ───────────────────────────────────────
        self._hero = FeaturedHero(self._registry, self)
        self._hero.clicked.connect(self.game_selected)
        outer.addWidget(self._hero)

        # ── Section divider ─────────────────────────────────────
        sect_row = QHBoxLayout()
        sect_row.setContentsMargins(0, 4, 0, 2)
        sect_row.setSpacing(10)
        sect = QLabel("// CATALOG", self)
        sect.setObjectName("PageSection")
        sect_row.addWidget(sect)
        rule = QFrame(self)
        rule.setFrameShape(QFrame.Shape.HLine)
        rule.setObjectName("SectionRule")
        rule.setFixedHeight(1)
        sect_row.addWidget(rule, 1)
        self._count_lbl = QLabel("00 / 00", self)
        self._count_lbl.setObjectName("PageSection")
        sect_row.addWidget(self._count_lbl)
        outer.addLayout(sect_row)

        # ── Manifest (rows) ─────────────────────────────────────
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._rows_widget = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setSpacing(2)
        self._rows_layout.setContentsMargins(0, 0, 6, 4)
        self._rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._rows_widget)
        outer.addWidget(self._scroll, 1)

    # ── public ────────────────────────────────────────────────────

    def populate(self, config: AppConfig) -> None:
        self._config = config
        groups = self._group(config.games)

        # Pick a featured group (HOT/UPD/NEW with rich theme art preferred)
        featured_idx = self._pick_featured(groups, config.themes)
        if featured_idx >= 0 and groups:
            key, entries = groups[featured_idx]
            theme = config.themes.get(key)
            img = ""
            if theme:
                img = theme.slideshow[0] if theme.slideshow else theme.image
            self._hero.set_game(entries, key, img)
            groups.pop(featured_idx)
            self._hero.show()
        else:
            self._hero.hide()

        # Clear rows
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows.clear()

        # Build rows
        for i, (key, entries) in enumerate(groups, start=1):
            theme = config.themes.get(key)
            img = ""
            if theme:
                img = theme.slideshow[0] if theme.slideshow else theme.image
            row = GameRow(
                entries, self._registry,
                image_url=img, index=i, parent=self._rows_widget,
            )
            row.clicked.connect(self.game_selected)
            self._rows_layout.addWidget(row)
            self._rows.append(row)

        # Header counts
        total = len(config.games)
        installed = sum(
            1 for g in config.games
            if self._registry.status_for(g) == InstallStatus.INSTALLED
        )
        self._sub.setText(
            f"// CATALOG · {total:02d} ENTRIES · {installed:02d} INSTALLED · STREAMING ONLINE"
        )
        self._count_lbl.setText(f"{len(self._rows):02d} / {len(self._rows):02d}")

    def refresh_cards(self) -> None:
        for r in self._rows:
            r.refresh()

    # ── helpers ───────────────────────────────────────────────────

    @staticmethod
    def _group(games: list[Game]) -> list[tuple[str, list[Game]]]:
        order: list[str] = []
        groups: dict[str, list[Game]] = {}
        for g in games:
            key = (g.game or g.name or "").strip() or g.id
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(g)
        return [(k, groups[k]) for k in order]

    @staticmethod
    def _pick_featured(groups, themes) -> int:
        # 1) hot/new/upd-tagged with rich art
        for i, (key, entries) in enumerate(groups):
            tags = {(e.tag or "").upper() for e in entries}
            if tags & {"HOT", "NEW", "UPD"}:
                t = themes.get(key)
                if t and (t.slideshow or t.image):
                    return i
        # 2) any tagged
        for i, (key, entries) in enumerate(groups):
            if any((e.tag or "").upper() for e in entries):
                t = themes.get(key)
                if t and (t.slideshow or t.image):
                    return i
        # 3) first with theme art
        for i, (key, _) in enumerate(groups):
            t = themes.get(key)
            if t and (t.slideshow or t.image):
                return i
        return 0 if groups else -1

    def _filter(self, text: str) -> None:
        q = text.strip().lower()
        visible = 0
        for row in self._rows:
            ok = row.matches(q)
            row.setVisible(ok)
            if ok:
                visible += 1
        self._count_lbl.setText(f"{visible:02d} / {len(self._rows):02d}")
