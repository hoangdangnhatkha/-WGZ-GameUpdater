"""AccountsView — Asset Vault console.

Single-page master-detail layout for the "Share Acc Game" tab.

Top:    Page title + KPI strip + toolbar (LOAD / PUSH).
Body:   Left rail of theaters (TheaterRail) · Right asset panel (AssetPanel).
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSplitter, QVBoxLayout, QWidget,
)

from ...core.config import AppConfig, GameTheme, load_config
from ...resources.strings_vi import (
    ACTION_LOAD_DRIVE, ACTION_SAVE_DRIVE, DIALOG_ERROR_TITLE,
    MSG_ACCOUNTS_LOADED, MSG_ACCOUNTS_SAVED, MSG_DRIVE_ERROR,
    NAV_ACCOUNTS,
)
from ...widgets.dialogs import wgz_error, wgz_info
from .asset_panel import AssetPanel
from .models import AccountRecord
from .theater_rail import TheaterRail

log = logging.getLogger(__name__)


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
        service = service[:1].upper() + service[1:].lower()
    return AccountRecord(
        service=service or "Khác",
        username=d.get("username", ""),
        password=d.get("password", ""),
        nickname=d.get("nickname", ""),
        game=d.get("game", "") or game_fallback,
    )


# ── Workers ──

class _DriveLoadWorker(QThread):
    finished_ok = pyqtSignal(dict)
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

    def __init__(self, accounts_by_game: dict[str, list[AccountRecord]], parent=None) -> None:
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


# ── Sync status indicator ──

class _SyncDot(QLabel):
    """Small status dot — IDLE / SYNC / OK / ERR."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SyncDot")
        self.setFixedSize(10, 10)
        self.set_state("idle")

    def set_state(self, state: str) -> None:
        # state: idle, sync, ok, err
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)


class _Kpi(QFrame):
    """One stat tile in the KPI strip."""

    def __init__(self, label: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("KpiTile")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)
        self._label = QLabel(label.upper(), self)
        self._label.setObjectName("KpiLabel")
        lay.addWidget(self._label)
        self._value = QLabel("0", self)
        self._value.setObjectName("KpiValue")
        lay.addWidget(self._value)

    def set_value(self, value: str) -> None:
        self._value.setText(value)


class AccountsView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AccountsVault")
        self._accounts: dict[str, list[AccountRecord]] = {}
        self._themes: dict[str, GameTheme] = {}
        self._game_names: list[str] = []
        self._load_worker: _DriveLoadWorker | None = None
        self._save_worker: _DriveSaveWorker | None = None
        self._load_in_progress = False
        self._save_in_progress = False
        self._dirty = False
        self._auto_load_done = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 18, 28, 16)
        outer.setSpacing(0)

        # ── Title row ──
        title = QLabel(NAV_ACCOUNTS.upper(), self)
        title.setObjectName("PageTitle")
        outer.addWidget(title)

        sub = QLabel("// SHARED INTELLIGENCE LIBRARY · ENCRYPTED VAULT", self)
        sub.setObjectName("PageSub")
        outer.addWidget(sub)
        outer.addSpacing(16)

        # ── KPI + toolbar row ──
        bar = QHBoxLayout()
        bar.setSpacing(8)
        bar.setContentsMargins(0, 0, 0, 0)

        self._kpi_theaters = _Kpi("THEATERS", self)
        self._kpi_assets = _Kpi("ASSETS", self)
        self._kpi_services = _Kpi("SERVICES", self)
        bar.addWidget(self._kpi_theaters)
        bar.addWidget(self._kpi_assets)
        bar.addWidget(self._kpi_services)

        # Sync status tile
        sync_tile = QFrame(self)
        sync_tile.setObjectName("KpiTile")
        sync_lay = QVBoxLayout(sync_tile)
        sync_lay.setContentsMargins(14, 10, 14, 10)
        sync_lay.setSpacing(2)
        sync_label = QLabel("SYNC", sync_tile)
        sync_label.setObjectName("KpiLabel")
        sync_lay.addWidget(sync_label)
        sync_row = QHBoxLayout()
        sync_row.setSpacing(8)
        sync_row.setContentsMargins(0, 0, 0, 0)
        self._sync_dot = _SyncDot(sync_tile)
        sync_row.addWidget(self._sync_dot)
        self._sync_text = QLabel("IDLE", sync_tile)
        self._sync_text.setObjectName("KpiValueSmall")
        sync_row.addWidget(self._sync_text)
        sync_row.addStretch(1)
        sync_lay.addLayout(sync_row)
        bar.addWidget(sync_tile)

        bar.addStretch(1)

        self._load_btn = QPushButton(f"▼  {ACTION_LOAD_DRIVE.upper()}", self)
        self._load_btn.setObjectName("VaultToolBtn")
        self._load_btn.clicked.connect(lambda: self._on_load(show_notification=True))
        bar.addWidget(self._load_btn)

        self._save_btn = QPushButton(f"▲  {ACTION_SAVE_DRIVE.upper()}", self)
        self._save_btn.setObjectName("VaultPrimaryBtn")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._on_save)
        bar.addWidget(self._save_btn)

        outer.addLayout(bar)
        outer.addSpacing(12)

        # ── Divider ──
        rule = QFrame(self)
        rule.setObjectName("SectionRule")
        rule.setFixedHeight(1)
        rule.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        outer.addWidget(rule)
        outer.addSpacing(12)

        # ── Master-detail body ──
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.setObjectName("VaultSplit")
        self._splitter.setHandleWidth(1)
        self._splitter.setChildrenCollapsible(False)

        self._rail = TheaterRail(self)
        self._panel = AssetPanel(self)

        # Wrap the rail so we can give it a frame
        rail_wrap = QFrame(self)
        rail_wrap.setObjectName("RailFrame")
        rail_lay = QVBoxLayout(rail_wrap)
        rail_lay.setContentsMargins(0, 0, 0, 0)
        rail_lay.setSpacing(0)
        rail_lay.addWidget(self._rail)

        panel_wrap = QFrame(self)
        panel_wrap.setObjectName("PanelFrame")
        panel_lay = QVBoxLayout(panel_wrap)
        panel_lay.setContentsMargins(0, 0, 0, 0)
        panel_lay.setSpacing(0)
        panel_lay.addWidget(self._panel)

        self._splitter.addWidget(rail_wrap)
        self._splitter.addWidget(panel_wrap)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([280, 720])
        outer.addWidget(self._splitter, 1)

        # Wire signals
        self._rail.selected.connect(self._on_theater_selected)
        self._panel.records_changed.connect(self._on_records_changed)

        # Pre-populate from cached config
        try:
            cfg = load_config(prefer_remote=False)
            self._absorb_config(cfg)
        except Exception:
            log.exception("Failed loading cached config for accounts")

        self._refresh_kpis()
        self._rail.populate(self._accounts, self._themes)
        self._panel.set_game_names(self._game_names)

        # Auto-load silently from Drive on startup
        QTimer.singleShot(120, self._auto_load)

    # ── Config / data ──

    def _absorb_config(self, cfg: AppConfig) -> None:
        self._themes = dict(cfg.themes)
        names_from_themes = list(cfg.themes.keys())
        names_from_games = sorted({g.game for g in cfg.games if g.game})
        seen, ordered = set(), []
        for n in names_from_themes + names_from_games:
            if n and n not in seen:
                seen.add(n)
                ordered.append(n)
        self._game_names = ordered

    def _refresh_kpis(self) -> None:
        non_empty = [g for g, recs in self._accounts.items() if recs]
        total_assets = sum(len(r) for r in self._accounts.values())
        services = set()
        for recs in self._accounts.values():
            for r in recs:
                if r.service:
                    services.add(r.service.lower())
        self._kpi_theaters.set_value(f"{len(non_empty):02d}")
        self._kpi_assets.set_value(f"{total_assets:02d}")
        self._kpi_services.set_value(f"{len(services):02d}")

    def _set_dirty(self, dirty: bool) -> None:
        self._dirty = dirty
        self._save_btn.setEnabled(dirty and not self._save_in_progress)
        if dirty:
            self._sync_dot.set_state("err")  # repurposed: amber-style "unsaved"
            self._sync_text.setText("DIRTY")
        else:
            self._sync_dot.set_state("ok")
            self._sync_text.setText("READY")

    # ── Theater selection ──

    def _on_theater_selected(self, game: str) -> None:
        records = self._accounts.get(game, [])
        self._panel.show_theater(game, records)

    def _on_records_changed(self, game: str, records: list) -> None:
        if not game:
            return
        if records:
            self._accounts[game] = list(records)
        else:
            self._accounts.pop(game, None)
        self._refresh_kpis()
        # Refresh just the touched rail entry (cheap)
        services = sorted({r.service for r in records if r.service})
        self._rail.update_entry(game, len(records), services)
        self._set_dirty(True)

    # ── Drive load ──

    def _auto_load(self) -> None:
        if not self._auto_load_done and not self._load_in_progress:
            self._auto_load_done = True
            self._on_load(show_notification=False)

    def _on_load(self, show_notification: bool = True) -> None:
        if self._load_in_progress:
            return
        self._load_in_progress = True
        self._load_btn.setEnabled(False)
        self._sync_dot.set_state("sync")
        self._sync_text.setText("PULLING…")
        worker = _DriveLoadWorker(self)
        worker.finished_ok.connect(lambda grouped: self._on_loaded(grouped, show_notification))
        worker.failed.connect(self._on_load_failed)
        self._load_worker = worker
        worker.start()

    def _on_load_failed(self, msg: str) -> None:
        self._load_in_progress = False
        self._load_btn.setEnabled(True)
        self._sync_dot.set_state("err")
        self._sync_text.setText("ERROR")
        wgz_error(self, DIALOG_ERROR_TITLE, MSG_DRIVE_ERROR.format(error=msg))

    def _on_loaded(self, grouped: dict, show_notification: bool = True) -> None:
        self._load_in_progress = False
        self._load_btn.setEnabled(True)
        self._accounts = {k: list(v) for k, v in grouped.items()}
        # Refresh themes too (best-effort, may be remote)
        try:
            cfg = load_config(prefer_remote=True)
            self._absorb_config(cfg)
            self._panel.set_game_names(self._game_names)
        except Exception:
            log.warning("Theme refresh failed", exc_info=True)
        self._refresh_kpis()
        self._rail.populate(self._accounts, self._themes)
        # If a theater was active, re-show its (possibly updated) records
        active = self._rail.active_game
        if active:
            self._panel.show_theater(active, self._accounts.get(active, []))
        self._set_dirty(False)
        if show_notification:
            wgz_info(self, "Drive", MSG_ACCOUNTS_LOADED)

    # ── Drive save ──

    def _on_save(self) -> None:
        if self._save_in_progress:
            return
        self._save_in_progress = True
        self._save_btn.setEnabled(False)
        self._sync_dot.set_state("sync")
        self._sync_text.setText("PUSHING…")
        worker = _DriveSaveWorker(dict(self._accounts), self)
        worker.finished_ok.connect(self._on_save_done)
        worker.failed.connect(self._on_save_failed)
        self._save_worker = worker
        worker.start()

    def _on_save_done(self) -> None:
        self._save_in_progress = False
        self._set_dirty(False)
        wgz_info(self, "Drive", MSG_ACCOUNTS_SAVED)

    def _on_save_failed(self, msg: str) -> None:
        self._save_in_progress = False
        self._save_btn.setEnabled(True)
        self._sync_dot.set_state("err")
        self._sync_text.setText("ERROR")
        wgz_error(self, DIALOG_ERROR_TITLE, MSG_DRIVE_ERROR.format(error=msg))
