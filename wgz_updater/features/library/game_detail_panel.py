from __future__ import annotations

import os
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.config import Game
from ...resources.strings_vi import (
    ACTION_BROWSE,
    ACTION_DOWNLOAD,
    ACTION_LAUNCH,
    ACTION_UPDATE,
)
from ...widgets.drop_zone import DropZone
from ...widgets.pill_label import PillLabel
from .models import InstallRegistry, InstallStatus


class GameDetailPanel(QWidget):
    download_requested = pyqtSignal(Game, str)  # game, install_path
    launch_requested = pyqtSignal(Game)

    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._game: Game | None = None
        self._install_path: Path | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self._title = QLabel(self)
        self._title.setStyleSheet("font-size: 22px; font-weight: 600;")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        meta_row = QHBoxLayout()
        self._game_label = QLabel(self)
        self._game_label.setStyleSheet("color: #b8b8b8;")
        meta_row.addWidget(self._game_label)
        meta_row.addStretch(1)
        self._pill = PillLabel(InstallStatus.NOT_INSTALLED, self)
        meta_row.addWidget(self._pill)
        layout.addLayout(meta_row)

        self._version = QLabel(self)
        self._version.setStyleSheet("color: #b8b8b8;")
        layout.addWidget(self._version)

        self._guide = QLabel(self)
        self._guide.setWordWrap(True)
        self._guide.setStyleSheet("color: #d8d8d8; padding-top: 8px;")
        layout.addWidget(self._guide)

        path_row = QHBoxLayout()
        self._path_label = QLabel("Đường dẫn cài đặt: (chưa chọn)", self)
        self._path_label.setStyleSheet("color: #b8b8b8;")
        self._path_label.setWordWrap(True)
        path_row.addWidget(self._path_label, 1)
        self._browse_btn = QPushButton(ACTION_BROWSE, self)
        self._browse_btn.clicked.connect(self._on_browse)
        path_row.addWidget(self._browse_btn)
        layout.addLayout(path_row)

        self._drop = DropZone("Hoặc kéo thư mục vào đây", self)
        self._drop.folder_dropped.connect(self._set_install_path)
        layout.addWidget(self._drop)

        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: rgba(255,255,255,0.06);")
        layout.addWidget(sep)

        actions = QHBoxLayout()
        self._action_btn = QPushButton(ACTION_DOWNLOAD, self)
        self._action_btn.setObjectName("Accent")
        self._action_btn.clicked.connect(self._on_action)
        self._launch_btn = QPushButton(ACTION_LAUNCH, self)
        self._launch_btn.clicked.connect(self._on_launch)
        actions.addWidget(self._action_btn)
        actions.addWidget(self._launch_btn)
        actions.addStretch(1)
        layout.addLayout(actions)

        layout.addStretch(1)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._clear()

    def _clear(self) -> None:
        self._game = None
        self._title.setText("Chọn một mục từ danh sách")
        self._game_label.setText("")
        self._version.setText("")
        self._guide.setText("")
        self._path_label.setText("Đường dẫn cài đặt: (chưa chọn)")
        self._action_btn.setEnabled(False)
        self._launch_btn.setEnabled(False)

    def show_game(self, game: Game | None) -> None:
        if game is None:
            self._clear()
            return
        self._game = game
        self._install_path = self._registry.install_path(game.id)
        self._title.setText(game.name)
        self._game_label.setText(game.game or "")
        self._version.setText(f"Phiên bản: {game.version}")
        self._guide.setText(game.path_guide or "")
        self._refresh_path_label()

        status = self._registry.status_for(game)
        self._pill.set_status(status)
        self._action_btn.setEnabled(True)
        self._action_btn.setText(ACTION_UPDATE if status == InstallStatus.UPDATE else ACTION_DOWNLOAD)
        self._launch_btn.setEnabled(
            status != InstallStatus.NOT_INSTALLED and bool(game.launch_file)
        )

    def _refresh_path_label(self) -> None:
        if self._install_path:
            self._path_label.setText(f"Đường dẫn cài đặt: {self._install_path}")
        else:
            self._path_label.setText("Đường dẫn cài đặt: (chưa chọn)")

    def _set_install_path(self, path: str) -> None:
        self._install_path = Path(path)
        self._refresh_path_label()

    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục cài đặt")
        if path:
            self._set_install_path(path)

    def _on_action(self) -> None:
        if not self._game:
            return
        if not self._install_path:
            self._on_browse()
            if not self._install_path:
                return
        self.download_requested.emit(self._game, str(self._install_path))

    def _on_launch(self) -> None:
        if not self._game or not self._install_path:
            return
        self.launch_requested.emit(self._game)
        if self._game.launch_file:
            target = self._install_path / self._game.launch_file
            if target.exists():
                try:
                    os.startfile(str(target))  # noqa: A001 — Windows-specific
                except Exception:
                    subprocess.Popen([str(target)])
