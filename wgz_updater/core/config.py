from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .http import get_json
from .paths import (
    APP_DIR,
    CONFIG_BUNDLED,
    CONFIG_LOCAL,
    GITHUB_JSON_URL,
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


class AppConfig(BaseModel):
    updater: UpdaterInfo = Field(default_factory=UpdaterInfo)
    games: list[Game] = Field(default_factory=list)
    themes: dict[str, GameTheme] = Field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict) -> "AppConfig":
        updater = UpdaterInfo(**raw.get("updater", {}))

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
            if key in ("updater", "game_themes.json") or not isinstance(value, dict):
                continue
            try:
                games.append(Game(id=str(key), **value))
            except Exception as exc:
                log.warning("Skipping invalid game entry %s: %s", key, exc)
        return cls(updater=updater, games=games, themes=themes)


def _read_local() -> dict | None:
    for path in (CONFIG_LOCAL, CONFIG_BUNDLED):
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


def load_config(*, prefer_remote: bool = True) -> AppConfig:
    raw: dict | None = None
    if prefer_remote:
        try:
            raw = get_json(GITHUB_JSON_URL, cachebust=True)
            _write_cache(raw)
            log.info("Loaded remote config")
        except Exception:
            log.warning("Remote config fetch failed; falling back to local")
    if raw is None:
        raw = _read_local() or {}
    return AppConfig.from_raw(raw)
