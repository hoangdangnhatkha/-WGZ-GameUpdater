from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from .local_config import LocalConfig

log = logging.getLogger(__name__)


def _find_steam_registry() -> str | None:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Valve\Steam",
        )
        value, _ = winreg.QueryValueEx(key, "SteamExe")
        winreg.CloseKey(key)
        if Path(value).exists():
            return value
    except Exception:
        pass
    return None


def _find_riot_path() -> str | None:
    import os
    default = Path(
        os.environ.get("LOCALAPPDATA", ""),
        "Riot Games", "Riot Client", "RiotClientServices.exe",
    )
    if default.exists():
        return str(default)

    try:
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                key = winreg.OpenKey(hive, r"SOFTWARE\Riot Games\Riot Client")
                value, _ = winreg.QueryValueEx(key, "InstallLocation")
                winreg.CloseKey(key)
                candidate = Path(value) / "RiotClientServices.exe"
                if candidate.exists():
                    return str(candidate)
            except Exception:
                continue
    except Exception:
        pass
    return None


class AutoPathWorker(QThread):
    """Background worker that detects Steam and Riot paths via registry."""

    steam_found = pyqtSignal(str)
    riot_found = pyqtSignal(str)

    def run(self) -> None:
        local = LocalConfig()
        if not local.steam_path:
            path = _find_steam_registry()
            if path:
                log.info("Auto-detected Steam: %s", path)
                local.steam_path = path
                local.save()
                self.steam_found.emit(path)
        if not local.riot_path:
            path = _find_riot_path()
            if path:
                log.info("Auto-detected Riot: %s", path)
                local.riot_path = path
                local.save()
                self.riot_found.emit(path)
