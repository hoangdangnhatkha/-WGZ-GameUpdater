from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from . import api_client
from .paths import (
    APP_DIR,
    CONFIG_BUNDLED,
    CONFIG_LOCAL,
    THEMES_BUNDLED_CANDIDATES,
    THEMES_LOCAL,
    ensure_user_dirs,
)

log = logging.getLogger(__name__)


class UpdaterInfo(BaseModel):
    latest_version: str = "0.0.0"
    release_notes: str = ""
    download_url: str | None = None
    base_url: str | None = None

    @property
    def effective_url(self) -> str | None:
        return self.base_url or self.download_url


class GameTheme(BaseModel):
    image: str = ""
    slideshow: list[str] = Field(default_factory=list)
    trailer_url: str = ""


class Game(BaseModel):
    id: str
    name: str
    game: str = ""
    version: str = ""
    type: str = "zip"
    url: str | None = None
    urls: list[str] = Field(default_factory=list)
    password: str | None = None
    delete_before_extract: list[str] = Field(default_factory=list)
    path_guide: str = ""
    launch_file: str | None = None
    tag: str | None = None
    # ISO-8601 timestamps populated by /api/config (server-side). Used by the
    # Library landing page to surface the most recently uploaded mod as the
    # featured hero.
    created_at: str | None = None
    updated_at: str | None = None

    @field_validator("path_guide", mode="before")
    @classmethod
    def _coerce_path_guide(cls, v: Any) -> str:
        return v if isinstance(v, str) else ""

    @field_validator("urls", mode="before")
    @classmethod
    def _ensure_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)

    @property
    def primary_url(self) -> str | None:
        if self.url:
            return self.url
        if self.urls:
            return self.urls[0]
        return None


class SupportConfig(BaseModel):
    discord_webhook: str = ""
    mention: str = ""  # optional `<@&ROLE_ID>` injected before payload


class AppConfig(BaseModel):
    updater: UpdaterInfo = Field(default_factory=UpdaterInfo)
    games: list[Game] = Field(default_factory=list)
    themes: dict[str, GameTheme] = Field(default_factory=dict)
    support: SupportConfig = Field(default_factory=SupportConfig)

    @classmethod
    def from_raw(cls, raw: dict) -> "AppConfig":
        updater = UpdaterInfo(**raw.get("updater", {}))
        support_raw = raw.get("support", {})
        support = SupportConfig(**support_raw) if isinstance(support_raw, dict) else SupportConfig()

        # Parse game themes
        themes: dict[str, GameTheme] = {}
        themes_raw = raw.get("game_themes.json", {})
        if isinstance(themes_raw, dict):
            for k, v in themes_raw.items():
                if isinstance(v, str):
                    themes[k] = GameTheme(image=v)
                elif isinstance(v, dict):
                    themes[k] = GameTheme(
                        image=v.get("image", ""),
                        slideshow=v.get("slideshow", []),
                        trailer_url=v.get("trailer_url", ""),
                    )

        games: list[Game] = []
        for key, value in raw.items():
            if key in ("updater", "game_themes.json", "support") or not isinstance(value, dict):
                continue
            try:
                games.append(Game(id=str(key), **value))
            except Exception as exc:
                log.warning("Skipping invalid game entry %s: %s", key, exc)
        return cls(updater=updater, games=games, themes=themes, support=support)


def _read_local() -> dict | None:
    for path in (CONFIG_LOCAL, CONFIG_BUNDLED):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                log.exception("Failed reading %s", path)
    return None


def _read_local_themes() -> dict | None:
    for path in (THEMES_LOCAL, *THEMES_BUNDLED_CANDIDATES):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                log.exception("Failed reading %s", path)
    return None


def _write_cache(raw: dict) -> None:
    ensure_user_dirs()
    try:
        CONFIG_LOCAL.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        log.exception("Failed writing config cache")


def _write_themes_cache(raw: dict) -> None:
    ensure_user_dirs()
    try:
        THEMES_LOCAL.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        log.exception("Failed writing themes cache")


def load_config(*, prefer_remote: bool = True) -> AppConfig:
    """Load the games catalog.

    Source priority:
      1. wgz-api `/api/config` (preferred; returns one merged JSON containing
         updater, games, and themes folded under the legacy "game_themes.json" key)
      2. local cache at CONFIG_LOCAL / THEMES_LOCAL
      3. bundled defaults

    The legacy GitHub raw URLs (GITHUB_JSON_URL, GITHUB_THEMES_URL) are no
    longer fetched; they remain in `paths.py` only for migration tooling.
    """
    raw: dict | None = None
    if prefer_remote:
        try:
            raw = api_client.get_config()
            _write_cache(raw)
            # Mirror themes into THEMES_LOCAL too so the manager view still has a snapshot.
            themes_blob = raw.get("game_themes.json") if isinstance(raw, dict) else None
            if isinstance(themes_blob, dict):
                _write_themes_cache(themes_blob)
            log.info("Loaded config from wgz-api")
        except Exception:
            log.warning("API config fetch failed; falling back to local cache", exc_info=True)

    if raw is None:
        raw = _read_local() or {}
        themes_raw = _read_local_themes() or {}
        if isinstance(themes_raw, dict) and themes_raw and "game_themes.json" not in raw:
            raw["game_themes.json"] = themes_raw

    return AppConfig.from_raw(raw)
