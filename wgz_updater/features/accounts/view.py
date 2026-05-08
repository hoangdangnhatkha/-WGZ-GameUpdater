from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ...resources.strings_vi import (
    ACTION_AUTO_LOGIN,
    DIALOG_ERROR_TITLE,
    NAV_ACCOUNTS,
)
from .account_list_model import AccountListModel
from .models import AccountRecord
from .riot_login import RiotLoginWorker
from .trailer_player import TrailerPlayer

log = logging.getLogger(__name__)


class AccountsView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._login_worker: RiotLoginWorker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel(NAV_ACCOUNTS, self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch(1)
        self._mask_toggle = QCheckBox("Ẩn mật khẩu", self)
        self._mask_toggle.setChecked(True)
        self._mask_toggle.toggled.connect(self._on_mask_toggle)
        header.addWidget(self._mask_toggle)
        outer.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        outer.addWidget(splitter, 1)

        # Left: account table + actions
        left = QWidget(self)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self._model = AccountListModel(self)
        self._table = QTableView(self)
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setDefaultSectionSize(34)
        left_layout.addWidget(self._table, 1)

        actions = QHBoxLayout()
        add_btn = QPushButton("Thêm", self)
        add_btn.clicked.connect(self._on_add)
        del_btn = QPushButton("Xóa", self)
        del_btn.clicked.connect(self._on_delete)
        copy_btn = QPushButton("Copy mật khẩu", self)
        copy_btn.clicked.connect(self._on_copy_password)
        login_btn = QPushButton(ACTION_AUTO_LOGIN, self)
        login_btn.setObjectName("Accent")
        login_btn.clicked.connect(self._on_auto_login)
        actions.addWidget(add_btn)
        actions.addWidget(del_btn)
        actions.addWidget(copy_btn)
        actions.addStretch(1)
        actions.addWidget(login_btn)
        left_layout.addLayout(actions)

        splitter.addWidget(left)

        # Right: trailer player
        self._trailer = TrailerPlayer(self)
        splitter.addWidget(self._trailer)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

    def set_records(self, records: list[AccountRecord]) -> None:
        self._model.set_records(records)

    def play_trailer(self, url: str) -> None:
        self._trailer.play(url)

    def _on_mask_toggle(self, checked: bool) -> None:
        self._model.set_mask_password(checked)

    def _selected_row(self) -> int:
        sel = self._table.selectionModel().selectedRows()
        return sel[0].row() if sel else -1

    def _on_add(self) -> None:
        service, ok = QInputDialog.getText(self, "Dịch vụ", "Tên dịch vụ:")
        if not ok or not service.strip():
            return
        username, ok = QInputDialog.getText(self, "Tên đăng nhập", "Username:")
        if not ok:
            return
        password, ok = QInputDialog.getText(self, "Mật khẩu", "Password:", QLineEdit.EchoMode.Password)
        if not ok:
            return
        self._model.add(AccountRecord(service=service.strip(), username=username, password=password))

    def _on_delete(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        if QMessageBox.question(self, "Xóa", "Xóa tài khoản đã chọn?") == QMessageBox.StandardButton.Yes:
            self._model.remove(row)

    def _on_copy_password(self) -> None:
        row = self._selected_row()
        rec = self._model.record_at(row)
        if rec:
            QGuiApplication.clipboard().setText(rec.password)

    def _on_auto_login(self) -> None:
        row = self._selected_row()
        rec = self._model.record_at(row)
        if not rec:
            QMessageBox.information(self, NAV_ACCOUNTS, "Hãy chọn một tài khoản.")
            return
        if self._login_worker is not None and self._login_worker.isRunning():
            return
        worker = RiotLoginWorker(
            username=rec.username,
            password=rec.password,
            parent=self,
        )
        worker.failed.connect(lambda msg: QMessageBox.critical(self, DIALOG_ERROR_TITLE, msg))
        worker.finished.connect(lambda: setattr(self, "_login_worker", None))
        self._login_worker = worker
        worker.start()
