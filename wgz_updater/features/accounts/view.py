from __future__ import annotations

import logging

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from ...core.config import load_config
from ...resources.strings_vi import (
    DIALOG_ERROR_TITLE, MSG_ACCOUNTS_LOADED,
    MSG_ACCOUNTS_SAVED, MSG_DRIVE_ERROR,
)
from ...widgets.dialogs import wgz_error, wgz_info
from .account_list_page import AccountListPage
from .models import AccountRecord
from .service_grid_page import ServiceGridPage

log = logging.getLogger(__name__)

_PAGE_GRID = 0
_PAGE_LIST = 1


class _DriveLoadWorker(QThread):
    finished_ok = pyqtSignal(dict)   # {service: [AccountRecord, ...]}
    failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            from .sheets_service import SheetsService
            svc = SheetsService()
            records = svc.fetch_accounts()
            grouped: dict[str, list[AccountRecord]] = {}
            for rec in records:
                grouped.setdefault(rec.service, []).append(rec)
            self.finished_ok.emit(grouped)
        except Exception as exc:
            log.exception("Drive load failed")
            self.failed.emit(str(exc))


class _DriveSaveWorker(QThread):
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, records: list[AccountRecord], parent=None) -> None:
        super().__init__(parent)
        self._records = records

    def run(self) -> None:
        try:
            from .sheets_service import SheetsService
            svc = SheetsService()
            svc.write_accounts(self._records)
            try:
                from .github_sync import GitHubSync
                GitHubSync().push(self._records)
            except Exception:
                log.warning("GitHub sync skipped (token missing or error)", exc_info=True)
            self.finished_ok.emit()
        except Exception as exc:
            log.exception("Drive save failed")
            self.failed.emit(str(exc))


class AccountsView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._accounts: dict[str, list[AccountRecord]] = {}
        self._current_service: str = ""
        self._load_worker: _DriveLoadWorker | None = None
        self._save_worker: _DriveSaveWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget(self)
        layout.addWidget(self._stack)

        self._grid_page = ServiceGridPage(self)
        self._list_page = AccountListPage(self)

        self._stack.addWidget(self._grid_page)  # _PAGE_GRID = 0
        self._stack.addWidget(self._list_page)  # _PAGE_LIST = 1

        self._grid_page.service_selected.connect(self._on_service_selected)
        self._list_page.back_requested.connect(self._on_back)
        self._list_page.save_requested.connect(self._on_save)
        self._list_page.load_requested.connect(self._on_load)

        self._grid_page.populate({})

        try:
            cfg = load_config(prefer_remote=False)
            self._game_names = [g.name for g in cfg.games]
        except Exception:
            self._game_names = []

    def _on_service_selected(self, service: str) -> None:
        self._current_service = service
        records = self._accounts.get(service, [])
        self._list_page.show_service(service, records, self._game_names)
        self._stack.setCurrentIndex(_PAGE_LIST)

    def _on_back(self) -> None:
        self._accounts[self._current_service] = self._list_page.get_records()
        self._grid_page.populate(self._accounts)
        self._stack.setCurrentIndex(_PAGE_GRID)

    def _on_load(self) -> None:
        if self._load_worker and self._load_worker.isRunning():
            return
        worker = _DriveLoadWorker(self)
        worker.finished_ok.connect(self._on_loaded)
        worker.failed.connect(
            lambda msg: wgz_error(self, DIALOG_ERROR_TITLE, MSG_DRIVE_ERROR.format(error=msg))
        )
        self._load_worker = worker
        worker.start()

    def _on_loaded(self, grouped: dict) -> None:
        self._accounts = grouped
        self._grid_page.populate(self._accounts)
        if self._stack.currentIndex() == _PAGE_LIST and self._current_service:
            records = self._accounts.get(self._current_service, [])
            self._list_page.set_records(records)
        wgz_info(self, "Drive", MSG_ACCOUNTS_LOADED)

    def _on_save(self) -> None:
        if self._save_worker and self._save_worker.isRunning():
            return
        self._accounts[self._current_service] = self._list_page.get_records()
        all_records = [r for recs in self._accounts.values() for r in recs]
        worker = _DriveSaveWorker(all_records, self)
        worker.finished_ok.connect(lambda: wgz_info(self, "Drive", MSG_ACCOUNTS_SAVED))
        worker.failed.connect(
            lambda msg: wgz_error(self, DIALOG_ERROR_TITLE, MSG_DRIVE_ERROR.format(error=msg))
        )
        self._save_worker = worker
        worker.start()
