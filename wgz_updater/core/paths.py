from __future__ import annotations

import os
import sys
from pathlib import Path


def _resolve_base() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


PACKAGE_ROOT = _resolve_base()
RESOURCES_DIR = PACKAGE_ROOT / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
QSS_DIR = RESOURCES_DIR / "qss"

INSTALL_ROOT = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "WGZ_Game_Launcher"
APP_DIR = INSTALL_ROOT / "GameUpdater"
LOG_DIR = INSTALL_ROOT / "logs"
USER_DATA_DIR = INSTALL_ROOT / "userdata"
VERSION_FILE = APP_DIR / "version.txt"

CONFIG_FILENAME = "CapNhatNightReignMod.json"
CONFIG_LOCAL = APP_DIR / CONFIG_FILENAME
CONFIG_BUNDLED = PACKAGE_ROOT / CONFIG_FILENAME

THEMES_FILENAME = "game_themes.json"
THEMES_LOCAL = APP_DIR / THEMES_FILENAME
THEMES_BUNDLED_CANDIDATES = (
    PACKAGE_ROOT / THEMES_FILENAME,
    PACKAGE_ROOT.parent / THEMES_FILENAME,
)

CREDENTIALS_FILE = APP_DIR / "credentials.json"
TOKEN_FILE = APP_DIR / "token.json"
GITHUB_TOKEN_FILE = APP_DIR / "github_token.txt"

GITHUB_JSON_URL = (
    "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/"
    "refs/heads/main/CapNhatNightReignMod.json"
)
GITHUB_THEMES_URL = (
    "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/"
    "refs/heads/main/game_themes.json"
)

MAIN_EXE_NAME = "GameUpdater.exe"
LAUNCHER_EXE_NAME = "Launcher.exe"
UPDATER_EXE_NAME = "updater.exe"
UNRAR_EXE = "UnRAR.exe"

SINGLETON_MUTEX_NAME = "WGZ_GameUpdater_Singleton"


def ensure_user_dirs() -> None:
    for d in (INSTALL_ROOT, APP_DIR, LOG_DIR, USER_DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)


def resource(*parts: str) -> Path:
    return RESOURCES_DIR.joinpath(*parts)


def icon(name: str) -> Path:
    return ICONS_DIR / name
