from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt

from .models import AccountRecord

_HEADERS = ["Dịch vụ", "Tên hiển thị", "Username", "Mật khẩu", "Game"]
COL_SERVICE, COL_NICKNAME, COL_USERNAME, COL_PASSWORD, COL_GAME = range(5)


class AccountListModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._records: list[AccountRecord] = []
        self._mask = True

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(_HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return _HEADERS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        rec = self._records[index.row()]
        col = index.column()
        if col == COL_SERVICE:
            return rec.service
        if col == COL_NICKNAME:
            return rec.nickname or rec.username
        if col == COL_USERNAME:
            return rec.username
        if col == COL_PASSWORD:
            return "•" * 8 if self._mask else rec.password
        if col == COL_GAME:
            return rec.game
        return None

    def set_records(self, records: list[AccountRecord]) -> None:
        self.beginResetModel()
        self._records = list(records)
        self.endResetModel()

    def set_mask_password(self, mask: bool) -> None:
        self._mask = mask
        self.layoutChanged.emit()

    def add(self, record: AccountRecord) -> None:
        row = len(self._records)
        self.beginInsertRows(QModelIndex(), row, row)
        self._records.append(record)
        self.endInsertRows()

    def remove(self, row: int) -> None:
        if 0 <= row < len(self._records):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._records.pop(row)
            self.endRemoveRows()

    def record_at(self, row: int) -> AccountRecord | None:
        if 0 <= row < len(self._records):
            return self._records[row]
        return None

    def all_records(self) -> list[AccountRecord]:
        return list(self._records)
