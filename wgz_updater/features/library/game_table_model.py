from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtGui import QIcon, QPixmap

from ...core.config import Game
from ...core.paths import icon as icon_path
from ...resources.strings_vi import (
    LIBRARY_HEADER_ACTION,
    LIBRARY_HEADER_GAME,
    LIBRARY_HEADER_NAME,
    LIBRARY_HEADER_STATUS,
    LIBRARY_HEADER_VERSION,
    STATUS_INSTALLED,
    STATUS_NOT_INSTALLED,
    STATUS_UPDATE,
)
from .models import InstallRegistry, InstallStatus

COL_NAME, COL_GAME, COL_VERSION, COL_STATUS, COL_ACTION = range(5)
HEADERS = (
    LIBRARY_HEADER_NAME,
    LIBRARY_HEADER_GAME,
    LIBRARY_HEADER_VERSION,
    LIBRARY_HEADER_STATUS,
    LIBRARY_HEADER_ACTION,
)

_STATUS_LABELS = {
    InstallStatus.INSTALLED: STATUS_INSTALLED,
    InstallStatus.UPDATE: STATUS_UPDATE,
    InstallStatus.NOT_INSTALLED: STATUS_NOT_INSTALLED,
}

_TYPE_ICON = {
    "exe": "exe_icon.png",
    "rar": "rar_icon.png",
    "zip": "zip_icon.png",
}


def _icon_for_game(game: Game) -> QIcon:
    fname = _TYPE_ICON.get(game.type.lower(), "unknown_icon.png")
    p = icon_path(fname)
    if p.exists():
        return QIcon(QPixmap(str(p)))
    return QIcon()


class GameTableModel(QAbstractTableModel):
    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._games: list[Game] = []

    def set_games(self, games: list[Game]) -> None:
        self.beginResetModel()
        self._games = list(games)
        self.endResetModel()

    def game_at(self, row: int) -> Game | None:
        if 0 <= row < len(self._games):
            return self._games[row]
        return None

    def status_at(self, row: int) -> InstallStatus:
        g = self.game_at(row)
        return self._registry.status_for(g) if g else InstallStatus.NOT_INSTALLED

    def refresh_row(self, row: int) -> None:
        if 0 <= row < len(self._games):
            self.dataChanged.emit(
                self.index(row, 0),
                self.index(row, len(HEADERS) - 1),
            )

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._games)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return HEADERS[section]
        return section + 1

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        game = self._games[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DecorationRole and col == COL_NAME:
            return _icon_for_game(game)

        if role == Qt.ItemDataRole.DisplayRole:
            if col == COL_NAME:
                return game.name
            if col == COL_GAME:
                return game.game
            if col == COL_VERSION:
                return game.version
            if col == COL_STATUS:
                return _STATUS_LABELS[self._registry.status_for(game)]
            if col == COL_ACTION:
                return ""

        if role == Qt.ItemDataRole.ToolTipRole:
            if col == COL_NAME:
                return game.path_guide
        return None
