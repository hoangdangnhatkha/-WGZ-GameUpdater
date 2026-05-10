from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from ...core.config import AppConfig, Game
from ...core.local_config import LocalConfig
from ...resources.strings_vi import (
    ACTION_BACK, ACTION_BROWSE, ACTION_DOWNLOAD, ACTION_LAUNCH_GAME,
    ACTION_UPDATE, DIALOG_ERROR_TITLE,
)
from ...widgets.drop_zone import DropZone
from .image_loader import ImageLoader
from .models import InstallRegistry, InstallStatus

log = logging.getLogger(__name__)


class GameDetailPage(QWidget):
    download_requested = pyqtSignal(object, str, int)  # Game, install_path, url_index
    back_requested = pyqtSignal()

    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._local = LocalConfig()
        self._entries: list[Game] = []
        self._game: Game | None = None
        self._slideshow_urls: list[str] = []
        self._slide_idx = 0
        self._slide_timer = QTimer(self)
        self._slide_timer.setInterval(4000)
        self._slide_timer.timeout.connect(self._advance_slide)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        # Back button
        back_btn = QPushButton(ACTION_BACK, self)
        back_btn.setObjectName("BackButton")
        back_btn.clicked.connect(self.back_requested)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # Hero image
        self._hero = QLabel(self)
        self._hero.setFixedSize(460, 215)
        self._hero.setObjectName("HeroImage")
        self._hero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._hero, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Title
        self._title = QLabel(self)
        self._title.setStyleSheet("font-size:18px;font-weight:600;")
        layout.addWidget(self._title)

        # Mod/variant selector
        self._mod_combo = QComboBox(self)
        self._mod_combo.currentIndexChanged.connect(self._on_variant_changed)
        layout.addWidget(self._mod_combo)

        # Path guide
        self._guide = QPlainTextEdit(self)
        self._guide.setReadOnly(True)
        self._guide.setFixedHeight(80)
        self._guide.setPlaceholderText("Hướng dẫn cài đặt...")
        layout.addWidget(self._guide)

        # Install path row
        path_row = QHBoxLayout()
        self._path_edit = QLineEdit(self)
        self._path_edit.setPlaceholderText("Chọn thư mục cài đặt...")
        self._path_edit.textChanged.connect(self._update_launch_state)
        path_row.addWidget(self._path_edit, 1)
        browse_btn = QPushButton(ACTION_BROWSE, self)
        browse_btn.clicked.connect(self._on_browse)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        # DropZone
        drop = DropZone(parent=self)
        drop.folder_dropped.connect(self._path_edit.setText)
        layout.addWidget(drop)

        # Action buttons
        btn_row = QHBoxLayout()
        self._dl_btn = QPushButton(ACTION_DOWNLOAD, self)
        self._dl_btn.setObjectName("Accent")
        self._dl_btn.clicked.connect(self._on_download)
        btn_row.addWidget(self._dl_btn)
        self._launch_btn = QPushButton(ACTION_LAUNCH_GAME, self)
        self._launch_btn.setEnabled(False)
        self._launch_btn.clicked.connect(self._on_launch)
        btn_row.addWidget(self._launch_btn)
        layout.addLayout(btn_row)
        layout.addStretch(1)

    def show_game(
        self,
        entries: list[Game] | Game,
        config: AppConfig | None = None,
    ) -> None:
        if isinstance(entries, Game):
            entries = [entries]
        if not entries:
            return
        self._entries = entries
        self._slide_timer.stop()
        self._slideshow_urls = []
        self._slide_idx = 0
        self._hero.clear()
        self._hero.setText("...")

        canonical = entries[0].game or entries[0].name
        self._title.setText(canonical)

        # Hero image / slideshow — look up theme by canonical name
        if config:
            theme = config.themes.get(canonical)
            if theme is None:
                for e in entries:
                    theme = config.themes.get(e.game) or config.themes.get(e.name)
                    if theme:
                        break
            if theme:
                if theme.slideshow:
                    self._slideshow_urls = theme.slideshow
                    ImageLoader.instance().request(theme.slideshow[0], self._set_hero)
                    if len(theme.slideshow) > 1:
                        self._slide_timer.start()
                elif theme.image:
                    ImageLoader.instance().request(theme.image, self._set_hero)

        # Mod/variant combo: each entry is one option; if entry has multiple urls, expand to parts
        self._mod_combo.blockSignals(True)
        self._mod_combo.clear()
        for entry in entries:
            if entry.urls and len(entry.urls) > 1:
                for i in range(len(entry.urls)):
                    self._mod_combo.addItem(
                        f"{entry.name} — Phần {i + 1}", userData=(entry, i)
                    )
            else:
                self._mod_combo.addItem(entry.name, userData=(entry, 0))
        self._mod_combo.blockSignals(False)
        self._mod_combo.setCurrentIndex(0)
        self._apply_variant(0)

    def _on_variant_changed(self, index: int) -> None:
        if index >= 0:
            self._apply_variant(index)

    def _apply_variant(self, index: int) -> None:
        data = self._mod_combo.itemData(index)
        if not data:
            return
        entry, _url_idx = data
        self._game = entry
        self._guide.setPlainText(entry.path_guide or "")
        saved = self._local.get_game_path(entry.id) or self._local.last_used_folder or ""
        self._path_edit.setText(saved)
        self._update_dl_button()
        self._update_launch_state()

    def _advance_slide(self) -> None:
        if not self._slideshow_urls:
            return
        self._slide_idx = (self._slide_idx + 1) % len(self._slideshow_urls)
        ImageLoader.instance().request(self._slideshow_urls[self._slide_idx], self._set_hero)

    def _set_hero(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            460, 215,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._hero.setPixmap(scaled)

    def _update_dl_button(self) -> None:
        if not self._game:
            return
        status = self._registry.status_for(self._game)
        self._dl_btn.setText(
            ACTION_UPDATE if status == InstallStatus.UPDATE else ACTION_DOWNLOAD
        )

    def _update_launch_state(self) -> None:
        if not self._game:
            self._launch_btn.setEnabled(False)
            return
        path_str = self._path_edit.text().strip()
        launch_rel = (
            self._local.get_game_launcher(self._game.id) or self._game.launch_file
        )
        if path_str and launch_rel:
            launch_abs = Path(path_str) / launch_rel
            self._launch_btn.setEnabled(launch_abs.exists())
        else:
            self._launch_btn.setEnabled(False)

    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục cài đặt")
        if folder:
            self._path_edit.setText(folder)

    def _on_download(self) -> None:
        if not self._game:
            return
        path = self._path_edit.text().strip()
        if not path:
            from ...widgets.dialogs import wgz_warn
            wgz_warn(self, "Chọn đường dẫn", "Vui lòng chọn thư mục cài đặt trước.")
            return
        self._local.set_game_path(self._game.id, path)
        self._local.last_used_folder = path
        self._local.save()
        data = self._mod_combo.itemData(self._mod_combo.currentIndex())
        url_idx = data[1] if data else 0
        self.download_requested.emit(self._game, path, url_idx)

    def _on_launch(self) -> None:
        if not self._game:
            return
        path_str = self._path_edit.text().strip()
        launch_rel = (
            self._local.get_game_launcher(self._game.id) or self._game.launch_file
        )
        if not path_str or not launch_rel:
            return
        launch_abs = Path(path_str) / launch_rel
        if launch_abs.exists():
            try:
                subprocess.Popen([str(launch_abs)], cwd=str(launch_abs.parent))
            except Exception as exc:
                log.exception("Launch failed")
                from ...widgets.dialogs import wgz_error
                wgz_error(self, DIALOG_ERROR_TITLE, f"Không thể chạy game: {exc}")
