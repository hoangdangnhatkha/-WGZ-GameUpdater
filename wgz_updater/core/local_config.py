from __future__ import annotations

import copy
import json
import logging
from pathlib import Path

from .paths import INSTALL_ROOT, ensure_user_dirs

log = logging.getLogger(__name__)

_SETTINGS_FILE = INSTALL_ROOT / "settings.json"
_DEFAULTS: dict = {
    "game_paths": {},
    "game_launchers": {},
    "installed_versions": {},
    "custom_games": {},
    "display_name_overrides": {},
    "theme_overrides": {},
    "steam_path": None,
    "riot_path": None,
    "last_used_folder": None,
}

_instance: "LocalConfig | None" = None


class LocalConfig:
    """Singleton wrapping %LOCALAPPDATA%/WGZ_Game_Launcher/settings.json."""

    def __new__(cls) -> "LocalConfig":
        global _instance
        if _instance is None:
            _instance = super().__new__(cls)
            _instance._data: dict = copy.deepcopy(_DEFAULTS)
        return _instance

    def load(self) -> None:
        if _SETTINGS_FILE.exists():
            try:
                on_disk = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
                for key, default in _DEFAULTS.items():
                    self._data[key] = on_disk.get(key, default)
            except Exception:
                log.exception("Failed to load settings.json")

    def save(self) -> None:
        ensure_user_dirs()
        try:
            _SETTINGS_FILE.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            log.exception("Failed to save settings.json")

    # ── Game paths ──
    def get_game_path(self, game_id: str) -> str | None:
        return self._data["game_paths"].get(game_id)

    def set_game_path(self, game_id: str, path: str) -> None:
        self._data["game_paths"][game_id] = path

    # ── Game launchers ──
    def get_game_launcher(self, game_id: str) -> str | None:
        return self._data["game_launchers"].get(game_id)

    def set_game_launcher(self, game_id: str, relative_path: str) -> None:
        self._data["game_launchers"][game_id] = relative_path

    # ── Properties ──
    @property
    def steam_path(self) -> str | None:
        return self._data.get("steam_path")

    @steam_path.setter
    def steam_path(self, v: str | None) -> None:
        self._data["steam_path"] = v

    @property
    def riot_path(self) -> str | None:
        return self._data.get("riot_path")

    @riot_path.setter
    def riot_path(self, v: str | None) -> None:
        self._data["riot_path"] = v

    @property
    def last_used_folder(self) -> str | None:
        return self._data.get("last_used_folder")

    @last_used_folder.setter
    def last_used_folder(self, v: str | None) -> None:
        self._data["last_used_folder"] = v
