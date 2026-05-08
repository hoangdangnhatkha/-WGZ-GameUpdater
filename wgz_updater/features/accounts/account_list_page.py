from __future__ import annotations

import logging
import subprocess

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSplitter, QVBoxLayout, QWidget,
)

from ...core.local_config import LocalConfig
from ...resources.strings_vi import (
    ACTION_ADD_ACCOUNT, ACTION_AUTO_LOGIN, ACTION_BACK,
    ACTION_LOAD_DRIVE, ACTION_SAVE_DRIVE, DIALOG_ERROR_TITLE,
    MSG_SELECT_ACCOUNT,
)
from .trailer_player import TrailerPlayer
from .account_dialog import AccountDialog
from .models import AccountRecord
from .riot_login import RiotLoginWorker

log = logging.getLogger(__name__)


class AccountRow(QFrame):
    login_requested = pyqtSignal(object)   # AccountRecord
    edit_requested = pyqtSignal(object)    # AccountRecord
    delete_requested = pyqtSignal(object)  # AccountRecord

    def __init__(self, record: AccountRecord, parent=None) -> None:
        super().__init__(parent)
        self._record = record
        self.setObjectName("AccountRow")

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(8)

        info = QVBoxLayout()
        nick = record.nickname or record.username
        nick_lbl = QLabel(nick, self)
        nick_lbl.setObjectName("AccountNickname")
        info.addWidget(nick_lbl)
        meta = f"{record.service}  •  {record.game}" if record.game else record.service
        meta_lbl = QLabel(meta, self)
        meta_lbl.setObjectName("AccountMeta")
        info.addWidget(meta_lbl)
        row.addLayout(info, 1)

        copy_btn = QPushButton("Copy PW", self)
        copy_btn.setFixedWidth(70)
        copy_btn.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(record.password)
        )
        row.addWidget(copy_btn)

        login_btn = QPushButton(ACTION_AUTO_LOGIN, self)
        login_btn.setObjectName("Accent")
        login_btn.setFixedWidth(90)
        login_btn.clicked.connect(lambda: self.login_requested.emit(self._record))
        row.addWidget(login_btn)

        edit_btn = QPushButton("Sửa", self)
        edit_btn.setFixedWidth(44)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._record))
        row.addWidget(edit_btn)

        del_btn = QPushButton("Xóa", self)
        del_btn.setFixedWidth(44)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._record))
        row.addWidget(del_btn)


class AccountListPage(QWidget):
    back_requested = pyqtSignal()
    dirty_changed = pyqtSignal(bool)
    save_requested = pyqtSignal()
    load_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._service: str = ""
        self._records: list[AccountRecord] = []
        self._game_names: list[str] = []
        self._login_worker: RiotLoginWorker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(8)

        # Top bar
        top = QHBoxLayout()
        back_btn = QPushButton(ACTION_BACK, self)
        back_btn.setObjectName("BackButton")
        back_btn.clicked.connect(self.back_requested)
        top.addWidget(back_btn)
        self._title_lbl = QLabel(self)
        self._title_lbl.setStyleSheet("font-size:18px;font-weight:600;")
        top.addWidget(self._title_lbl)
        top.addStretch(1)
        self._save_btn = QPushButton(ACTION_SAVE_DRIVE, self)
        self._save_btn.setObjectName("Accent")
        self._save_btn.setEnabled(False)
        top.addWidget(self._save_btn)
        load_btn = QPushButton(ACTION_LOAD_DRIVE, self)
        top.addWidget(load_btn)
        outer.addLayout(top)

        # Splitter: account list | trailer
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        outer.addWidget(splitter, 1)

        # Left: scroll area of account rows
        left = QWidget(self)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._rows_widget = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setSpacing(6)
        self._rows_layout.setContentsMargins(0, 0, 4, 4)
        self._rows_layout.addStretch(1)
        self._scroll.setWidget(self._rows_widget)
        left_layout.addWidget(self._scroll, 1)

        add_btn = QPushButton(ACTION_ADD_ACCOUNT, self)
        add_btn.clicked.connect(self._on_add)
        left_layout.addWidget(add_btn)
        splitter.addWidget(left)

        # Right: trailer player
        self._trailer = TrailerPlayer(self)
        splitter.addWidget(self._trailer)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        # Wire Drive buttons
        self._save_btn.clicked.connect(self.save_requested)
        load_btn.clicked.connect(self.load_requested)

    def show_service(
        self,
        service_name: str,
        records: list[AccountRecord],
        game_names: list[str] | None = None,
    ) -> None:
        self._service = service_name
        self._records = list(records)
        self._game_names = game_names or []
        self._title_lbl.setText(service_name)
        self._render_rows()
        self._save_btn.setEnabled(False)

    def _render_rows(self) -> None:
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for rec in self._records:
            row_widget = AccountRow(rec, self._rows_widget)
            row_widget.login_requested.connect(self._on_login)
            row_widget.edit_requested.connect(self._on_edit)
            row_widget.delete_requested.connect(self._on_delete)
            self._rows_layout.insertWidget(self._rows_layout.count() - 1, row_widget)

    def get_records(self) -> list[AccountRecord]:
        return list(self._records)

    def set_records(self, records: list[AccountRecord]) -> None:
        self._records = list(records)
        self._render_rows()

    def _mark_dirty(self) -> None:
        self._save_btn.setEnabled(True)
        self.dirty_changed.emit(True)

    def _on_add(self) -> None:
        dlg = AccountDialog(self, game_names=self._game_names)
        if dlg.exec():
            self._records.append(dlg.get_record())
            self._render_rows()
            self._mark_dirty()

    def _on_edit(self, record: AccountRecord) -> None:
        dlg = AccountDialog(self, record=record, game_names=self._game_names)
        if dlg.exec():
            idx = self._records.index(record)
            self._records[idx] = dlg.get_record()
            self._render_rows()
            self._mark_dirty()

    def _on_delete(self, record: AccountRecord) -> None:
        from ...widgets.dialogs import wgz_ask
        if wgz_ask(self, "Xóa tài khoản", f"Xóa '{record.nickname or record.username}'?"):
            self._records.remove(record)
            self._render_rows()
            self._mark_dirty()

    def _on_login(self, record: AccountRecord) -> None:
        local = LocalConfig()
        service_lower = record.service.lower()
        if service_lower == "steam":
            steam = local.steam_path
            if not steam:
                from ...widgets.dialogs import wgz_warn
                wgz_warn(self, DIALOG_ERROR_TITLE, "Chưa tìm thấy Steam. Vui lòng thiết lập đường dẫn trong Cài Đặt.")
                return
            try:
                subprocess.Popen([steam, "-login", record.username, record.password])
            except Exception as exc:
                log.exception("Steam login failed")
                from ...widgets.dialogs import wgz_error
                wgz_error(self, DIALOG_ERROR_TITLE, str(exc))
        elif service_lower == "riot":
            if self._login_worker and self._login_worker.isRunning():
                return
            worker = RiotLoginWorker(
                username=record.username, password=record.password, parent=self
            )
            worker.failed.connect(
                lambda msg: (
                    __import__("wgz_updater.widgets.dialogs", fromlist=["wgz_error"]).wgz_error(
                        self, DIALOG_ERROR_TITLE, msg
                    )
                )
            )
            worker.finished.connect(lambda: setattr(self, "_login_worker", None))
            self._login_worker = worker
            worker.start()
        else:
            from ...widgets.dialogs import wgz_info
            wgz_info(self, "Đăng nhập", f"Dịch vụ '{record.service}' chưa hỗ trợ đăng nhập tự động.")
