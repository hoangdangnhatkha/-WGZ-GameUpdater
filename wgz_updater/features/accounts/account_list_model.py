from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt

from .models import AccountRecord

HEADERS = ("Dịch vụ", "Tên đăng nhập", "Mật khẩu", "Ghi chú")


class AccountListModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._records: list[AccountRecord] = []
        self._mask_password = True

    def set_records(self, records: list[AccountRecord]) -> None:
        self.beginResetModel()
        self._records = list(records)
        self.endResetModel()

    def records(self) -> list[AccountRecord]:
        return list(self._records)

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

    def set_mask_password(self, mask: bool) -> None:
        self._mask_password = mask
        if self._records:
            self.dataChanged.emit(
                self.index(0, 2),
                self.index(len(self._records) - 1, 2),
            )

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return HEADERS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        rec = self._records[index.row()]
        col = index.column()
        if col == 0:
            return rec.service
        if col == 1:
            return rec.username
        if col == 2:
            return "•" * 8 if self._mask_password and rec.password else rec.password
        if col == 3:
            return rec.note
        return None
