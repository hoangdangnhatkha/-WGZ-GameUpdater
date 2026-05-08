from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from packaging import version as pkg_version

from .paths import APP_DIR, MAIN_EXE_NAME, UPDATER_EXE_NAME, VERSION_FILE

log = logging.getLogger(__name__)


def get_local_version() -> str:
    if VERSION_FILE.exists():
        try:
            return VERSION_FILE.read_text(encoding="utf-8").strip() or "0.0.0"
        except Exception:
            log.exception("Reading local version")
    return "0.0.0"


def set_local_version(value: str) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(value, encoding="utf-8")


def is_remote_newer(remote: str) -> bool:
    try:
        return pkg_version.parse(remote) > pkg_version.parse(get_local_version())
    except Exception:
        return False


def spawn_updater_and_exit(updater_path: Path | None = None) -> bool:
    target = updater_path or (APP_DIR / UPDATER_EXE_NAME)
    if not target.exists():
        log.warning("Updater binary not found at %s", target)
        return False
    try:
        subprocess.Popen([str(target)], cwd=str(target.parent))
        sys.exit(0)
    except Exception:
        log.exception("Failed to spawn updater")
        return False
    return True


def main_exe_path() -> Path:
    return APP_DIR / MAIN_EXE_NAME
