from __future__ import annotations

import logging

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from ...core.config import AppConfig, GameTheme, load_config
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


def _record_to_dict(rec: AccountRecord, game: str) -> dict:
    return {
        "nickname": rec.nickname or rec.username,
        "username": rec.username,
        "password": rec.password,
        "type": rec.service.lower(),
        "game": game,
    }


def _dict_to_record(d: dict, game_fallback: str = "") -> AccountRecord:
    service = (d.get("type") or "").strip()
    if service:
        # Capitalize: steam → Steam, riot → Riot
        service = service[:1].upper() + service[1:].lower()
    return AccountRecord(
        service=service or "Khác",
        username=d.get("username", ""),
        password=d.get("password", ""),
        nickname=d.get("nickname", ""),
        game=d.get("game", "") or game_fallback,
    )


class _DriveLoadWorker(QThread):
    finished_ok = pyqtSignal(dict)   # {game_name: [AccountRecord, ...]}
    failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            from .drive_accounts import DriveAccountsService
            svc = DriveAccountsService()
            raw = svc.fetch()
            grouped: dict[str, list[AccountRecord]] = {}
            for game_name, accounts in raw.items():
                if not isinstance(accounts, list):
                    continue
                grouped[game_name] = [
                    _dict_to_record(a, game_name) for a in accounts if isinstance(a, dict)
                ]
            self.finished_ok.emit(grouped)
        except Exception as exc:
            log.exception("Drive load failed")
            self.failed.emit(str(exc))


class _DriveSaveWorker(QThread):
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(
        self,
        accounts_by_game: dict[str, list[AccountRecord]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._data = accounts_by_game

    def run(self) -> None:
        try:
            from .drive_accounts import DriveAccountsService
            payload: dict[str, list[dict]] = {}
            for game, recs in self._data.items():
                if not recs:
                    continue
                payload[game] = [_record_to_dict(r, game) for r in recs]
            DriveAccountsService().push(payload)
            self.finished_ok.emit()
        except Exception as exc:
            log.exception("Drive save failed")
            self.failed.emit(str(exc))


class AccountsView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._accounts: dict[str, list[AccountRecord]] = {}
        self._themes: dict[str, GameTheme] = {}
        self._game_names: list[str] = []
        self._current_game: str = ""
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

        self._grid_page.service_selected.connect(self._on_game_selected)
        self._list_page.back_requested.connect(self._on_back)
        self._list_page.save_requested.connect(self._on_save)
        self._list_page.load_requested.connect(self._on_load)

        # Pre-populate from cached config (no remote fetch on init)
        try:
            cfg = load_config(prefer_remote=False)
            self._absorb_config(cfg)
        except Exception:
            log.exception("Failed loading cached config for accounts")

        self._grid_page.populate(self._accounts, self._themes)

    def _absorb_config(self, cfg: AppConfig) -> None:
        self._themes = dict(cfg.themes)
        names_from_themes = list(cfg.themes.keys())
        names_from_games = sorted({g.game for g in cfg.games if g.game})
        # Prefer theme order, then add any extra games
        seen = set()
        ordered: list[str] = []
        for n in names_from_themes + names_from_games:
            if n and n not in seen:
                seen.add(n)
                ordered.append(n)
        self._game_names = ordered

    def _on_game_selected(self, game_name: str) -> None:
        self._current_game = game_name
        records = self._accounts.get(game_name, [])
        self._list_page.show_service(game_name, records, self._game_names)
        self._stack.setCurrentIndex(_PAGE_LIST)

    def _on_back(self) -> None:
        self._accounts[self._current_game] = self._list_page.get_records()
        if not self._accounts[self._current_game]:
            self._accounts.pop(self._current_game, None)
        self._grid_page.populate(self._accounts, self._themes)
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
        self._accounts = {k: list(v) for k, v in grouped.items()}
        # Refresh themes too in case user wants newest
        try:
            cfg = load_config(prefer_remote=True)
            self._absorb_config(cfg)
        except Exception:
            log.warning("Theme refresh failed", exc_info=True)
        self._grid_page.populate(self._accounts, self._themes)
        if self._stack.currentIndex() == _PAGE_LIST and self._current_game:
            records = self._accounts.get(self._current_game, [])
            self._list_page.set_records(records)
        wgz_info(self, "Drive", MSG_ACCOUNTS_LOADED)

    def _on_save(self) -> None:
        if self._save_worker and self._save_worker.isRunning():
            return
        self._accounts[self._current_game] = self._list_page.get_records()
        if not self._accounts[self._current_game]:
            self._accounts.pop(self._current_game, None)
        worker = _DriveSaveWorker(dict(self._accounts), self)
        worker.finished_ok.connect(lambda: wgz_info(self, "Drive", MSG_ACCOUNTS_SAVED))
        worker.failed.connect(
            lambda msg: wgz_error(self, DIALOG_ERROR_TITLE, MSG_DRIVE_ERROR.format(error=msg))
        )
        self._save_worker = worker
        worker.start()
