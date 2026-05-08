from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from PyQt6.QtCore import QSortFilterProxyModel, Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ...core.config import Game, load_config
from ...core.win32_utils import prevent_sleep
from ...resources.strings_vi import (
    ACTION_REFRESH,
    APP_TITLE,
    DIALOG_ERROR_TITLE,
    NAV_LIBRARY,
)
from .download_worker import DownloadWorker
from .extract_worker import ExtractWorker
from .game_detail_panel import GameDetailPanel
from .game_table_model import COL_ACTION, GameTableModel
from .models import InstallRegistry, InstallStatus

log = logging.getLogger(__name__)


class LibraryView(QWidget):
    worker_started = pyqtSignal(object)  # the active worker (DownloadWorker or ExtractWorker)
    worker_message = pyqtSignal(str)
    worker_progress = pyqtSignal(int)
    worker_finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._registry = InstallRegistry()
        self._sleep_ctx = None
        self._download_worker: DownloadWorker | None = None
        self._extract_worker: ExtractWorker | None = None
        self._pending_game: Game | None = None
        self._pending_path: Path | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel(NAV_LIBRARY, self)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        header_row.addWidget(title)
        header_row.addStretch(1)

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Tìm kiếm...")
        self._search.setClearButtonEnabled(True)
        self._search.setFixedWidth(260)
        header_row.addWidget(self._search)

        self._refresh_btn = QPushButton(ACTION_REFRESH, self)
        self._refresh_btn.clicked.connect(lambda: self.reload(prefer_remote=True))
        header_row.addWidget(self._refresh_btn)

        outer.addLayout(header_row)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        outer.addWidget(splitter, 1)

        self._table_model = GameTableModel(self._registry, self)
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._table_model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)
        self._search.textChanged.connect(self._proxy.setFilterFixedString)

        self._table = QTableView(self)
        self._table.setModel(self._proxy)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        hh = self._table.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setDefaultSectionSize(40)
        self._table.setColumnWidth(COL_ACTION, 110)
        self._table.selectionModel().selectionChanged.connect(self._on_selection)
        self._table.doubleClicked.connect(self._on_double_click)
        splitter.addWidget(self._table)

        self._detail = GameDetailPanel(self._registry, self)
        self._detail.download_requested.connect(self._on_download_requested)
        self._detail.launch_requested.connect(self._on_launch_requested)
        splitter.addWidget(self._detail)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.reload(prefer_remote=False)

    def reload(self, *, prefer_remote: bool = True) -> None:
        try:
            cfg = load_config(prefer_remote=prefer_remote)
            self._table_model.set_games(cfg.games)
            log.info("Loaded %d games (remote=%s)", len(cfg.games), prefer_remote)
        except Exception as exc:
            log.exception("Reload failed")
            QMessageBox.warning(self, DIALOG_ERROR_TITLE, str(exc))

    def _selected_game(self) -> Game | None:
        sel = self._table.selectionModel().selectedRows()
        if not sel:
            return None
        proxy_idx = sel[0]
        src_idx = self._proxy.mapToSource(proxy_idx)
        return self._table_model.game_at(src_idx.row())

    def _on_selection(self, *_args) -> None:
        self._detail.show_game(self._selected_game())

    def _on_double_click(self, _idx) -> None:
        game = self._selected_game()
        if game:
            self._detail.show_game(game)

    def _on_download_requested(self, game: Game, install_path: str) -> None:
        if self._download_worker is not None or self._extract_worker is not None:
            QMessageBox.information(self, APP_TITLE, "Đang có một tác vụ đang chạy.")
            return
        url = game.primary_url
        if not url:
            QMessageBox.warning(self, DIALOG_ERROR_TITLE, "Game chưa có link tải.")
            return

        self._pending_game = game
        self._pending_path = Path(install_path)

        archive_name = f"{game.id}_{game.name}.{game.type}".replace(" ", "_")
        cache_dir = Path(tempfile.gettempdir()) / "wgz_downloads"
        cache_dir.mkdir(parents=True, exist_ok=True)

        self._sleep_ctx = prevent_sleep()
        self._sleep_ctx.__enter__()

        worker = DownloadWorker(url, cache_dir, archive_name, parent=self)
        worker.progress.connect(self.worker_progress)
        worker.status.connect(self.worker_message)
        worker.speed.connect(lambda s: self.worker_message.emit(s))
        worker.failed.connect(self._on_failed)
        worker.finished_ok.connect(self._on_download_done)
        worker.finished.connect(lambda: self._cleanup_worker("download"))
        self._download_worker = worker
        self.worker_started.emit(worker)
        self.worker_message.emit(f"Đang tải: {game.name}")
        worker.start()

    def _on_download_done(self, archive_path: str) -> None:
        game = self._pending_game
        target = self._pending_path
        if not game or not target:
            return
        worker = ExtractWorker(
            archive_path=Path(archive_path),
            target_dir=target,
            archive_type=game.type,
            password=game.password,
            delete_before=game.delete_before_extract,
            parent=self,
        )
        worker.progress.connect(self.worker_progress)
        worker.status.connect(self.worker_message)
        worker.failed.connect(self._on_failed)
        worker.finished_ok.connect(self._on_extract_done)
        worker.finished.connect(lambda: self._cleanup_worker("extract"))
        self._extract_worker = worker
        self.worker_started.emit(worker)
        worker.start()

    def _on_extract_done(self, _final_dir: str) -> None:
        if self._pending_game and self._pending_path:
            self._registry.record_install(
                self._pending_game.id,
                self._pending_path,
                self._pending_game.version,
            )
            self._refresh_visible_row(self._pending_game.id)
            self._detail.show_game(self._pending_game)
        self.worker_message.emit("Hoàn tất.")
        self.worker_finished.emit()

    def _on_failed(self, message: str) -> None:
        log.error("Worker failed: %s", message)
        QMessageBox.critical(self, DIALOG_ERROR_TITLE, message)
        self.worker_finished.emit()

    def _cleanup_worker(self, kind: str) -> None:
        if kind == "download":
            self._download_worker = None
        elif kind == "extract":
            self._extract_worker = None
        if self._download_worker is None and self._extract_worker is None:
            if self._sleep_ctx is not None:
                try:
                    self._sleep_ctx.__exit__(None, None, None)
                except Exception:
                    pass
                self._sleep_ctx = None

    def _refresh_visible_row(self, game_id: str) -> None:
        for row in range(self._table_model.rowCount()):
            g = self._table_model.game_at(row)
            if g and g.id == game_id:
                self._table_model.refresh_row(row)
                break

    def _on_launch_requested(self, _game: Game) -> None:
        return
