from __future__ import annotations

import logging

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from ...core.config import AppConfig, load_config
from ...resources.strings_vi import DIALOG_ERROR_TITLE
from ...widgets.loading_dialog import LoadingDialog
from .download_progress_page import DownloadProgressPage
from .game_detail_page import GameDetailPage
from .game_grid_page import GameGridPage
from .models import InstallRegistry

log = logging.getLogger(__name__)

_PAGE_GRID = 0
_PAGE_DETAIL = 1
_PAGE_PROGRESS = 2


class _RemoteConfigWorker(QThread):
    finished_ok = pyqtSignal(object)
    failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            cfg = load_config(prefer_remote=True)
            self.finished_ok.emit(cfg)
        except Exception as exc:
            log.exception("Library remote reload failed")
            self.failed.emit(str(exc))


class LibraryView(QWidget):
    worker_started = pyqtSignal(object)
    worker_message = pyqtSignal(str)
    worker_progress = pyqtSignal(int)
    worker_finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._registry = InstallRegistry()
        self._config: AppConfig | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget(self)
        layout.addWidget(self._stack)

        self._grid_page = GameGridPage(self._registry, self)
        self._detail_page = GameDetailPage(self._registry, self)
        self._progress_page = DownloadProgressPage(self._registry, self)

        self._stack.addWidget(self._grid_page)      # index 0
        self._stack.addWidget(self._detail_page)    # index 1
        self._stack.addWidget(self._progress_page)  # index 2

        # Signals
        self._grid_page.game_selected.connect(self._on_game_selected)
        self._grid_page.refresh_requested.connect(self._refresh_remote_blocking)

        self._detail_page.back_requested.connect(lambda: self._stack.setCurrentIndex(_PAGE_GRID))
        self._detail_page.download_requested.connect(self._on_download_requested)

        self._reload_worker: _RemoteConfigWorker | None = None
        self._loading_dlg: LoadingDialog | None = None

        self._progress_page.finished.connect(self._on_download_finished)
        self._progress_page.cancelled.connect(lambda: self._stack.setCurrentIndex(_PAGE_DETAIL))

        # Forward worker signals to StatusStrip
        self._progress_page.worker_started.connect(self.worker_started)
        self._progress_page.worker_message.connect(self.worker_message)
        self._progress_page.worker_progress.connect(self.worker_progress)
        self._progress_page.worker_finished.connect(self.worker_finished)

        self.reload(prefer_remote=False)

    def reload(self, *, prefer_remote: bool = True) -> None:
        try:
            self._config = load_config(prefer_remote=prefer_remote)
            self._grid_page.populate(self._config)
            log.info("Loaded %d games (remote=%s)", len(self._config.games), prefer_remote)
        except Exception as exc:
            log.exception("Reload failed")
            from ...widgets.dialogs import wgz_error
            wgz_error(self, DIALOG_ERROR_TITLE, str(exc))

    def _refresh_remote_blocking(self) -> None:
        if self._reload_worker is not None and self._reload_worker.isRunning():
            return
        worker = _RemoteConfigWorker(self)
        worker.finished_ok.connect(self._on_remote_loaded)
        worker.failed.connect(self._on_remote_failed)
        self._reload_worker = worker
        self._loading_dlg = LoadingDialog(self)
        worker.start()
        self._loading_dlg.exec()
        self._loading_dlg = None

    def _dismiss_loading(self) -> None:
        if self._loading_dlg is not None:
            self._loading_dlg.hide()
            self._loading_dlg.accept()

    def _on_remote_loaded(self, cfg) -> None:
        self._dismiss_loading()
        self._config = cfg
        self._grid_page.populate(self._config)
        log.info("Loaded %d games (remote=True)", len(self._config.games))

    def _on_remote_failed(self, msg: str) -> None:
        self._dismiss_loading()
        from ...widgets.dialogs import wgz_error
        wgz_error(self, DIALOG_ERROR_TITLE, msg)

    def _on_game_selected(self, game) -> None:
        self._detail_page.show_game(game, self._config)
        self._stack.setCurrentIndex(_PAGE_DETAIL)

    def _on_download_requested(self, game, install_path: str, url_idx: int) -> None:
        self._stack.setCurrentIndex(_PAGE_PROGRESS)
        image_url = ""
        if self._config:
            canonical = (game.game or game.name or "").strip()
            theme = self._config.themes.get(canonical)
            if theme:
                image_url = theme.slideshow[0] if theme.slideshow else theme.image
        self._progress_page.start(game, install_path, url_idx, image_url=image_url)

    def _on_download_finished(self, game, install_path: str) -> None:
        self._grid_page.refresh_cards()
        self._stack.setCurrentIndex(_PAGE_GRID)
