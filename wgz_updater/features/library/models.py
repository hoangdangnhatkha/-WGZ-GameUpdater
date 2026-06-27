from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Iterable

from packaging import version as pkg_version

from ...core import api_client
from ...core.config import Game
from ...core.paths import USER_DATA_DIR, ensure_user_dirs

log = logging.getLogger(__name__)

_INSTALL_REGISTRY = USER_DATA_DIR / "install_paths.json"


_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".avif")
# Hosts that serve images without a recognisable extension in the URL path
# (Google encrypted thumbs / user uploads, Steam CDN, GitHub raw, etc.).
_IMAGE_HOSTS = (
    "encrypted-tbn",
    "googleusercontent.com",
    "lh3.googleusercontent",
    "steamcdn-a.akamaihd.net",
    "cdn.akamai.steamstatic.com",
    "shared.akamai.steamstatic.com",
    "shared.cloudflare.steamstatic.com",
    "raw.githubusercontent.com",
)


def _is_image_url(url: str) -> bool:
    if not url:
        return False
    u = url.lower().split("?", 1)[0]
    if any(u.endswith(ext) for ext in _IMAGE_EXTS):
        return True
    return any(host in u for host in _IMAGE_HOSTS)


def filter_slideshow_images(slideshow) -> list[str]:
    """Return only entries from `slideshow` that look like real image URLs.

    Skips Steam store / Wikipedia / generic webpages that users sometimes
    paste into the slideshow field — they'd otherwise render as a black
    panel because ImageLoader can't decode an HTML page.
    """
    return [u for u in (slideshow or []) if _is_image_url(u)]


def resolve_launch_target(entries, registry) -> tuple | None:
    """For a list of mod entries, return the first one whose install dir +
    resolved launch file actually exists on disk.

    Returns `(Game, install_path: Path, launch_relative: str)` or None.
    Honors per-user override from LocalConfig.game_launchers, falls back to
    Game.launch_file from the server-side mod definition.
    """
    from ...core.local_config import LocalConfig
    local = LocalConfig()
    for e in entries:
        path = registry.install_path(e.id)
        if not path or not path.exists():
            continue
        launch_rel = (local.get_game_launcher(e.id) or e.launch_file or "").strip()
        if not launch_rel:
            continue
        try:
            target = path / launch_rel
            if target.exists():
                return (e, path, launch_rel)
        except Exception:
            continue
    return None


def launch_game(install_path, launch_relative: str) -> None:
    """Launch the game exe through ShellExecute so UAC prompts work for exes
    whose manifest declares `requireAdministrator`."""
    import os
    from pathlib import Path
    target = Path(install_path) / launch_relative
    if not target.exists():
        raise FileNotFoundError(target)
    try:
        os.startfile(str(target), cwd=str(target.parent))
    except TypeError:
        prev = os.getcwd()
        try:
            os.chdir(str(target.parent))
            os.startfile(str(target))
        finally:
            os.chdir(prev)


def pick_theme_image(theme) -> str:
    """Pick the best single image URL for a theme.

    Prefers the first image-like slideshow entry, then falls back to
    `theme.image`. Returns "" when nothing usable is configured.
    """
    if theme is None:
        return ""
    imgs = filter_slideshow_images(getattr(theme, "slideshow", None))
    if imgs:
        return imgs[0]
    return getattr(theme, "image", "") or ""


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
    """Per-user install state. Local JSON cache + wgz-api sync.

    Strategy:
    * Constructor pulls the latest state from the API once; if the call fails
      (offline, no auth), the local JSON cache is used as the authoritative copy.
    * Every `record_install`/`clear` writes locally AND fires the API call.
      Local cache stays authoritative if the API call fails so the UI still
      reflects the install.
    """

    def __init__(self) -> None:
        self._data = _load_registry()
        try:
            server = api_client.get_installs()
            if isinstance(server, dict) and server:
                self._data = server
                _save_registry(self._data)
        except Exception as exc:
            log.warning("Install sync from API failed; using local cache (%s)", exc)

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
        try:
            api_client.put_install(int(game_id), str(path), version)
        except Exception:
            log.warning("Mirroring install to API failed", exc_info=True)

    def clear(self, game_id: str) -> None:
        self._data.pop(game_id, None)
        _save_registry(self._data)
        try:
            api_client.delete_install(int(game_id))
        except Exception:
            log.warning("Mirroring install delete to API failed", exc_info=True)

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
