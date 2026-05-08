from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt
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

from ... import __version__
from ...core.paths import GITHUB_TOKEN_FILE, INSTALL_ROOT, LOG_DIR, ensure_user_dirs
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
        if GITHUB_TOKEN_FILE.exists():
            try:
                return GITHUB_TOKEN_FILE.read_text(encoding="utf-8").strip()
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

    def _check_update(self) -> None:
        from ...core.config import load_config
        try:
            cfg = load_config(prefer_remote=True)
            QMessageBox.information(
                self,
                "Phiên bản",
                f"Phiên bản mới nhất: {cfg.updater.latest_version}\n\n{cfg.updater.release_notes}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))
