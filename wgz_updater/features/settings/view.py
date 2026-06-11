from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...widgets.loading_dialog import run_blocking


class _CheckUpdateWorker(QThread):
    finished_ok = pyqtSignal(object)
    failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            from ...core.config import load_config
            cfg = load_config(prefer_remote=True)
            self.finished_ok.emit(cfg)
        except Exception as exc:
            log.exception("Check update failed")
            self.failed.emit(str(exc))

from ... import __version__
from ...core.local_config import LocalConfig
from ...core.paths import GITHUB_TOKEN_FILE, INSTALL_ROOT, LOG_DIR, ensure_user_dirs, find_github_token
from ...core.updater import get_local_version
from ...resources.strings_vi import (
    NAV_SETTINGS,
    SETTINGS_CHECK_UPDATE,
    SETTINGS_GITHUB_TOKEN,
    SETTINGS_INSTALL_PATH,
    SETTINGS_OPEN_LOG,
    SETTINGS_RESET_CACHE,
    SETTINGS_VERSION,
)

log = logging.getLogger(__name__)


class SettingsView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(16)

        title = QLabel(NAV_SETTINGS, self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        outer.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)

        path_row = QHBoxLayout()
        self._path_field = QLineEdit(str(INSTALL_ROOT), self)
        self._path_field.setReadOnly(True)
        path_row.addWidget(self._path_field, 1)
        open_btn = QPushButton("Mở", self)
        open_btn.clicked.connect(self._open_install)
        path_row.addWidget(open_btn)
        form.addRow(QLabel(SETTINGS_INSTALL_PATH, self), self._wrap(path_row))

        self._local = LocalConfig()

        riot_row = QHBoxLayout()
        self._riot_field = QLineEdit(self._local.riot_path or "", self)
        self._riot_field.setReadOnly(True)
        self._riot_field.setPlaceholderText("Chưa thiết lập")
        riot_row.addWidget(self._riot_field, 1)
        riot_browse = QPushButton("Chọn...", self)
        riot_browse.clicked.connect(self._browse_riot)
        riot_row.addWidget(riot_browse)
        riot_auto = QPushButton("Tự dò", self)
        riot_auto.clicked.connect(self._auto_detect_riot)
        riot_row.addWidget(riot_auto)
        form.addRow(QLabel("Riot Client", self), self._wrap(riot_row))

        steam_row = QHBoxLayout()
        self._steam_field = QLineEdit(self._local.steam_path or "", self)
        self._steam_field.setReadOnly(True)
        self._steam_field.setPlaceholderText("Chưa thiết lập")
        steam_row.addWidget(self._steam_field, 1)
        steam_browse = QPushButton("Chọn...", self)
        steam_browse.clicked.connect(self._browse_steam)
        steam_row.addWidget(steam_browse)
        steam_auto = QPushButton("Tự dò", self)
        steam_auto.clicked.connect(self._auto_detect_steam)
        steam_row.addWidget(steam_auto)
        form.addRow(QLabel("Steam", self), self._wrap(steam_row))

        self._token_field = QLineEdit(self)
        self._token_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._token_field.setText(self._read_token())
        token_row = QHBoxLayout()
        token_row.addWidget(self._token_field, 1)
        save_btn = QPushButton("Lưu", self)
        save_btn.clicked.connect(self._save_token)
        token_row.addWidget(save_btn)
        form.addRow(QLabel(SETTINGS_GITHUB_TOKEN, self), self._wrap(token_row))

        version_row = QHBoxLayout()
        local_v = get_local_version()
        v_label = QLabel(f"App: {__version__} • Cài đặt: {local_v}", self)
        version_row.addWidget(v_label, 1)
        check_btn = QPushButton(SETTINGS_CHECK_UPDATE, self)
        check_btn.clicked.connect(self._check_update)
        version_row.addWidget(check_btn)
        form.addRow(QLabel(SETTINGS_VERSION, self), self._wrap(version_row))

        outer.addLayout(form)

        actions = QHBoxLayout()
        log_btn = QPushButton(SETTINGS_OPEN_LOG, self)
        log_btn.clicked.connect(self._open_logs)
        actions.addWidget(log_btn)

        cache_btn = QPushButton(SETTINGS_RESET_CACHE, self)
        cache_btn.clicked.connect(self._reset_cache)
        actions.addWidget(cache_btn)
        actions.addStretch(1)
        outer.addLayout(actions)

        outer.addStretch(1)

    def _wrap(self, layout) -> QWidget:
        w = QWidget(self)
        w.setLayout(layout)
        return w

    def _read_token(self) -> str:
        path = find_github_token()
        if path is not None:
            try:
                return path.read_text(encoding="utf-8").strip()
            except Exception:
                log.exception("Reading github token")
        return ""

    def _save_token(self) -> None:
        ensure_user_dirs()
        try:
            GITHUB_TOKEN_FILE.write_text(self._token_field.text().strip(), encoding="utf-8")
            QMessageBox.information(self, "Đã lưu", "Đã lưu GitHub token.")
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))

    def _open_install(self) -> None:
        ensure_user_dirs()
        os.startfile(str(INSTALL_ROOT))

    def _open_logs(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(LOG_DIR))

    def _reset_cache(self) -> None:
        from ...core.paths import CONFIG_LOCAL
        if CONFIG_LOCAL.exists():
            try:
                CONFIG_LOCAL.unlink()
                QMessageBox.information(self, "Đã xóa", "Đã xóa cache cấu hình.")
            except Exception as exc:
                QMessageBox.critical(self, "Lỗi", str(exc))

    def _browse_riot(self) -> None:
        start_dir = self._local.riot_path or self._local.last_used_folder or ""
        if start_dir and Path(start_dir).is_file():
            start_dir = str(Path(start_dir).parent)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn RiotClientServices.exe",
            start_dir,
            "Riot Client (RiotClientServices.exe);;Tệp thực thi (*.exe)",
        )
        if not path:
            return
        self._local.riot_path = path
        self._local.last_used_folder = str(Path(path).parent)
        self._local.save()
        self._riot_field.setText(path)

    def _browse_steam(self) -> None:
        start_dir = self._local.steam_path or self._local.last_used_folder or ""
        if start_dir and Path(start_dir).is_file():
            start_dir = str(Path(start_dir).parent)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn steam.exe",
            start_dir,
            "Steam (steam.exe);;Tệp thực thi (*.exe)",
        )
        if not path:
            return
        self._local.steam_path = path
        self._local.last_used_folder = str(Path(path).parent)
        self._local.save()
        self._steam_field.setText(path)

    def _auto_detect_riot(self) -> None:
        from ...core.auto_path import _find_riot_path
        path = _find_riot_path()
        if not path:
            QMessageBox.warning(self, "Không tìm thấy", "Không tự dò được Riot Client.")
            return
        self._local.riot_path = path
        self._local.save()
        self._riot_field.setText(path)

    def _auto_detect_steam(self) -> None:
        from ...core.auto_path import _find_steam_registry
        path = _find_steam_registry()
        if not path:
            QMessageBox.warning(self, "Không tìm thấy", "Không tự dò được Steam.")
            return
        self._local.steam_path = path
        self._local.save()
        self._steam_field.setText(path)

    def _check_update(self) -> None:
        worker = _CheckUpdateWorker(self)
        run_blocking(
            self,
            worker,
            message="Đang tải dữ liệu...",
            slots={
                "finished_ok": self._on_check_update_ok,
                "failed": self._on_check_update_failed,
            },
        )

    def _on_check_update_ok(self, cfg) -> None:
        QMessageBox.information(
            self,
            "Phiên bản",
            f"Phiên bản mới nhất: {cfg.updater.latest_version}\n\n{cfg.updater.release_notes}",
        )

    def _on_check_update_failed(self, msg: str) -> None:
        QMessageBox.critical(self, "Lỗi", msg)
