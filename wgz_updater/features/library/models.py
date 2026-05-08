from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Iterable

from packaging import version as pkg_version

from ...core.config import Game
from ...core.paths import USER_DATA_DIR, ensure_user_dirs

log = logging.getLogger(__name__)

_INSTALL_REGISTRY = USER_DATA_DIR / "install_paths.json"


class InstallStatus(str, Enum):
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    UPDATE = "update"


def _load_registry() -> dict[str, dict]:
    if not _INSTALL_REGISTRY.exists():
        return {}
    try:
        return json.loads(_INSTALL_REGISTRY.read_text(encoding="utf-8"))
    except Exception:
        log.exception("Reading install registry")
        return {}


def _save_registry(data: dict[str, dict]) -> None:
    ensure_user_dirs()
    _INSTALL_REGISTRY.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class InstallRegistry:
    def __init__(self) -> None:
        self._data = _load_registry()

    def install_path(self, game_id: str) -> Path | None:
        entry = self._data.get(game_id)
        if entry and entry.get("path"):
            return Path(entry["path"])
        return None

    def installed_version(self, game_id: str) -> str | None:
        entry = self._data.get(game_id)
        return entry.get("version") if entry else None

    def record_install(self, game_id: str, path: Path, version: str) -> None:
        self._data[game_id] = {"path": str(path), "version": version}
        _save_registry(self._data)

    def clear(self, game_id: str) -> None:
        self._data.pop(game_id, None)
        _save_registry(self._data)

    def status_for(self, game: Game) -> InstallStatus:
        installed = self.installed_version(game.id)
        if not installed:
            return InstallStatus.NOT_INSTALLED
        try:
            if pkg_version.parse(game.version) > pkg_version.parse(installed):
                return InstallStatus.UPDATE
        except Exception:
            if game.version and installed and game.version != installed:
                return InstallStatus.UPDATE
        return InstallStatus.INSTALLED


def filter_games(games: Iterable[Game], query: str) -> list[Game]:
    q = query.strip().lower()
    if not q:
        return list(games)
    return [
        g for g in games
        if q in g.name.lower() or q in g.game.lower() or q in g.id.lower()
    ]
