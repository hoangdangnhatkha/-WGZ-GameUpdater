# User Flow Parity — WGZ Game Updater Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat table/panel UI with the original tkinter app's 3-page library flow (game card grid → detail → download progress) and 2-level accounts flow (service grid → account list with Google Drive sync).

**Architecture:** Each feature view (LibraryView, AccountsView) owns an internal QStackedWidget. Pages are self-contained widgets that emit navigation signals picked up by the parent coordinator. Existing workers (DownloadWorker, ExtractWorker, RiotLoginWorker, SheetsService, GitHubSync) are reused unchanged.

**Tech Stack:** PyQt6, httpx (image loading), gdown (downloads), pydantic v2, google-api-python-client, pywinauto, winreg (stdlib)

---

## File Map

### New files
| File | Responsibility |
|---|---|
| `wgz_updater/core/local_config.py` | Singleton wrapping `settings.json` (game paths, launchers, Steam/Riot paths) |
| `wgz_updater/core/auto_path.py` | QThread: finds Steam/Riot via Windows Registry |
| `wgz_updater/widgets/dialogs.py` | Styled dialog helpers: wgz_info, wgz_warn, wgz_error, wgz_ask, DownloadConfirmDialog |
| `wgz_updater/features/library/image_loader.py` | QThreadPool-based image loader with 2-layer cache |
| `wgz_updater/features/library/game_card.py` | GameCard widget: image, tag badge, name, action button |
| `wgz_updater/features/library/game_grid_page.py` | Page 0 of LibraryView: 3-col grid + search |
| `wgz_updater/features/library/game_detail_page.py` | Page 1: hero image, mod selector, path_guide, install path, download/launch |
| `wgz_updater/features/library/download_progress_page.py` | Page 2: full-screen download + extract progress |
| `wgz_updater/features/accounts/service_grid_page.py` | Page 0 of AccountsView: 5-col service icon grid |
| `wgz_updater/features/accounts/account_list_page.py` | Page 1: per-service account list, Drive sync, trailer |
| `wgz_updater/features/accounts/account_dialog.py` | QDialog: add/edit account (all fields) |

### Modified files
| File | Change |
|---|---|
| `wgz_updater/core/config.py` | Add `GameTheme` model; parse `"game_themes.json"` block into `AppConfig.themes` |
| `wgz_updater/features/library/models.py` | `InstallRegistry` unchanged; `filter_games` kept |
| `wgz_updater/features/accounts/models.py` | Add `nickname`, `game` fields to `AccountRecord`; add `to_json/from_json` |
| `wgz_updater/features/library/view.py` | Rewrite: thin QStackedWidget coordinator wiring 3 pages |
| `wgz_updater/features/accounts/view.py` | Rewrite: QStackedWidget coordinator + Drive/GitHub sync workers |
| `wgz_updater/app.py` | Add admin elevation check + LocalConfig.load() + AutoPathWorker |
| `wgz_updater/resources/strings_vi.py` | Add strings for new pages |
| `wgz_updater/resources/qss/styles.qss` | Add GameCard, ServiceCard, ProgressPage, TagBadge, AccountRow styles |

### Deleted files
| File | Reason |
|---|---|
| `wgz_updater/features/library/game_detail_panel.py` | Replaced by game_detail_page.py |
| `wgz_updater/features/library/game_table_model.py` | Table replaced by card grid |
| `wgz_updater/widgets/progress_card.py` | Replaced by download_progress_page.py |

---

## Task 1: Strings + QSS foundation

**Files:**
- Modify: `wgz_updater/resources/strings_vi.py`
- Modify: `wgz_updater/resources/qss/styles.qss`

- [ ] **Add missing Vietnamese strings to `strings_vi.py`**

Append to the end of `wgz_updater/resources/strings_vi.py`:

```python
# Library grid + detail page
ACTION_LAUNCH_GAME = "🚀 Chạy Game"
ACTION_BACK = "← Quay lại"
ACTION_BROWSE_FOLDER = "Chọn thư mục..."
LABEL_INSTALL_PATH = "Thư mục cài đặt:"
LABEL_PATH_GUIDE = "Hướng dẫn cài đặt:"
LABEL_MOD_SELECT = "Chọn bản cài:"
LABEL_PART_OF = "Phần {current}/{total}"
STATUS_READY = "Sẵn sàng"
STATUS_DONE = "Hoàn tất!"
STATUS_CANCELLED = "Đã hủy"

# Accounts
ACTION_SAVE_DRIVE = "Lưu lên Drive"
ACTION_LOAD_DRIVE = "Tải từ Drive"
ACTION_ADD_ACCOUNT = "Thêm tài khoản"
LABEL_SERVICE = "Dịch vụ:"
LABEL_NICKNAME = "Tên hiển thị:"
LABEL_GAME_TAG = "Game:"
LABEL_ACCOUNTS_COUNT = "{count} tài khoản"
DIALOG_CONFIRM_LOGOUT = "Xác nhận đăng xuất"
MSG_ACCOUNTS_SAVED = "Đã lưu tài khoản lên Drive thành công."
MSG_ACCOUNTS_LOADED = "Đã tải tài khoản từ Drive."
MSG_DRIVE_ERROR = "Lỗi Drive: {error}"
MSG_NO_ACCOUNTS = "Chưa có tài khoản nào."
MSG_SELECT_ACCOUNT = "Hãy chọn một tài khoản."

# Download confirm
DIALOG_DOWNLOAD_CONFIRM = "Xác nhận tải về"
MSG_DOWNLOAD_CONFIRM = "Tải {name} ({parts} phần)?\nDung lượng trống: {free:.1f} GB"
```

- [ ] **Add QSS styles for new widgets**

Append to the end of `wgz_updater/resources/qss/styles.qss`:

```css
/* ── Game Card ── */
#GameCard {
    background: #252545;
    border-radius: 6px;
    border: 1px solid #333;
}
#GameCard:hover {
    background: #2d2d60;
    border: 1px solid #0078d4;
}
#GameCardName {
    font-size: 11px;
    font-weight: 600;
    color: #e0e0e0;
}

/* ── Tag Badge ── */
/* Inline styles are set per-tag in GameCard.__init__ */

/* ── Hero Image placeholder ── */
#HeroImage {
    background: #1a1a2e;
    border-radius: 4px;
}

/* ── Service Card (Accounts grid) ── */
#ServiceCard {
    background: #252545;
    border-radius: 6px;
    border: 1px solid #333;
    min-width: 150px;
}
#ServiceCard:hover {
    background: #2d2d60;
    border: 1px solid #0078d4;
}
#ServiceCardName {
    font-size: 12px;
    font-weight: 600;
    color: #e0e0e0;
}
#ServiceCardCount {
    font-size: 10px;
    color: #888;
}

/* ── Download Progress Page ── */
#ProgressPage {
    background: transparent;
}
#ProgressPage QProgressBar {
    min-height: 18px;
    border-radius: 9px;
}

/* ── Account Row ── */
#AccountRow {
    background: #252545;
    border-radius: 4px;
    padding: 6px;
    border: 1px solid #333;
}
#AccountRow:hover {
    border: 1px solid #0078d4;
}
#AccountNickname {
    font-size: 12px;
    font-weight: 600;
    color: #e0e0e0;
}
#AccountMeta {
    font-size: 10px;
    color: #888;
}

/* ── Back Button ── */
#BackButton {
    background: transparent;
    border: none;
    color: #0078d4;
    font-size: 13px;
    padding: 4px 0;
    text-align: left;
}
#BackButton:hover {
    color: #4da3ff;
}
```

- [ ] **Commit**

```bash
git add wgz_updater/resources/strings_vi.py wgz_updater/resources/qss/styles.qss
git commit -m "feat: add strings and QSS for new UI pages"
```

---

## Task 2: LocalConfig — persistent settings wrapper

**Files:**
- Create: `wgz_updater/core/local_config.py`
- Create: `tests/test_local_config.py`

- [ ] **Write the failing test**

Create `tests/__init__.py` (empty) and `tests/test_local_config.py`:

```python
import json, tempfile
from pathlib import Path
import pytest

def test_local_config_load_save(monkeypatch, tmp_path):
    import wgz_updater.core.local_config as lc_mod
    lc_mod._SETTINGS_FILE = tmp_path / "settings.json"
    lc_mod._instance = None  # reset singleton

    from wgz_updater.core.local_config import LocalConfig
    cfg = LocalConfig()
    cfg.load()  # file doesn't exist yet — should not raise
    cfg.set_game_path("game1", "D:/Games/game1")
    cfg.last_used_folder = "D:/Games"
    cfg.save()

    # Re-create singleton and reload
    lc_mod._instance = None
    cfg2 = LocalConfig()
    cfg2.load()
    assert cfg2.get_game_path("game1") == "D:/Games/game1"
    assert cfg2.last_used_folder == "D:/Games"
```

- [ ] **Run test to verify it fails**

```powershell
python -m pytest tests/test_local_config.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` — `local_config` doesn't exist yet.

- [ ] **Implement `wgz_updater/core/local_config.py`**

```python
from __future__ import annotations

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
            _instance._data: dict = {k: v for k, v in _DEFAULTS.items()}
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
```

- [ ] **Run test to verify it passes**

```powershell
python -m pytest tests/test_local_config.py -v
```

Expected: `PASSED`

- [ ] **Commit**

```bash
git add wgz_updater/core/local_config.py tests/
git commit -m "feat: add LocalConfig singleton for settings.json"
```

---

## Task 3: GameTheme model in AppConfig

**Files:**
- Modify: `wgz_updater/core/config.py`
- Create: `tests/test_config_themes.py`

- [ ] **Write the failing test**

Create `tests/test_config_themes.py`:

```python
from wgz_updater.core.config import AppConfig

_RAW = {
    "updater": {"latest_version": "1.0.0"},
    "game_themes.json": {
        "Elden Ring": {
            "image": "https://example.com/er.jpg",
            "slideshow": ["https://a.com/1.jpg", "https://a.com/2.jpg"],
            "trailer_url": "https://youtube.com/watch?v=abc"
        },
        "Night Reign": "https://example.com/nr.jpg",
    },
    "Mod_1": {
        "name": "Night Reign Mod",
        "game": "Night Reign",
        "version": "v2.0",
        "urls": ["https://drive.google.com/file1"],
        "type": "zip",
        "tag": "HOT",
    },
}


def test_themes_parsed():
    cfg = AppConfig.from_raw(_RAW)
    assert "Elden Ring" in cfg.themes
    theme = cfg.themes["Elden Ring"]
    assert theme.image == "https://example.com/er.jpg"
    assert len(theme.slideshow) == 2
    assert theme.trailer_url == "https://youtube.com/watch?v=abc"


def test_string_theme_becomes_image():
    cfg = AppConfig.from_raw(_RAW)
    assert cfg.themes["Night Reign"].image == "https://example.com/nr.jpg"


def test_games_parsed():
    cfg = AppConfig.from_raw(_RAW)
    assert len(cfg.games) == 1
    assert cfg.games[0].tag == "HOT"
```

- [ ] **Run test to verify it fails**

```powershell
python -m pytest tests/test_config_themes.py -v
```

Expected: `AttributeError: 'AppConfig' object has no attribute 'themes'`

- [ ] **Add `GameTheme` model and update `AppConfig.from_raw` in `wgz_updater/core/config.py`**

Add after the `UpdaterInfo` class:

```python
class GameTheme(BaseModel):
    image: str = ""
    slideshow: list[str] = Field(default_factory=list)
    trailer_url: str = ""
```

Update `AppConfig`:

```python
class AppConfig(BaseModel):
    updater: UpdaterInfo = Field(default_factory=UpdaterInfo)
    games: list[Game] = Field(default_factory=list)
    themes: dict[str, "GameTheme"] = Field(default_factory=dict)

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
```

- [ ] **Run test to verify it passes**

```powershell
python -m pytest tests/test_config_themes.py -v
```

Expected: 3 tests `PASSED`

- [ ] **Commit**

```bash
git add wgz_updater/core/config.py tests/test_config_themes.py
git commit -m "feat: add GameTheme model and parse game_themes.json block"
```

---

## Task 4: Update AccountRecord model

**Files:**
- Modify: `wgz_updater/features/accounts/models.py`
- Modify: `wgz_updater/features/accounts/account_list_model.py`
- Create: `tests/test_account_record.py`

- [ ] **Write the failing test**

Create `tests/test_account_record.py`:

```python
from wgz_updater.features.accounts.models import AccountRecord


def test_to_json():
    rec = AccountRecord(
        service="Steam", username="user1", password="pass1",
        nickname="My Steam", game="Elden Ring"
    )
    d = rec.to_json()
    assert d["nickname"] == "My Steam"
    assert d["username"] == "user1"
    assert d["game"] == "Elden Ring"
    assert d["type"] == "steam"


def test_from_json():
    rec = AccountRecord.from_json("Riot", {
        "nickname": "Riot Main",
        "username": "riotuser",
        "password": "riotpass",
        "type": "riot",
        "game": "Valorant",
    })
    assert rec.service == "Riot"
    assert rec.nickname == "Riot Main"
    assert rec.game == "Valorant"
```

- [ ] **Run test to verify it fails**

```powershell
python -m pytest tests/test_account_record.py -v
```

Expected: `TypeError` — `AccountRecord` doesn't accept `nickname` or `game` yet.

- [ ] **Update `wgz_updater/features/accounts/models.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AccountRecord:
    service: str
    username: str
    password: str = ""
    nickname: str = ""
    game: str = ""
    note: str = ""

    def to_row(self) -> list[str]:
        return [self.service, self.username, self.password, self.nickname, self.game, self.note]

    @classmethod
    def from_row(cls, row: list[str]) -> "AccountRecord":
        padded = list(row) + [""] * (6 - len(row))
        return cls(
            service=padded[0], username=padded[1], password=padded[2],
            nickname=padded[3], game=padded[4], note=padded[5],
        )

    def to_json(self) -> dict:
        return {
            "nickname": self.nickname,
            "username": self.username,
            "password": self.password,
            "type": self.service.lower(),
            "game": self.game,
        }

    @classmethod
    def from_json(cls, service: str, data: dict) -> "AccountRecord":
        return cls(
            service=service,
            username=data.get("username", ""),
            password=data.get("password", ""),
            nickname=data.get("nickname", ""),
            game=data.get("game", ""),
        )


@dataclass
class ServiceEntry:
    key: str
    label: str
    trailer_url: str = ""
    riot_window_titles: list[str] = field(default_factory=list)
```

- [ ] **Update `AccountListModel` in `wgz_updater/features/accounts/account_list_model.py`** to match the new columns (add Nickname column):

```python
from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt

from .models import AccountRecord

_HEADERS = ["Dịch vụ", "Tên hiển thị", "Username", "Mật khẩu", "Game"]
COL_SERVICE, COL_NICKNAME, COL_USERNAME, COL_PASSWORD, COL_GAME = range(5)


class AccountListModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._records: list[AccountRecord] = []
        self._mask = True

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(_HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return _HEADERS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        rec = self._records[index.row()]
        col = index.column()
        if col == COL_SERVICE:
            return rec.service
        if col == COL_NICKNAME:
            return rec.nickname or rec.username
        if col == COL_USERNAME:
            return rec.username
        if col == COL_PASSWORD:
            return "•" * 8 if self._mask else rec.password
        if col == COL_GAME:
            return rec.game
        return None

    def set_records(self, records: list[AccountRecord]) -> None:
        self.beginResetModel()
        self._records = list(records)
        self.endResetModel()

    def set_mask_password(self, mask: bool) -> None:
        self._mask = mask
        self.layoutChanged.emit()

    def add(self, record: AccountRecord) -> None:
        row = len(self._records)
        self.beginInsertRows(QModelIndex(), row, row)
        self._records.append(record)
        self.endInsertRows()

    def remove(self, row: int) -> None:
        if 0 <= row < len(self._records):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._records.pop(row)
            self.endRemoveRows()

    def record_at(self, row: int) -> AccountRecord | None:
        if 0 <= row < len(self._records):
            return self._records[row]
        return None

    def all_records(self) -> list[AccountRecord]:
        return list(self._records)
```

- [ ] **Run test to verify it passes**

```powershell
python -m pytest tests/test_account_record.py -v
```

Expected: 2 tests `PASSED`

- [ ] **Commit**

```bash
git add wgz_updater/features/accounts/models.py wgz_updater/features/accounts/account_list_model.py tests/test_account_record.py
git commit -m "feat: add nickname/game fields to AccountRecord + update list model"
```

---

## Task 5: ImageLoader — async image loading with 2-layer cache

**Files:**
- Create: `wgz_updater/features/library/image_loader.py`

- [ ] **Create `wgz_updater/features/library/image_loader.py`**

```python
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Callable

import httpx
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt6.QtGui import QPixmap

from ...core.paths import INSTALL_ROOT

log = logging.getLogger(__name__)

_IMG_CACHE_DIR = INSTALL_ROOT / "img_cache"
_MEM_CACHE: dict[str, QPixmap] = {}


class _ImageSignals(QObject):
    ready = pyqtSignal(str, object)  # url, QPixmap


class _ImageTask(QRunnable):
    def __init__(self, url: str, signals: _ImageSignals) -> None:
        super().__init__()
        self._url = url
        self._signals = signals
        self.setAutoDelete(True)

    def run(self) -> None:
        url = self._url
        h = hashlib.md5(url.encode()).hexdigest()
        disk_path = _IMG_CACHE_DIR / f"{h}.png"

        if disk_path.exists():
            pix = QPixmap(str(disk_path))
            if not pix.isNull():
                _MEM_CACHE[url] = pix
                self._signals.ready.emit(url, pix)
                return

        try:
            resp = httpx.get(url, timeout=10, follow_redirects=True)
            resp.raise_for_status()
            _IMG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            disk_path.write_bytes(resp.content)
            pix = QPixmap()
            pix.loadFromData(resp.content)
            if not pix.isNull():
                _MEM_CACHE[url] = pix
                self._signals.ready.emit(url, pix)
        except Exception:
            log.debug("Image load failed: %s", url, exc_info=True)


class ImageLoader(QObject):
    """Singleton image loader — thread-pool workers, 2-layer cache (memory + disk)."""

    _instance: "ImageLoader | None" = None

    @classmethod
    def instance(cls) -> "ImageLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._pool.setMaxThreadCount(4)
        self._pending_signals: dict[str, _ImageSignals] = {}
        self._callbacks: dict[str, list[Callable]] = {}

    def request(self, url: str, callback: Callable[[QPixmap], None]) -> None:
        """Request image at *url*. *callback(pixmap)* is called on the main thread."""
        if not url:
            return
        if url in _MEM_CACHE:
            callback(_MEM_CACHE[url])
            return
        if url not in self._callbacks:
            self._callbacks[url] = []
            sig = _ImageSignals(self)
            sig.ready.connect(self._on_ready)
            self._pending_signals[url] = sig
            self._pool.start(_ImageTask(url, sig))
        self._callbacks[url].append(callback)

    def _on_ready(self, url: str, pixmap: QPixmap) -> None:
        for cb in self._callbacks.pop(url, []):
            try:
                cb(pixmap)
            except Exception:
                log.exception("Image callback error for %s", url)
        self._pending_signals.pop(url, None)
```

- [ ] **Verify it imports cleanly**

```powershell
python -c "from wgz_updater.features.library.image_loader import ImageLoader; print('OK')"
```

Expected: `OK`

- [ ] **Commit**

```bash
git add wgz_updater/features/library/image_loader.py
git commit -m "feat: add ImageLoader with 2-layer cache (memory + disk)"
```

---

## Task 6: GameCard widget

**Files:**
- Create: `wgz_updater/features/library/game_card.py`

- [ ] **Create `wgz_updater/features/library/game_card.py`**

```python
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from ...core.config import Game
from ...resources.strings_vi import ACTION_DOWNLOAD, ACTION_UPDATE, STATUS_INSTALLED
from .image_loader import ImageLoader
from .models import InstallRegistry, InstallStatus

_TAG_COLORS: dict[str, tuple[str, str]] = {
    "HOT":  ("#ff4d4d", "#ffffff"),
    "GOTY": ("#ffd700", "#000000"),
    "NEW":  ("#4cff00", "#000000"),
    "UPD":  ("#4a90e2", "#ffffff"),
    "BEST": ("#9b59b6", "#ffffff"),
    "FIX":  ("#e67e22", "#ffffff"),
}


class GameCard(QFrame):
    clicked = pyqtSignal(object)  # emits Game

    def __init__(
        self,
        game: Game,
        registry: InstallRegistry,
        image_url: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._game = game
        self._registry = registry
        self.setObjectName("GameCard")
        self.setFixedWidth(210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Image
        self._img_label = QLabel(self)
        self._img_label.setFixedSize(194, 90)
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setObjectName("HeroImage")
        layout.addWidget(self._img_label)

        # Tag badge
        tag = (game.tag or "").upper()
        if tag in _TAG_COLORS:
            bg, fg = _TAG_COLORS[tag]
            self._tag = QLabel(tag, self)
            self._tag.setStyleSheet(
                f"background:{bg};color:{fg};border-radius:3px;"
                f"padding:1px 5px;font-size:9px;font-weight:700;"
            )
            layout.addWidget(self._tag)

        # Name
        name_lbl = QLabel(game.name, self)
        name_lbl.setObjectName("GameCardName")
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        # Action button
        self._btn = QPushButton(self)
        self._btn.clicked.connect(lambda: self.clicked.emit(self._game))
        layout.addWidget(self._btn)

        self._refresh_button()

        if image_url:
            ImageLoader.instance().request(image_url, self._set_image)

    def _refresh_button(self) -> None:
        status = self._registry.status_for(self._game)
        if status == InstallStatus.NOT_INSTALLED:
            self._btn.setText(ACTION_DOWNLOAD)
            self._btn.setObjectName("")
        elif status == InstallStatus.UPDATE:
            self._btn.setText(ACTION_UPDATE)
            self._btn.setObjectName("Accent")
        else:
            self._btn.setText("✓ " + STATUS_INSTALLED)
            self._btn.setObjectName("")
        # Refresh QSS for object name change
        self._btn.style().unpolish(self._btn)
        self._btn.style().polish(self._btn)

    def _set_image(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            194, 90,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._img_label.setPixmap(scaled)

    def refresh(self) -> None:
        """Call after install status changes."""
        self._refresh_button()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._game)
        super().mousePressEvent(event)
```

- [ ] **Verify it imports**

```powershell
python -c "from wgz_updater.features.library.game_card import GameCard; print('OK')"
```

Expected: `OK`

- [ ] **Commit**

```bash
git add wgz_updater/features/library/game_card.py
git commit -m "feat: add GameCard widget with image, tag badge, status button"
```

---

## Task 7: GameGridPage — 3-column game card grid

**Files:**
- Create: `wgz_updater/features/library/game_grid_page.py`

- [ ] **Create `wgz_updater/features/library/game_grid_page.py`**

```python
from __future__ import annotations

import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from ...core.config import AppConfig, Game
from ...resources.strings_vi import ACTION_REFRESH, NAV_LIBRARY
from .game_card import GameCard
from .models import InstallRegistry

log = logging.getLogger(__name__)
_COLS = 3


class GameGridPage(QWidget):
    game_selected = pyqtSignal(object)   # Game
    refresh_requested = pyqtSignal()

    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._cards: list[GameCard] = []
        self._config: AppConfig | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(10)

        # Header row
        header = QHBoxLayout()
        title = QLabel(NAV_LIBRARY, self)
        title.setStyleSheet("font-size:22px;font-weight:600;")
        header.addWidget(title)
        header.addStretch(1)
        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Tìm kiếm game...")
        self._search.setClearButtonEnabled(True)
        self._search.setFixedWidth(240)
        self._search.textChanged.connect(self._filter)
        header.addWidget(self._search)
        refresh_btn = QPushButton(ACTION_REFRESH, self)
        refresh_btn.clicked.connect(self.refresh_requested)
        header.addWidget(refresh_btn)
        outer.addLayout(header)

        # Scroll area with grid
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(10)
        self._grid.setContentsMargins(0, 0, 4, 4)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._scroll.setWidget(self._grid_widget)
        outer.addWidget(self._scroll, 1)

    def populate(self, config: AppConfig) -> None:
        self._config = config
        self._render(config.games)

    def _render(self, games: list[Game]) -> None:
        # Remove old cards
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        for i, game in enumerate(games):
            theme = config.themes.get(game.game) or config.themes.get(game.name) if (config := self._config) else None
            image_url = ""
            if theme:
                image_url = theme.image or (theme.slideshow[0] if theme.slideshow else "")
            card = GameCard(game, self._registry, image_url=image_url, parent=self._grid_widget)
            card.clicked.connect(self.game_selected)
            self._grid.addWidget(card, i // _COLS, i % _COLS)
            self._cards.append(card)

    def _filter(self, text: str) -> None:
        q = text.strip().lower()
        for card in self._cards:
            visible = not q or q in card._game.name.lower() or q in card._game.game.lower()
            card.setVisible(visible)

    def refresh_cards(self) -> None:
        """Refresh all card button states (call after install/update)."""
        for card in self._cards:
            card.refresh()
```

Fix the walrus operator usage (Python 3.8 compat) in `_render`:

```python
    def _render(self, games: list[Game]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        for i, game in enumerate(games):
            image_url = ""
            if self._config:
                theme = (
                    self._config.themes.get(game.game)
                    or self._config.themes.get(game.name)
                )
                if theme:
                    image_url = theme.image or (theme.slideshow[0] if theme.slideshow else "")
            card = GameCard(game, self._registry, image_url=image_url, parent=self._grid_widget)
            card.clicked.connect(self.game_selected)
            self._grid.addWidget(card, i // _COLS, i % _COLS)
            self._cards.append(card)
```

Also add the missing import at the top of the file:

```python
from PyQt6.QtCore import Qt, pyqtSignal
```

- [ ] **Verify import**

```powershell
python -c "from wgz_updater.features.library.game_grid_page import GameGridPage; print('OK')"
```

Expected: `OK`

- [ ] **Commit**

```bash
git add wgz_updater/features/library/game_grid_page.py
git commit -m "feat: add GameGridPage — 3-column game card grid with search"
```

---

## Task 8: GameDetailPage

**Files:**
- Create: `wgz_updater/features/library/game_detail_page.py`
- Delete: `wgz_updater/features/library/game_detail_panel.py`

- [ ] **Create `wgz_updater/features/library/game_detail_page.py`**

```python
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from ...core.config import AppConfig, Game
from ...core.local_config import LocalConfig
from ...resources.strings_vi import (
    ACTION_BACK, ACTION_BROWSE_FOLDER, ACTION_DOWNLOAD, ACTION_LAUNCH_GAME,
    ACTION_UPDATE, DIALOG_ERROR_TITLE,
)
from ...widgets.drop_zone import DropZone
from .image_loader import ImageLoader
from .models import InstallRegistry, InstallStatus

log = logging.getLogger(__name__)


class GameDetailPage(QWidget):
    download_requested = pyqtSignal(object, str, int)  # Game, install_path, url_index
    back_requested = pyqtSignal()

    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._local = LocalConfig()
        self._game: Game | None = None
        self._slideshow_urls: list[str] = []
        self._slide_idx = 0
        self._slide_timer = QTimer(self)
        self._slide_timer.setInterval(4000)
        self._slide_timer.timeout.connect(self._advance_slide)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        # Back button
        back_btn = QPushButton(ACTION_BACK, self)
        back_btn.setObjectName("BackButton")
        back_btn.clicked.connect(self.back_requested)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # Hero image
        self._hero = QLabel(self)
        self._hero.setFixedSize(460, 215)
        self._hero.setObjectName("HeroImage")
        self._hero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._hero, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Title
        self._title = QLabel(self)
        self._title.setStyleSheet("font-size:18px;font-weight:600;")
        layout.addWidget(self._title)

        # Mod/variant selector
        self._mod_combo = QComboBox(self)
        layout.addWidget(self._mod_combo)

        # Path guide
        self._guide = QPlainTextEdit(self)
        self._guide.setReadOnly(True)
        self._guide.setFixedHeight(80)
        self._guide.setPlaceholderText("Hướng dẫn cài đặt...")
        layout.addWidget(self._guide)

        # Install path row
        path_row = QHBoxLayout()
        self._path_edit = QLineEdit(self)
        self._path_edit.setPlaceholderText("Chọn thư mục cài đặt...")
        self._path_edit.textChanged.connect(self._update_launch_state)
        path_row.addWidget(self._path_edit, 1)
        browse_btn = QPushButton(ACTION_BROWSE_FOLDER, self)
        browse_btn.clicked.connect(self._on_browse)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        # DropZone
        drop = DropZone(self)
        drop.folder_dropped.connect(self._path_edit.setText)
        layout.addWidget(drop)

        # Action buttons
        btn_row = QHBoxLayout()
        self._dl_btn = QPushButton(ACTION_DOWNLOAD, self)
        self._dl_btn.setObjectName("Accent")
        self._dl_btn.clicked.connect(self._on_download)
        btn_row.addWidget(self._dl_btn)
        self._launch_btn = QPushButton(ACTION_LAUNCH_GAME, self)
        self._launch_btn.setEnabled(False)
        self._launch_btn.clicked.connect(self._on_launch)
        btn_row.addWidget(self._launch_btn)
        layout.addLayout(btn_row)
        layout.addStretch(1)

    def show_game(self, game: Game, config: AppConfig | None = None) -> None:
        self._game = game
        self._slide_timer.stop()
        self._slideshow_urls = []
        self._slide_idx = 0
        self._hero.clear()
        self._hero.setText("...")

        self._title.setText(f"{game.name}  {game.version}")

        # Hero image / slideshow
        if config:
            theme = config.themes.get(game.game) or config.themes.get(game.name)
            if theme:
                if theme.slideshow:
                    self._slideshow_urls = theme.slideshow
                    ImageLoader.instance().request(theme.slideshow[0], self._set_hero)
                    if len(theme.slideshow) > 1:
                        self._slide_timer.start()
                elif theme.image:
                    ImageLoader.instance().request(theme.image, self._set_hero)

        # Mod combo
        self._mod_combo.blockSignals(True)
        self._mod_combo.clear()
        if game.urls and len(game.urls) > 1:
            for i in range(len(game.urls)):
                self._mod_combo.addItem(f"{game.name} — Phần {i + 1}")
        elif game.primary_url:
            self._mod_combo.addItem(game.name)
        self._mod_combo.blockSignals(False)

        # Path guide
        self._guide.setPlainText(game.path_guide or "")

        # Install path pre-fill
        saved = self._local.get_game_path(game.id) or self._local.last_used_folder or ""
        self._path_edit.setText(saved)

        self._update_dl_button()
        self._update_launch_state()

    def _advance_slide(self) -> None:
        if not self._slideshow_urls:
            return
        self._slide_idx = (self._slide_idx + 1) % len(self._slideshow_urls)
        ImageLoader.instance().request(self._slideshow_urls[self._slide_idx], self._set_hero)

    def _set_hero(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            460, 215,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._hero.setPixmap(scaled)

    def _update_dl_button(self) -> None:
        if not self._game:
            return
        status = self._registry.status_for(self._game)
        self._dl_btn.setText(
            ACTION_UPDATE if status == InstallStatus.UPDATE else ACTION_DOWNLOAD
        )

    def _update_launch_state(self) -> None:
        if not self._game:
            self._launch_btn.setEnabled(False)
            return
        path_str = self._path_edit.text().strip()
        launch_rel = (
            self._local.get_game_launcher(self._game.id) or self._game.launch_file
        )
        if path_str and launch_rel:
            launch_abs = Path(path_str) / launch_rel
            self._launch_btn.setEnabled(launch_abs.exists())
        else:
            self._launch_btn.setEnabled(False)

    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục cài đặt")
        if folder:
            self._path_edit.setText(folder)

    def _on_download(self) -> None:
        if not self._game:
            return
        path = self._path_edit.text().strip()
        if not path:
            from ...widgets.dialogs import wgz_warn
            wgz_warn(self, "Chọn đường dẫn", "Vui lòng chọn thư mục cài đặt trước.")
            return
        self._local.set_game_path(self._game.id, path)
        self._local.last_used_folder = path
        self._local.save()
        url_idx = max(0, self._mod_combo.currentIndex())
        self.download_requested.emit(self._game, path, url_idx)

    def _on_launch(self) -> None:
        if not self._game:
            return
        path_str = self._path_edit.text().strip()
        launch_rel = (
            self._local.get_game_launcher(self._game.id) or self._game.launch_file
        )
        if not path_str or not launch_rel:
            return
        launch_abs = Path(path_str) / launch_rel
        if launch_abs.exists():
            try:
                subprocess.Popen([str(launch_abs)], cwd=str(launch_abs.parent))
            except Exception as exc:
                log.exception("Launch failed")
                from ...widgets.dialogs import wgz_error
                wgz_error(self, DIALOG_ERROR_TITLE, f"Không thể chạy game: {exc}")
```

- [ ] **Delete the old detail panel**

```powershell
Remove-Item "wgz_updater\features\library\game_detail_panel.py"
```

- [ ] **Verify import**

```powershell
python -c "from wgz_updater.features.library.game_detail_page import GameDetailPage; print('OK')"
```

Expected: `OK`

- [ ] **Commit**

```bash
git add wgz_updater/features/library/game_detail_page.py
git rm wgz_updater/features/library/game_detail_panel.py
git commit -m "feat: add GameDetailPage (hero image, slideshow, mod selector, path, launch)"
```

---

## Task 9: DownloadProgressPage

**Files:**
- Create: `wgz_updater/features/library/download_progress_page.py`
- Delete: `wgz_updater/widgets/progress_card.py`

- [ ] **Create `wgz_updater/features/library/download_progress_page.py`**

```python
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from ...core.config import Game
from ...core.win32_utils import prevent_sleep
from ...resources.strings_vi import ACTION_BACK, ACTION_CANCEL, STATUS_DONE
from .download_worker import DownloadWorker
from .extract_worker import ExtractWorker
from .models import InstallRegistry

log = logging.getLogger(__name__)


class DownloadProgressPage(QWidget):
    """Full-screen download + extraction progress page."""

    finished = pyqtSignal(object, str)    # Game, install_path (on success)
    cancelled = pyqtSignal()              # user cancelled or back after error

    # Forwarded to StatusStrip
    worker_started = pyqtSignal(object)
    worker_message = pyqtSignal(str)
    worker_progress = pyqtSignal(int)
    worker_finished = pyqtSignal()

    def __init__(self, registry: InstallRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._game: Game | None = None
        self._install_path: Path | None = None
        self._url_list: list[str] = []
        self._url_idx = 0
        self._archive_path: str = ""
        self._download_worker: DownloadWorker | None = None
        self._extract_worker: ExtractWorker | None = None
        self._sleep_ctx = None
        self.setObjectName("ProgressPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(16)
        layout.addStretch(2)

        self._game_label = QLabel(self)
        self._game_label.setStyleSheet("font-size:20px;font-weight:600;")
        self._game_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._game_label)

        self._part_label = QLabel(self)
        self._part_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._part_label.setStyleSheet("color:#aaa;font-size:13px;")
        layout.addWidget(self._part_label)

        self._progress = QProgressBar(self)
        self._progress.setRange(0, 100)
        self._progress.setTextVisible(True)
        layout.addWidget(self._progress)

        speed_row = QHBoxLayout()
        self._speed_label = QLabel("", self)
        speed_row.addWidget(self._speed_label)
        speed_row.addStretch(1)
        layout.addLayout(speed_row)

        self._status_label = QLabel(self)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("color:#aaa;")
        layout.addWidget(self._status_label)

        self._cancel_btn = QPushButton(ACTION_CANCEL, self)
        self._cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self._cancel_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(3)

    def start(self, game: Game, install_path: str, url_idx: int) -> None:
        """Begin download+extraction sequence."""
        self._game = game
        self._install_path = Path(install_path)
        self._archive_path = ""
        self._url_idx = 0

        # Multi-part: download all urls; single: download the chosen one
        if game.urls and len(game.urls) > 1:
            self._url_list = game.urls
        elif game.urls:
            self._url_list = [game.urls[url_idx]]
        elif game.url:
            self._url_list = [game.url]
        else:
            self._url_list = []

        self._game_label.setText(game.name)
        self._part_label.setText("")
        self._progress.setValue(0)
        self._speed_label.setText("")
        self._status_label.setText("Đang chuẩn bị...")
        self._cancel_btn.setText(ACTION_CANCEL)
        self._cancel_btn.setEnabled(True)
        # Reset button signal to cancel handler
        try:
            self._cancel_btn.clicked.disconnect()
        except TypeError:
            pass
        self._cancel_btn.clicked.connect(self._on_cancel)

        self._sleep_ctx = prevent_sleep()
        self._sleep_ctx.__enter__()
        self._start_next_download()

    def _start_next_download(self) -> None:
        if not self._url_list or self._url_idx >= len(self._url_list):
            self._start_extraction()
            return
        url = self._url_list[self._url_idx]
        total = len(self._url_list)
        if total > 1:
            self._part_label.setText(f"Phần {self._url_idx + 1}/{total}")

        game = self._game
        archive_name = f"{game.id}_part{self._url_idx + 1}.{game.type}".replace(" ", "_")
        cache_dir = Path(tempfile.gettempdir()) / "wgz_downloads"
        cache_dir.mkdir(parents=True, exist_ok=True)

        worker = DownloadWorker(url, cache_dir, archive_name, parent=self)
        worker.progress.connect(self._progress.setValue)
        worker.progress.connect(self.worker_progress)
        worker.speed.connect(self._speed_label.setText)
        worker.status.connect(self._status_label.setText)
        worker.status.connect(self.worker_message)
        worker.failed.connect(self._on_failed)
        worker.finished_ok.connect(self._on_part_done)
        self._download_worker = worker
        self.worker_started.emit(worker)
        worker.start()

    def _on_part_done(self, archive_path: str) -> None:
        self._archive_path = archive_path
        self._url_idx += 1
        self._download_worker = None
        self._start_next_download()

    def _start_extraction(self) -> None:
        if not self._archive_path:
            self._finish_success()
            return
        self._progress.setValue(0)
        self._part_label.setText("Đang giải nén...")
        worker = ExtractWorker(
            archive_path=Path(self._archive_path),
            target_dir=self._install_path,
            archive_type=self._game.type,
            password=self._game.password,
            delete_before=self._game.delete_before_extract,
            parent=self,
        )
        worker.progress.connect(self._progress.setValue)
        worker.progress.connect(self.worker_progress)
        worker.status.connect(self._status_label.setText)
        worker.status.connect(self.worker_message)
        worker.failed.connect(self._on_failed)
        worker.finished_ok.connect(lambda _: self._finish_success())
        self._extract_worker = worker
        self.worker_started.emit(worker)
        worker.start()

    def _finish_success(self) -> None:
        self._exit_sleep()
        self._status_label.setText(STATUS_DONE)
        self._progress.setValue(100)
        self._cancel_btn.setEnabled(False)
        if self._game and self._install_path:
            self._registry.record_install(
                self._game.id, self._install_path, self._game.version
            )
        self.worker_finished.emit()
        if self._game and self._install_path:
            self.finished.emit(self._game, str(self._install_path))

    def _on_failed(self, msg: str) -> None:
        log.error("Download/extract failed: %s", msg)
        self._exit_sleep()
        self._status_label.setText(f"Lỗi: {msg}")
        self._part_label.setText("")
        self.worker_finished.emit()
        # Repurpose cancel button as "Back"
        try:
            self._cancel_btn.clicked.disconnect()
        except TypeError:
            pass
        self._cancel_btn.setText(ACTION_BACK)
        self._cancel_btn.clicked.connect(self.cancelled)

    def _on_cancel(self) -> None:
        if self._download_worker:
            self._download_worker.cancel()
        self._exit_sleep()
        self.worker_finished.emit()
        self.cancelled.emit()

    def _exit_sleep(self) -> None:
        if self._sleep_ctx:
            try:
                self._sleep_ctx.__exit__(None, None, None)
            except Exception:
                pass
            self._sleep_ctx = None
```

- [ ] **Delete old progress_card.py**

```powershell
Remove-Item "wgz_updater\widgets\progress_card.py"
```

- [ ] **Verify import**

```powershell
python -c "from wgz_updater.features.library.download_progress_page import DownloadProgressPage; print('OK')"
```

Expected: `OK`

- [ ] **Commit**

```bash
git add wgz_updater/features/library/download_progress_page.py
git rm wgz_updater/widgets/progress_card.py
git commit -m "feat: add DownloadProgressPage with multi-part download chain"
```

---

## Task 10: LibraryView rewrite — QStackedWidget coordinator

**Files:**
- Modify: `wgz_updater/features/library/view.py` (complete rewrite)
- Delete: `wgz_updater/features/library/game_table_model.py`

- [ ] **Rewrite `wgz_updater/features/library/view.py`**

```python
from __future__ import annotations

import logging

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from ...core.config import AppConfig, load_config
from ...resources.strings_vi import DIALOG_ERROR_TITLE
from .download_progress_page import DownloadProgressPage
from .game_detail_page import GameDetailPage
from .game_grid_page import GameGridPage
from .models import InstallRegistry

log = logging.getLogger(__name__)

_PAGE_GRID = 0
_PAGE_DETAIL = 1
_PAGE_PROGRESS = 2


class LibraryView(QWidget):
    # Forwarded to StatusStrip
    worker_started = pyqtSignal(object)
    worker_message = pyqtSignal(str)
    worker_progress = pyqtSignal(int)
    worker_finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._registry = InstallRegistry()
        self._config: AppConfig | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget(self)
        layout.addWidget(self._stack)

        self._grid_page = GameGridPage(self._registry, self)
        self._detail_page = GameDetailPage(self._registry, self)
        self._progress_page = DownloadProgressPage(self._registry, self)

        self._stack.addWidget(self._grid_page)      # _PAGE_GRID = 0
        self._stack.addWidget(self._detail_page)    # _PAGE_DETAIL = 1
        self._stack.addWidget(self._progress_page)  # _PAGE_PROGRESS = 2

        # Navigation wiring
        self._grid_page.game_selected.connect(self._on_game_selected)
        self._grid_page.refresh_requested.connect(lambda: self.reload(prefer_remote=True))
        self._detail_page.back_requested.connect(
            lambda: self._stack.setCurrentIndex(_PAGE_GRID)
        )
        self._detail_page.download_requested.connect(self._on_download_requested)
        self._progress_page.finished.connect(self._on_download_finished)
        self._progress_page.cancelled.connect(
            lambda: self._stack.setCurrentIndex(_PAGE_GRID)
        )

        # StatusStrip forwarding
        self._progress_page.worker_started.connect(self.worker_started)
        self._progress_page.worker_message.connect(self.worker_message)
        self._progress_page.worker_progress.connect(self.worker_progress)
        self._progress_page.worker_finished.connect(self.worker_finished)

        self.reload(prefer_remote=False)

    def reload(self, *, prefer_remote: bool = True) -> None:
        try:
            self._config = load_config(prefer_remote=prefer_remote)
            self._grid_page.populate(self._config)
            log.info("Loaded %d games (remote=%s)", len(self._config.games), prefer_remote)
        except Exception as exc:
            log.exception("Config reload failed")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, DIALOG_ERROR_TITLE, str(exc))

    def _on_game_selected(self, game) -> None:
        self._detail_page.show_game(game, self._config)
        self._stack.setCurrentIndex(_PAGE_DETAIL)

    def _on_download_requested(self, game, install_path: str, url_idx: int) -> None:
        self._stack.setCurrentIndex(_PAGE_PROGRESS)
        self._progress_page.start(game, install_path, url_idx)

    def _on_download_finished(self, game, install_path: str) -> None:
        self._grid_page.refresh_cards()
        self._stack.setCurrentIndex(_PAGE_GRID)
```

- [ ] **Delete old table model**

```powershell
Remove-Item "wgz_updater\features\library\game_table_model.py"
```

- [ ] **Verify the app launches**

```powershell
python -m wgz_updater
```

Expected: App opens, Library tab shows a grid of game cards (images load async). Clicking a card opens the detail page. Back button returns to grid. No crashes in the log.

- [ ] **Commit**

```bash
git add wgz_updater/features/library/view.py
git rm wgz_updater/features/library/game_table_model.py
git commit -m "feat: rewrite LibraryView as QStackedWidget with 3-page flow"
```

---

## Task 11: Custom Dialogs

**Files:**
- Create: `wgz_updater/widgets/dialogs.py`

- [ ] **Create `wgz_updater/widgets/dialogs.py`**

```python
from __future__ import annotations

import shutil
from pathlib import Path

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QMessageBox, QVBoxLayout, QWidget


def wgz_info(parent: QWidget | None, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Icon.Information)
    box.exec()


def wgz_warn(parent: QWidget | None, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Icon.Warning)
    box.exec()


def wgz_error(parent: QWidget | None, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Icon.Critical)
    box.exec()


def wgz_ask(parent: QWidget | None, title: str, message: str) -> bool:
    result = QMessageBox.question(parent, title, message)
    return result == QMessageBox.StandardButton.Yes


class DownloadConfirmDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        game_name: str,
        part_count: int,
        install_path: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Xác nhận tải về")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)

        free_gb = 0.0
        if install_path:
            try:
                usage = shutil.disk_usage(install_path)
                free_gb = usage.free / (1024 ** 3)
            except Exception:
                pass

        parts_text = f"{part_count} phần" if part_count > 1 else "1 tệp"
        msg = f"Tải về: <b>{game_name}</b><br>Số phần: {parts_text}"
        if free_gb:
            msg += f"<br>Dung lượng trống: {free_gb:.1f} GB"

        lbl = QLabel(msg, self)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def confirm(
        parent: QWidget | None,
        game_name: str,
        part_count: int,
        install_path: str = "",
    ) -> bool:
        dlg = DownloadConfirmDialog(parent, game_name, part_count, install_path)
        return dlg.exec() == QDialog.DialogCode.Accepted
```

- [ ] **Verify import**

```powershell
python -c "from wgz_updater.widgets.dialogs import wgz_info, DownloadConfirmDialog; print('OK')"
```

Expected: `OK`

- [ ] **Commit**

```bash
git add wgz_updater/widgets/dialogs.py
git commit -m "feat: add custom styled dialogs (wgz_info/warn/error/ask, DownloadConfirmDialog)"
```

---

## Task 12: ServiceGridPage — 5-column accounts grid

**Files:**
- Create: `wgz_updater/features/accounts/service_grid_page.py`

- [ ] **Create `wgz_updater/features/accounts/service_grid_page.py`**

```python
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from ...resources.strings_vi import LABEL_ACCOUNTS_COUNT, NAV_ACCOUNTS

_MAX_COLS = 5


class ServiceCard(QFrame):
    clicked = pyqtSignal(str)  # service name

    def __init__(self, service_name: str, count: int, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ServiceCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(4)

        icon_lbl = QLabel(self)
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setText(service_name[0].upper())
        icon_lbl.setStyleSheet(
            "background:#0078d4;border-radius:20px;color:#fff;font-size:18px;font-weight:700;"
        )
        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        name_lbl = QLabel(service_name, self)
        name_lbl.setObjectName("ServiceCardName")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)

        count_lbl = QLabel(LABEL_ACCOUNTS_COUNT.format(count=count), self)
        count_lbl.setObjectName("ServiceCardCount")
        count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(count_lbl)

        self._service = service_name

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._service)
        super().mousePressEvent(event)


class ServiceGridPage(QWidget):
    service_selected = pyqtSignal(str)  # service name

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(10)

        title = QLabel(NAV_ACCOUNTS, self)
        title.setStyleSheet("font-size:22px;font-weight:600;")
        outer.addWidget(title)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(10)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._grid_widget)
        outer.addWidget(scroll, 1)

    def populate(self, accounts_data: dict[str, list]) -> None:
        """accounts_data: {service_name: [AccountRecord, ...]}"""
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        services = sorted(accounts_data.keys())
        # Always show Steam and Riot first
        priority = ["Steam", "Riot"]
        ordered = [s for s in priority if s in services] + [
            s for s in services if s not in priority
        ]
        # Add empty slots for Steam/Riot even if no accounts yet
        for s in priority:
            if s not in ordered:
                ordered.insert(priority.index(s), s)
        ordered = list(dict.fromkeys(ordered))  # deduplicate preserving order

        for i, service_name in enumerate(ordered):
            count = len(accounts_data.get(service_name, []))
            card = ServiceCard(service_name, count, self._grid_widget)
            card.clicked.connect(self.service_selected)
            self._grid.addWidget(card, i // _MAX_COLS, i % _MAX_COLS)
```

- [ ] **Verify import**

```powershell
python -c "from wgz_updater.features.accounts.service_grid_page import ServiceGridPage; print('OK')"
```

Expected: `OK`

- [ ] **Commit**

```bash
git add wgz_updater/features/accounts/service_grid_page.py
git commit -m "feat: add ServiceGridPage — 5-column accounts service grid"
```

---

## Task 13: AccountDialog — add/edit account form

**Files:**
- Create: `wgz_updater/features/accounts/account_dialog.py`

- [ ] **Create `wgz_updater/features/accounts/account_dialog.py`**

```python
from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from ...resources.strings_vi import (
    LABEL_GAME_TAG, LABEL_NICKNAME, LABEL_SERVICE,
)
from .models import AccountRecord

_KNOWN_SERVICES = ["Steam", "Riot"]


class AccountDialog(QDialog):
    """Add or edit an AccountRecord."""

    def __init__(
        self,
        parent: QWidget | None = None,
        record: AccountRecord | None = None,
        game_names: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Thêm tài khoản" if record is None else "Sửa tài khoản")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._service = QComboBox(self)
        self._service.addItems(_KNOWN_SERVICES)
        self._service.setEditable(True)
        form.addRow(LABEL_SERVICE, self._service)

        self._nickname = QLineEdit(self)
        form.addRow(LABEL_NICKNAME, self._nickname)

        self._username = QLineEdit(self)
        form.addRow("Username:", self._username)

        # Password with show/hide toggle
        pw_row = QHBoxLayout()
        self._password = QLineEdit(self)
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        pw_row.addWidget(self._password)
        toggle = QPushButton("👁", self)
        toggle.setFixedWidth(32)
        toggle.setCheckable(True)
        toggle.toggled.connect(
            lambda checked: self._password.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        pw_row.addWidget(toggle)
        form.addRow("Mật khẩu:", pw_row)

        self._game = QComboBox(self)
        self._game.addItem("")
        if game_names:
            self._game.addItems(game_names)
        self._game.setEditable(True)
        form.addRow(LABEL_GAME_TAG, self._game)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if record:
            self._service.setCurrentText(record.service)
            self._nickname.setText(record.nickname)
            self._username.setText(record.username)
            self._password.setText(record.password)
            self._game.setCurrentText(record.game)

    def get_record(self) -> AccountRecord:
        return AccountRecord(
            service=self._service.currentText().strip(),
            username=self._username.text().strip(),
            password=self._password.text(),
            nickname=self._nickname.text().strip(),
            game=self._game.currentText().strip(),
        )
```

- [ ] **Verify import**

```powershell
python -c "from wgz_updater.features.accounts.account_dialog import AccountDialog; print('OK')"
```

Expected: `OK`

- [ ] **Commit**

```bash
git add wgz_updater/features/accounts/account_dialog.py
git commit -m "feat: add AccountDialog with service/nickname/username/password/game fields"
```

---

## Task 14: AccountListPage — per-service account list

**Files:**
- Create: `wgz_updater/features/accounts/account_list_page.py`

- [ ] **Create `wgz_updater/features/accounts/account_list_page.py`**

```python
from __future__ import annotations

import logging
import subprocess

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSplitter, QVBoxLayout, QWidget,
)

from ...core.local_config import LocalConfig
from ...resources.strings_vi import (
    ACTION_ADD_ACCOUNT, ACTION_AUTO_LOGIN, ACTION_BACK,
    ACTION_LOAD_DRIVE, ACTION_SAVE_DRIVE, DIALOG_ERROR_TITLE,
    MSG_SELECT_ACCOUNT,
)
from ..accounts.trailer_player import TrailerPlayer
from .account_dialog import AccountDialog
from .models import AccountRecord
from .riot_login import RiotLoginWorker

log = logging.getLogger(__name__)


class AccountRow(QFrame):
    login_requested = pyqtSignal(object)   # AccountRecord
    edit_requested = pyqtSignal(object)    # AccountRecord
    delete_requested = pyqtSignal(object)  # AccountRecord

    def __init__(self, record: AccountRecord, parent=None) -> None:
        super().__init__(parent)
        self._record = record
        self.setObjectName("AccountRow")

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(8)

        info = QVBoxLayout()
        nick = record.nickname or record.username
        nick_lbl = QLabel(nick, self)
        nick_lbl.setObjectName("AccountNickname")
        info.addWidget(nick_lbl)
        meta = f"{record.service}  •  {record.game}" if record.game else record.service
        meta_lbl = QLabel(meta, self)
        meta_lbl.setObjectName("AccountMeta")
        info.addWidget(meta_lbl)
        row.addLayout(info, 1)

        copy_btn = QPushButton("Copy PW", self)
        copy_btn.setFixedWidth(70)
        copy_btn.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(record.password)
        )
        row.addWidget(copy_btn)

        login_btn = QPushButton(ACTION_AUTO_LOGIN, self)
        login_btn.setObjectName("Accent")
        login_btn.setFixedWidth(90)
        login_btn.clicked.connect(lambda: self.login_requested.emit(self._record))
        row.addWidget(login_btn)

        edit_btn = QPushButton("Sửa", self)
        edit_btn.setFixedWidth(44)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._record))
        row.addWidget(edit_btn)

        del_btn = QPushButton("Xóa", self)
        del_btn.setFixedWidth(44)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._record))
        row.addWidget(del_btn)


class AccountListPage(QWidget):
    back_requested = pyqtSignal()
    dirty_changed = pyqtSignal(bool)   # True when unsaved changes exist

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._service: str = ""
        self._records: list[AccountRecord] = []
        self._game_names: list[str] = []
        self._login_worker: RiotLoginWorker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(8)

        # Top bar
        top = QHBoxLayout()
        back_btn = QPushButton(ACTION_BACK, self)
        back_btn.setObjectName("BackButton")
        back_btn.clicked.connect(self.back_requested)
        top.addWidget(back_btn)
        self._title_lbl = QLabel(self)
        self._title_lbl.setStyleSheet("font-size:18px;font-weight:600;")
        top.addWidget(self._title_lbl)
        top.addStretch(1)
        self._save_btn = QPushButton(ACTION_SAVE_DRIVE, self)
        self._save_btn.setObjectName("Accent")
        self._save_btn.setEnabled(False)
        top.addWidget(self._save_btn)
        load_btn = QPushButton(ACTION_LOAD_DRIVE, self)
        top.addWidget(load_btn)
        outer.addLayout(top)

        # Splitter: account list | trailer
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        outer.addWidget(splitter, 1)

        # Left: scroll area of account rows
        left = QWidget(self)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._rows_widget = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setSpacing(6)
        self._rows_layout.setContentsMargins(0, 0, 4, 4)
        self._rows_layout.addStretch(1)
        self._scroll.setWidget(self._rows_widget)
        left_layout.addWidget(self._scroll, 1)

        add_btn = QPushButton(ACTION_ADD_ACCOUNT, self)
        add_btn.clicked.connect(self._on_add)
        left_layout.addWidget(add_btn)
        splitter.addWidget(left)

        # Right: trailer player
        self._trailer = TrailerPlayer(self)
        splitter.addWidget(self._trailer)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        # Wire Drive buttons
        self._save_btn.clicked.connect(self.save_requested)
        load_btn.clicked.connect(self.load_requested)

    save_requested = pyqtSignal()
    load_requested = pyqtSignal()

    def show_service(
        self,
        service_name: str,
        records: list[AccountRecord],
        game_names: list[str] | None = None,
    ) -> None:
        self._service = service_name
        self._records = list(records)
        self._game_names = game_names or []
        self._title_lbl.setText(service_name)
        self._render_rows()
        self._save_btn.setEnabled(False)

    def _render_rows(self) -> None:
        # Remove existing rows (keep the stretch at end)
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for rec in self._records:
            row_widget = AccountRow(rec, self._rows_widget)
            row_widget.login_requested.connect(self._on_login)
            row_widget.edit_requested.connect(self._on_edit)
            row_widget.delete_requested.connect(self._on_delete)
            self._rows_layout.insertWidget(self._rows_layout.count() - 1, row_widget)

    def get_records(self) -> list[AccountRecord]:
        return list(self._records)

    def set_records(self, records: list[AccountRecord]) -> None:
        self._records = list(records)
        self._render_rows()

    def _mark_dirty(self) -> None:
        self._save_btn.setEnabled(True)
        self.dirty_changed.emit(True)

    def _on_add(self) -> None:
        dlg = AccountDialog(self, game_names=self._game_names)
        if dlg.exec():
            self._records.append(dlg.get_record())
            self._render_rows()
            self._mark_dirty()

    def _on_edit(self, record: AccountRecord) -> None:
        dlg = AccountDialog(self, record=record, game_names=self._game_names)
        if dlg.exec():
            idx = self._records.index(record)
            self._records[idx] = dlg.get_record()
            self._render_rows()
            self._mark_dirty()

    def _on_delete(self, record: AccountRecord) -> None:
        from ...widgets.dialogs import wgz_ask
        if wgz_ask(self, "Xóa tài khoản", f"Xóa '{record.nickname or record.username}'?"):
            self._records.remove(record)
            self._render_rows()
            self._mark_dirty()

    def _on_login(self, record: AccountRecord) -> None:
        local = LocalConfig()
        service_lower = record.service.lower()
        if service_lower == "steam":
            steam = local.steam_path
            if not steam:
                from ...widgets.dialogs import wgz_warn
                wgz_warn(self, DIALOG_ERROR_TITLE, "Chưa tìm thấy Steam. Vui lòng thiết lập đường dẫn trong Cài Đặt.")
                return
            try:
                subprocess.Popen([steam, "-login", record.username, record.password])
            except Exception as exc:
                log.exception("Steam login failed")
                from ...widgets.dialogs import wgz_error
                wgz_error(self, DIALOG_ERROR_TITLE, str(exc))
        elif service_lower == "riot":
            if self._login_worker and self._login_worker.isRunning():
                return
            worker = RiotLoginWorker(
                username=record.username, password=record.password, parent=self
            )
            worker.failed.connect(
                lambda msg: (
                    __import__("wgz_updater.widgets.dialogs", fromlist=["wgz_error"]).wgz_error(
                        self, DIALOG_ERROR_TITLE, msg
                    )
                )
            )
            worker.finished.connect(lambda: setattr(self, "_login_worker", None))
            self._login_worker = worker
            worker.start()
        else:
            from ...widgets.dialogs import wgz_info
            wgz_info(self, "Đăng nhập", f"Dịch vụ '{record.service}' chưa hỗ trợ đăng nhập tự động.")
```

- [ ] **Verify import**

```powershell
python -c "from wgz_updater.features.accounts.account_list_page import AccountListPage; print('OK')"
```

Expected: `OK`

- [ ] **Commit**

```bash
git add wgz_updater/features/accounts/account_list_page.py
git commit -m "feat: add AccountListPage with per-account rows, add/edit/delete, login"
```

---

## Task 15: AccountsView rewrite — coordinator + Drive/GitHub sync

**Files:**
- Modify: `wgz_updater/features/accounts/view.py` (complete rewrite)

- [ ] **Rewrite `wgz_updater/features/accounts/view.py`**

```python
from __future__ import annotations

import json
import logging

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from ...core.config import load_config
from ...resources.strings_vi import (
    DIALOG_ERROR_TITLE, MSG_ACCOUNTS_LOADED,
    MSG_ACCOUNTS_SAVED, MSG_DRIVE_ERROR,
)
from ...widgets.dialogs import wgz_error, wgz_info
from .account_list_page import AccountListPage
from .models import AccountRecord
from .service_grid_page import ServiceGridPage

log = logging.getLogger(__name__)

_PAGE_GRID = 0
_PAGE_LIST = 1


class _DriveLoadWorker(QThread):
    finished_ok = pyqtSignal(dict)   # {service: [AccountRecord, ...]}
    failed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def run(self) -> None:
        try:
            from ..accounts.sheets_service import SheetsService
            svc = SheetsService()
            records = svc.fetch_accounts()
            # Group by service
            grouped: dict[str, list[AccountRecord]] = {}
            for rec in records:
                grouped.setdefault(rec.service, []).append(rec)
            self.finished_ok.emit(grouped)
        except Exception as exc:
            log.exception("Drive load failed")
            self.failed.emit(str(exc))


class _DriveSaveWorker(QThread):
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, records: list[AccountRecord], parent=None) -> None:
        super().__init__(parent)
        self._records = records

    def run(self) -> None:
        try:
            from ..accounts.sheets_service import SheetsService
            svc = SheetsService()
            svc.write_accounts(self._records)
            # Also push to GitHub if token available
            try:
                from ..accounts.github_sync import GitHubSync
                data = {}
                for rec in self._records:
                    data.setdefault(rec.service, []).append(rec.to_json())
                GitHubSync().push(self._records)
            except Exception:
                log.warning("GitHub sync skipped (token missing or error)", exc_info=True)
            self.finished_ok.emit()
        except Exception as exc:
            log.exception("Drive save failed")
            self.failed.emit(str(exc))


class AccountsView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._accounts: dict[str, list[AccountRecord]] = {}
        self._current_service: str = ""
        self._load_worker: _DriveLoadWorker | None = None
        self._save_worker: _DriveSaveWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget(self)
        layout.addWidget(self._stack)

        self._grid_page = ServiceGridPage(self)
        self._list_page = AccountListPage(self)

        self._stack.addWidget(self._grid_page)  # _PAGE_GRID = 0
        self._stack.addWidget(self._list_page)  # _PAGE_LIST = 1

        # Navigation wiring
        self._grid_page.service_selected.connect(self._on_service_selected)
        self._list_page.back_requested.connect(self._on_back)
        self._list_page.save_requested.connect(self._on_save)
        self._list_page.load_requested.connect(self._on_load)

        # Pre-populate grid with empty data (Drive loads lazily)
        self._grid_page.populate({})

        # Load game names for the account dialog dropdown
        try:
            cfg = load_config(prefer_remote=False)
            self._game_names = [g.name for g in cfg.games]
        except Exception:
            self._game_names = []

        # Auto-load accounts from Drive on first open
        self._on_load()

    def _on_service_selected(self, service: str) -> None:
        self._current_service = service
        records = self._accounts.get(service, [])
        self._list_page.show_service(service, records, self._game_names)
        self._stack.setCurrentIndex(_PAGE_LIST)

    def _on_back(self) -> None:
        # Sync any edits back into accounts dict before leaving
        self._accounts[self._current_service] = self._list_page.get_records()
        self._grid_page.populate(self._accounts)
        self._stack.setCurrentIndex(_PAGE_GRID)

    def _on_load(self) -> None:
        if self._load_worker and self._load_worker.isRunning():
            return
        worker = _DriveLoadWorker(self)
        worker.finished_ok.connect(self._on_loaded)
        worker.failed.connect(lambda msg: wgz_error(self, DIALOG_ERROR_TITLE, MSG_DRIVE_ERROR.format(error=msg)))
        self._load_worker = worker
        worker.start()

    def _on_loaded(self, grouped: dict) -> None:
        self._accounts = grouped
        self._grid_page.populate(self._accounts)
        if self._stack.currentIndex() == _PAGE_LIST and self._current_service:
            records = self._accounts.get(self._current_service, [])
            self._list_page.set_records(records)
        wgz_info(self, "Drive", MSG_ACCOUNTS_LOADED)

    def _on_save(self) -> None:
        if self._save_worker and self._save_worker.isRunning():
            return
        # Collect current page's edits
        self._accounts[self._current_service] = self._list_page.get_records()
        all_records = [r for recs in self._accounts.values() for r in recs]
        worker = _DriveSaveWorker(all_records, self)
        worker.finished_ok.connect(lambda: wgz_info(self, "Drive", MSG_ACCOUNTS_SAVED))
        worker.failed.connect(lambda msg: wgz_error(self, DIALOG_ERROR_TITLE, MSG_DRIVE_ERROR.format(error=msg)))
        self._save_worker = worker
        worker.start()
```

- [ ] **Verify the app launches with Accounts tab working**

```powershell
python -m wgz_updater
```

Expected: Switch to Accounts tab → shows service grid (Steam, Riot cards) → clicking a card opens account list → Back returns to grid. Drive load runs in background on open.

- [ ] **Commit**

```bash
git add wgz_updater/features/accounts/view.py
git commit -m "feat: rewrite AccountsView as 2-level hierarchy with Drive/GitHub sync"
```

---

## Task 16: AutoPath worker — registry-based Steam/Riot detection

**Files:**
- Create: `wgz_updater/core/auto_path.py`

- [ ] **Create `wgz_updater/core/auto_path.py`**

```python
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
    # Method 1: known default path
    default = Path(
        __import__("os").environ.get("LOCALAPPDATA", ""),
        "Riot Games", "Riot Client", "RiotClientServices.exe",
    )
    if default.exists():
        return str(default)

    # Method 2: registry
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
```

- [ ] **Verify import**

```powershell
python -c "from wgz_updater.core.auto_path import AutoPathWorker; print('OK')"
```

Expected: `OK`

- [ ] **Commit**

```bash
git add wgz_updater/core/auto_path.py
git commit -m "feat: add AutoPathWorker — registry-based Steam/Riot path detection"
```

---

## Task 17: App startup — admin elevation + LocalConfig + AutoPath

**Files:**
- Modify: `wgz_updater/app.py`

- [ ] **Update `wgz_updater/app.py`**

Replace the `main()` function with:

```python
def main() -> int:
    from .core.local_config import LocalConfig
    from .core.win32_utils import elevate_and_relaunch, is_admin

    # Admin elevation — must happen before QApplication
    if not is_admin():
        launched = elevate_and_relaunch()
        if launched:
            return 0  # Elevated process is starting; exit this one

    configure_logging()
    _install_excepthook()

    # Load persisted settings
    LocalConfig().load()

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setOrganizationName("WGZ")
    app.setFont(QFont("Segoe UI Variable", 10))

    instance = SingleInstance()
    if instance.already_running:
        log.info("Another instance detected — focusing existing window")
        instance.focus_existing()
        return 0

    _install_app_icon(app)
    _load_qss(app)

    window = MainWindow()
    window.show()

    try:
        from .features.library.view import LibraryView
        window.install_view("library", LibraryView(window))
    except Exception:
        log.exception("Library view failed to load")

    try:
        from .features.accounts.view import AccountsView
        window.install_view("accounts", AccountsView(window))
    except Exception:
        log.exception("Accounts view failed to load")

    try:
        from .features.settings.view import SettingsView
        window.install_view("settings", SettingsView(window))
    except Exception:
        log.exception("Settings view failed to load")

    try:
        from .widgets.status_strip import StatusStrip
        window.install_status_strip(StatusStrip(window))
    except Exception:
        log.exception("Status strip failed to load")

    # Background: auto-detect Steam/Riot paths
    try:
        from .core.auto_path import AutoPathWorker
        auto = AutoPathWorker(app)
        auto.steam_found.connect(lambda p: log.info("Steam path set: %s", p))
        auto.riot_found.connect(lambda p: log.info("Riot path set: %s", p))
        auto.start()
    except Exception:
        log.exception("AutoPathWorker failed to start")

    rc = app.exec()
    instance.release()
    return rc
```

- [ ] **Verify the app launches**

```powershell
python -m wgz_updater
```

Expected: UAC prompt appears (if not already running as admin) → app opens normally. Log shows `Steam path set:` or `Riot path set:` if they're installed.

- [ ] **Commit**

```bash
git add wgz_updater/app.py
git commit -m "feat: add admin elevation, LocalConfig load, AutoPathWorker on startup"
```

---

## Verification Checklist

Run `python -m wgz_updater` and verify each item:

- [ ] **1. Game grid loads** — 33 games appear as cards with images, HOT/NEW/etc. badges, correct button text (Tải Về / Cập Nhật / ✓ Đã Cài)
- [ ] **2. Search filters cards** — typing in search box shows/hides cards in real time
- [ ] **3. Card click → detail page** — hero image loads, mod combobox populated, path_guide text shown, install path pre-filled from last session
- [ ] **4. Slideshow** — games with `slideshow` in themes rotate every 4 seconds
- [ ] **5. Download flow** — click "Tải Về", DownloadProgressPage shows speed/ETA/cancel → extraction completes → success → grid, card now shows "✓ Đã Cài"
- [ ] **6. Multi-part counter** — game with multiple URLs shows "Phần 1/3" etc.
- [ ] **7. Cancel download** — Cancel button stops download, returns to grid
- [ ] **8. Launch game** — set install path where `launch_file` exists → Launch button enables → click → game starts
- [ ] **9. Accounts grid** — Steam and Riot cards appear; other services from Drive load appear after auto-load
- [ ] **10. Drive auto-load** — accounts load on open; wgz_info shows "Đã tải tài khoản từ Drive"
- [ ] **11. Account list** — clicking a service card opens per-service list with nickname, game tag, Copy PW, Login, Edit, Delete buttons
- [ ] **12. Add account** — form opens with all fields; saved record appears in list; Save button enabled
- [ ] **13. Edit account** — form pre-filled with existing data; changes reflected on confirm
- [ ] **14. Drive save** — "Lưu lên Drive" pushes to Sheets + GitHub; success dialog appears
- [ ] **15. Riot auto-login** — select Riot account → Login → RiotLoginWorker fires (check log)
- [ ] **16. Steam login** — select Steam account → Login → Steam opens with credentials
- [ ] **17. Admin elevation** — running without admin triggers UAC prompt; app runs elevated after
- [ ] **18. Steam/Riot auto-detect** — check log for `Steam path set:` / `Riot path set:` on first launch
