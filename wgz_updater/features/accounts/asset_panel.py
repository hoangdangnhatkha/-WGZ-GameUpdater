"""AssetPanel — right-side detail showing all accounts for the active theater.

Each row shows: index, nickname, service tag, username (mono), masked password
with reveal toggle, and inline actions (copy, auto-login, edit, delete).
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ...core.local_config import LocalConfig
from ...resources.strings_vi import (
    ACTION_ADD_ACCOUNT, DIALOG_ERROR_TITLE,
)
from .account_dialog import AccountDialog
from .login_progress_dialog import LoginProgressDialog
from .models import AccountRecord
from .riot_login import RiotLoginWorker
from .steam_login import SteamLoginWorker

log = logging.getLogger(__name__)


def _mask(pw: str) -> str:
    n = len(pw)
    if n == 0:
        return "—"
    return "•" * min(n, 12)


class AssetRow(QFrame):
    login_requested = pyqtSignal(object)
    edit_requested = pyqtSignal(object)
    delete_requested = pyqtSignal(object)

    def __init__(self, record: AccountRecord, index: int, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AssetRow")
        self._record = record
        self._revealed = False

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(14)

        # Index
        idx = QLabel(f"{index:02d}", self)
        idx.setObjectName("AssetIndex")
        idx.setFixedWidth(30)
        idx.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(idx)

        # Identity column
        ident = QVBoxLayout()
        ident.setSpacing(3)
        ident.setContentsMargins(0, 0, 0, 0)

        # Top row: nickname + service tag
        top = QHBoxLayout()
        top.setSpacing(8)
        top.setContentsMargins(0, 0, 0, 0)

        nick_text = record.nickname or record.username or "—"
        nick = QLabel(nick_text, self)
        nick.setObjectName("AssetNick")
        top.addWidget(nick)

        svc = QLabel((record.service or "—").upper(), self)
        svc.setObjectName(self._svc_object_name(record.service))
        svc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(svc)
        top.addStretch(1)
        ident.addLayout(top)

        # Bottom row: username + password
        creds = QHBoxLayout()
        creds.setSpacing(14)
        creds.setContentsMargins(0, 0, 0, 0)

        user_lbl = QLabel("USR", self)
        user_lbl.setObjectName("AssetFieldLabel")
        creds.addWidget(user_lbl)
        user_val = QLabel(record.username or "—", self)
        user_val.setObjectName("AssetFieldValue")
        user_val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        creds.addWidget(user_val)

        creds.addSpacing(12)

        pw_lbl = QLabel("PWD", self)
        pw_lbl.setObjectName("AssetFieldLabel")
        creds.addWidget(pw_lbl)
        self._pw_val = QLabel(_mask(record.password), self)
        self._pw_val.setObjectName("AssetFieldValue")
        self._pw_val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        creds.addWidget(self._pw_val)

        self._reveal = QPushButton("SHOW", self)
        self._reveal.setObjectName("AssetMicroBtn")
        self._reveal.setToolTip("Hiện/ẩn mật khẩu")
        self._reveal.setFixedWidth(50)
        self._reveal.clicked.connect(self._toggle_reveal)
        creds.addWidget(self._reveal)

        creds.addStretch(1)
        ident.addLayout(creds)
        outer.addLayout(ident, 1)

        # Right action cluster
        actions = QHBoxLayout()
        actions.setSpacing(6)
        actions.setContentsMargins(0, 0, 0, 0)

        self._copy = QPushButton("COPY", self)
        self._copy.setObjectName("AssetMicroBtn")
        self._copy.setFixedWidth(58)
        self._copy.setToolTip("Copy mật khẩu")
        self._copy.clicked.connect(self._on_copy)
        actions.addWidget(self._copy)

        login = QPushButton("AUTO-LOGIN", self)
        login.setObjectName("AssetLoginBtn")
        login.setFixedHeight(30)
        login.clicked.connect(lambda: self.login_requested.emit(self._record))
        actions.addWidget(login)

        edit = QPushButton("EDIT", self)
        edit.setObjectName("AssetMicroBtn")
        edit.setFixedWidth(50)
        edit.clicked.connect(lambda: self.edit_requested.emit(self._record))
        actions.addWidget(edit)

        delete = QPushButton("×", self)
        delete.setObjectName("AssetDeleteBtn")
        delete.setFixedWidth(30)
        delete.setToolTip("Xóa tài khoản")
        delete.clicked.connect(lambda: self.delete_requested.emit(self._record))
        actions.addWidget(delete)

        outer.addLayout(actions)

    @staticmethod
    def _svc_object_name(service: str) -> str:
        s = (service or "").lower()
        if s == "steam":
            return "AssetSvcSteam"
        if s == "riot":
            return "AssetSvcRiot"
        return "AssetSvcOther"

    def _toggle_reveal(self) -> None:
        self._revealed = not self._revealed
        if self._revealed:
            self._pw_val.setText(self._record.password or "—")
            self._reveal.setText("HIDE")
        else:
            self._pw_val.setText(_mask(self._record.password))
            self._reveal.setText("SHOW")

    def _on_copy(self) -> None:
        QGuiApplication.clipboard().setText(self._record.password)
        self._copy.setText("OK")
        QTimer.singleShot(900, lambda: self._copy.setText("COPY"))


class AssetPanel(QWidget):
    """Right pane: shows all assets for the currently active theater."""

    save_requested = pyqtSignal()
    load_requested = pyqtSignal()
    add_requested = pyqtSignal(str)        # game
    records_changed = pyqtSignal(str, list)  # game, [AccountRecord]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AssetPanel")
        self._game: str = ""
        self._records: list[AccountRecord] = []
        self._game_names: list[str] = []
        self._login_worker: RiotLoginWorker | SteamLoginWorker | None = None
        self._login_dialog: LoginProgressDialog | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header strip
        header = QFrame(self)
        header.setObjectName("PanelHeader")
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(20, 14, 20, 14)
        hlay.setSpacing(12)

        col = QVBoxLayout()
        col.setSpacing(2)
        self._title = QLabel("// ASSET FILES", self)
        self._title.setObjectName("PanelTitle")
        col.addWidget(self._title)
        self._meta = QLabel("> CHỌN MỘT THEATER ĐỂ XEM TÀI KHOẢN", self)
        self._meta.setObjectName("PanelMeta")
        col.addWidget(self._meta)
        hlay.addLayout(col, 1)

        self._add_btn = QPushButton("+  ADD ASSET", self)
        self._add_btn.setObjectName("PanelAddBtn")
        self._add_btn.clicked.connect(self._on_add)
        self._add_btn.setEnabled(False)
        hlay.addWidget(self._add_btn)

        outer.addWidget(header)

        # Body
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._body = QWidget()
        self._body.setObjectName("PanelBody")
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(0)
        self._body_lay.addStretch(1)
        self._scroll.setWidget(self._body)
        outer.addWidget(self._scroll, 1)

        # Empty state widget (shown when no theater selected or theater has no assets)
        self._empty = QLabel(self)
        self._empty.setObjectName("PanelEmpty")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setWordWrap(True)
        self._empty.setMinimumHeight(160)
        self._empty.hide()
        outer.addWidget(self._empty)

        self._render_empty_initial()

    # ── Public API ──

    def set_game_names(self, names: list[str]) -> None:
        self._game_names = list(names)

    def show_theater(self, game: str, records: list[AccountRecord]) -> None:
        self._game = game
        self._records = list(records)
        self._title.setText(f"// {game.upper()}")
        self._meta.setText(f"> {len(records)} ASSET{'S' if len(records) != 1 else ''} · ENCRYPTED")
        self._add_btn.setEnabled(True)
        self._render_rows()

    def get_records(self) -> list[AccountRecord]:
        return list(self._records)

    def update_records(self, records: list[AccountRecord]) -> None:
        """Called when external load updates the active theater silently."""
        self._records = list(records)
        self._meta.setText(f"> {len(records)} ASSET{'S' if len(records) != 1 else ''} · ENCRYPTED")
        self._render_rows()

    def clear_theater(self) -> None:
        self._game = ""
        self._records = []
        self._title.setText("// ASSET FILES")
        self._meta.setText("> CHỌN MỘT THEATER ĐỂ XEM TÀI KHOẢN")
        self._add_btn.setEnabled(False)
        self._render_empty_initial()

    # ── Rendering ──

    def _render_empty_initial(self) -> None:
        # Clear body
        while self._body_lay.count() > 1:
            it = self._body_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self._scroll.hide()
        self._empty.setText(
            "// NO THEATER SELECTED\n"
            "CHỌN MỘT THEATER Ở CỘT TRÁI ĐỂ XEM TÀI KHOẢN."
        )
        self._empty.show()

    def _render_rows(self) -> None:
        # Clear
        while self._body_lay.count() > 1:
            it = self._body_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        if not self._records:
            self._scroll.hide()
            self._empty.setText(
                f"// {self._game.upper()} · 00 ASSETS\n"
                "CHƯA CÓ TÀI KHOẢN. NHẤN  +ADD ASSET  ĐỂ TẠO MỚI."
            )
            self._empty.show()
            return

        self._empty.hide()
        self._scroll.show()
        for i, rec in enumerate(self._records, start=1):
            row = AssetRow(rec, i, self._body)
            row.login_requested.connect(self._on_login)
            row.edit_requested.connect(self._on_edit)
            row.delete_requested.connect(self._on_delete)
            self._body_lay.insertWidget(self._body_lay.count() - 1, row)

    def _emit_change(self) -> None:
        self.records_changed.emit(self._game, list(self._records))

    # ── Actions ──

    def _on_add(self) -> None:
        if not self._game:
            return
        # Pre-select current game
        names = self._game_names or [self._game]
        dlg = AccountDialog(self, game_names=names)
        # Try to default the game combo to the current theater
        try:
            dlg._game.setCurrentText(self._game)
        except Exception:
            pass
        if dlg.exec():
            rec = dlg.get_record()
            if not rec.game:
                rec.game = self._game
            self._records.append(rec)
            self._meta.setText(f"> {len(self._records)} ASSETS · ENCRYPTED")
            self._render_rows()
            self._emit_change()

    def _on_edit(self, record: AccountRecord) -> None:
        names = self._game_names or [self._game]
        dlg = AccountDialog(self, record=record, game_names=names)
        if dlg.exec():
            try:
                idx = self._records.index(record)
            except ValueError:
                return
            self._records[idx] = dlg.get_record()
            self._render_rows()
            self._emit_change()

    def _on_delete(self, record: AccountRecord) -> None:
        from ...widgets.dialogs import wgz_ask
        label = record.nickname or record.username or "?"
        if wgz_ask(self, "Xóa tài khoản", f"Xóa '{label}'?"):
            try:
                self._records.remove(record)
            except ValueError:
                return
            self._meta.setText(f"> {len(self._records)} ASSET{'S' if len(self._records) != 1 else ''} · ENCRYPTED")
            self._render_rows()
            self._emit_change()

    def _on_login(self, record: AccountRecord) -> None:
        if self._login_worker and self._login_worker.isRunning():
            return
        local = LocalConfig()
        service = (record.service or "").lower()
        if service == "steam":
            steam_path = local.steam_path
            if not steam_path:
                from ...widgets.dialogs import wgz_warn
                wgz_warn(self, DIALOG_ERROR_TITLE,
                         "Chưa tìm thấy Steam. Vui lòng thiết lập đường dẫn trong Cài Đặt.")
                return
            worker = SteamLoginWorker(
                username=record.username,
                password=record.password,
                steam_exe_path=steam_path,
                parent=self,
            )
            self._run_login(worker, service_name="STEAM")
        elif service == "riot":
            riot_path = local.riot_path
            if not riot_path:
                from ...core.auto_path import _find_riot_path
                riot_path = _find_riot_path()
                if riot_path:
                    local.riot_path = riot_path
                    local.save()
            if not riot_path:
                from ...widgets.dialogs import wgz_warn
                wgz_warn(self, DIALOG_ERROR_TITLE,
                         "Không tìm thấy Riot Client.\n"
                         "Vui lòng cài đặt hoặc thiết lập đường dẫn trong Cài Đặt.")
                return
            worker = RiotLoginWorker(
                username=record.username,
                password=record.password,
                riot_exe_path=riot_path,
                parent=self,
            )
            self._run_login(worker, service_name="RIOT")
        else:
            from ...widgets.dialogs import wgz_info
            wgz_info(self, "Đăng nhập",
                     f"Dịch vụ '{record.service}' chưa hỗ trợ đăng nhập tự động.")

    def _run_login(self, worker, service_name: str) -> None:
        """Start an auto-login worker and show the modal progress dialog."""
        worker.failed.connect(self._on_login_failed)
        worker.finished.connect(self._on_login_finished)
        worker.status.connect(
            lambda msg, sn=service_name: log.info("%s login: %s", sn, msg)
        )
        self._login_worker = worker
        self._login_dialog = LoginProgressDialog(
            worker, service_name=service_name, parent=self.window()
        )
        worker.start()
        self._login_dialog.exec()

    def _on_login_failed(self, msg: str) -> None:
        # The modal progress dialog displays the error in its log.
        log.warning("Auto-login failed: %s", msg)

    def _on_login_finished(self) -> None:
        self._login_worker = None
        self._login_dialog = None

    def _activate_app(self) -> None:
        try:
            win = self.window()
            if win:
                win.raise_()
                win.activateWindow()
        except Exception:
            pass
