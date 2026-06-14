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
USER_TOKEN_FILE = APP_DIR / "user_token.json"
GITHUB_TOKEN_FILE = APP_DIR / "github_token.txt"

GITHUB_JSON_URL = (
    "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/"
    "refs/heads/main/CapNhatNightReignMod.json"
)
GITHUB_THEMES_URL = (
    "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/"
    "refs/heads/main/game_themes.json"
)

# REST API backend (overrides GitHub/Drive fetches when set).
# Override at runtime with the WGZ_API_URL env var; falls back to APP_DIR/api_url.txt.
API_URL_FILE = APP_DIR / "api_url.txt"
DEFAULT_API_URL = "https://chiatien.holao.online/wgz-api"


def get_api_base_url() -> str:
    env = os.environ.get("WGZ_API_URL")
    if env:
        return env.rstrip("/")
    if API_URL_FILE.exists():
        try:
            v = API_URL_FILE.read_text(encoding="utf-8-sig").strip()
            if v:
                return v.rstrip("/")
        except Exception:
            pass
    return DEFAULT_API_URL.rstrip("/")

MAIN_EXE_NAME = "GameUpdater.exe"
LAUNCHER_EXE_NAME = "Launcher.exe"
UPDATER_EXE_NAME = "updater.exe"
UNRAR_EXE = "UnRAR.exe"

# Bundled portable RustDesk (used by the remote-support button).
RUSTDESK_DIR = RESOURCES_DIR / "rustdesk"
RUSTDESK_EXE = RUSTDESK_DIR / "rustdesk.exe"
RUSTDESK_CONFIG_TOML = (
    Path(os.environ.get("APPDATA", str(Path.home()))) / "RustDesk" / "config" / "RustDesk2.toml"
)
# Permanent support password that the install step writes via `RustDesk --password`.
# Plaintext is persisted here so subsequent support calls reuse it without UAC.
RUSTDESK_SUPPORT_PW_FILE = APP_DIR / "rustdesk_support_pw.txt"

SINGLETON_MUTEX_NAME = "WGZ_GameUpdater_Singleton"


def ensure_user_dirs() -> None:
    for d in (INSTALL_ROOT, APP_DIR, LOG_DIR, USER_DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)


def find_credentials() -> "Path | None":
    """Return credentials.json: prefer APP_DIR, fall back to the bundled copy."""
    if CREDENTIALS_FILE.exists():
        return CREDENTIALS_FILE
    for candidate in (PACKAGE_ROOT / "credentials.json", PACKAGE_ROOT.parent / "credentials.json"):
        if candidate.exists():
            return candidate
    return None


def find_github_token() -> "Path | None":
    """Return github_token.txt: prefer APP_DIR, fall back to bundled copy."""
    if GITHUB_TOKEN_FILE.exists():
        return GITHUB_TOKEN_FILE
    bundled = PACKAGE_ROOT / "github_token.txt"
    if bundled.exists():
        return bundled
    return None


SERVICE_ACCOUNT_FILE = APP_DIR / "service_account.json"


def find_service_account() -> "Path | None":
    """Return service_account.json: prefer APP_DIR, fall back to bundled copy."""
    if SERVICE_ACCOUNT_FILE.exists():
        return SERVICE_ACCOUNT_FILE
    bundled = PACKAGE_ROOT / "service_account.json"
    if bundled.exists():
        return bundled
    return None


def resource(*parts: str) -> Path:
    return RESOURCES_DIR.joinpath(*parts)


def icon(name: str) -> Path:
    return ICONS_DIR / name
