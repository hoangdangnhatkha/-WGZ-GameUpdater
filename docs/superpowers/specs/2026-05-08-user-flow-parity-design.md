# User Flow Parity Design — WGZ Game Updater PyQt6 Rewrite

**Date:** 2026-05-08  
**Status:** Approved

## Problem

The PyQt6 rewrite in `wgz_updater/` has modernized the framework and library stack but does not replicate the user flows of the original tkinter app. Specifically:

- **Library tab**: The original has a 3-page flow (game card grid → game detail page → download progress page). The rewrite has a table + right panel (no images, no page transitions, no multi-part download progress).
- **Accounts tab**: The original has a 2-level flow (service/game icon grid → account list per service). The rewrite has a flat table with no Google Drive sync and no per-service grouping.
- **Startup**: Missing admin rights enforcement and auto Steam/Riot path detection.
- **Launch game**: Stub — does nothing.

## User's Confirmed Choices

| Decision | Choice |
|---|---|
| Library display | **Grid of cards** (images, tags, status button) — like original |
| Library navigation | **3 separate pages** (grid → detail → progress) with back buttons |
| Accounts display | **2-level hierarchy** (service grid → account list) — like original |
| Drive sync | **Full Google Drive + GitHub sync** (credentials.json already configured) |

## Architecture — Approach

Each feature view owns an internal `QStackedWidget`. The sidebar stays visible at all times; only the feature's content area switches pages. Back navigation is handled by the feature's own signals.

```
MainWindow
├── Sidebar (always visible)
└── QStackedWidget (feature selector)
    ├── LibraryView  ← owns its own QStackedWidget
    │   ├── Page 0: GameGridPage
    │   ├── Page 1: GameDetailPage
    │   └── Page 2: DownloadProgressPage
    ├── AccountsView ← owns its own QStackedWidget
    │   ├── Page 0: ServiceGridPage
    │   └── Page 1: AccountListPage
    └── SettingsView (unchanged)
```

---

## Section 1 — Library Feature

### 1.1 GameGridPage (`features/library/game_grid_page.py`)

A `QScrollArea` containing a `QWidget` with a `QGridLayout` (3 columns). Populated from the `Game` list loaded by `load_config()`.

**Per card** (`GameCard` widget):
- 192×89 px image (async loaded via `ImageLoader`)
- Tag badge (QLabel with QSS color per tag: HOT=#ff4d4d, GOTY=#ffd700, NEW=#4cff00, UPD=#4a90e2, BEST=#9b59b6)
- Game name label
- Action button text changes by `InstallStatus`: "Tải Về" / "Cập Nhật" / "✓ Đã Cài"
- Right-click context menu for custom games: Đổi Tên, Đổi Ảnh, Chọn File Chạy, Xóa, Khôi phục Ảnh

**Top bar**: search `QLineEdit` (real-time filter by game name) + Refresh button.

Emits: `game_selected(Game)` → LibraryView switches to GameDetailPage.

### 1.2 GameDetailPage (`features/library/game_detail_page.py`)

Replaces the existing `game_detail_panel.py`.

Layout (top to bottom):
1. Back button (← Quay lại) — returns to GameGridPage
2. Hero image (QLabel, 460×215 px, loads async; slideshow timer cycles through `GameTheme.slideshow` URLs if present — theme data comes from the `"game_themes.json"` block in the remote config, not from `game.urls`)
3. Mod/variant selector (`QComboBox`) — populated from `game.urls` list; each entry label is `game.name + " - Part N"` or the mod name
4. `path_guide` text (`QPlainTextEdit`, read-only)
5. Install path row: `QLineEdit` (shows last-used path from `LocalConfig`) + Browse button (`QFileDialog`) + `DropZone`
6. Action button: "Tải Về" or "Cập Nhật" — triggers download
7. Launch button: "🚀 Chạy Game" — enabled only when `launch_file` exists at `install_path`

Install path persistence: reads/writes `LocalConfig.last_used_folder`. Per-game path saved to `LocalConfig.game_paths[game.id]`.

Launch file detection priority:
1. `LocalConfig.game_launchers[game.id]` (user-set)
2. `game.launch_file` from JSON (relative path, joined with install path)
3. Disabled if neither found

Emits: `download_requested(Game, install_path, selected_url_index)`, `back_requested()`

### 1.3 DownloadProgressPage (`features/library/download_progress_page.py`)

Full-content page shown during download + extraction.

Layout:
- Game name label (large)
- Part indicator label: "Part 1/3" (hidden if single URL)
- `QProgressBar` (0–100)
- Speed label ("5.5 MB/s")
- ETA label ("00:45")
- Status text label ("Đang tải về...")
- Cancel button

After download completes, extraction starts on the same page (status label updates). On success: navigates back to GameGridPage and refreshes the card status. On failure: shows error dialog, stays on page with Retry / Back options.

Emits: `cancel_requested()`, `finished()`

### 1.4 ImageLoader (`features/library/image_loader.py`)

A pool of `QThread` workers. Each worker downloads one image URL via `httpx`, converts bytes to `QPixmap`, and emits `image_ready(url: str, pixmap: QPixmap)`.

Cache: two-layer
1. In-memory `dict[url, QPixmap]` (process lifetime)
2. Disk cache under `%LOCALAPPDATA%\WGZ_Game_Launcher\img_cache\<hash>.png`

`GameGridPage` and `GameDetailPage` call `ImageLoader.request(url, callback)`. If cached, callback fires immediately from the main thread.

### 1.5 LibraryView (`features/library/view.py`) — Rewrite

Becomes a thin coordinator: owns the `QStackedWidget`, wires signals between pages and workers. Continues emitting `worker_started / worker_message / worker_progress / worker_finished` for the `StatusStrip`.

Multi-part download: `DownloadWorker` is chained per URL index. `DownloadProgressPage` receives `(game, url_list, target_dir)` and drives the worker chain internally.

---

## Section 2 — Accounts Feature

### 2.1 ServiceGridPage (`features/accounts/service_grid_page.py`)

A `QScrollArea` with a `QGridLayout` (5 columns, matching original `MAX_COLS=5`).

Service list = `["Steam", "Riot"] + sorted(keys from g_user_accounts_data)`.

Per card: service icon (192×89 px, from preloaded or `ImageLoader`) + service name + account count badge.

Emits: `service_selected(service_name: str)`

### 2.2 AccountListPage (`features/accounts/account_list_page.py`)

Layout:
- Top bar: Back button + service name title + "Lưu lên Drive" + "Tải từ Drive" buttons
- Left side: scroll area with per-account rows
  - Per row: service icon, nickname, game tag, type label, Login button, Edit button, Delete button
- Right side: `TrailerPlayer` (existing widget)
- Bottom: "Thêm tài khoản" button

Account row Login button behavior:
- Steam: `subprocess.Popen([steam_path, "-login", username, password])`
- Riot: `RiotLoginWorker` (existing, wrapped)

Dirty flag: any add/edit/delete sets `_dirty = True` → enables "Lưu lên Drive" button.

Emits: `back_requested()`

### 2.3 AccountDialog (`features/accounts/account_dialog.py`)

`QDialog` for add/edit. Fields:
- Service (`QComboBox`): Steam, Riot, + custom
- Game (`QComboBox`): populated from `Game` list (the config)
- Nickname (`QLineEdit`)
- Username (`QLineEdit`)
- Password (`QLineEdit`, `EchoMode.Password` + show/hide toggle)

Returns `AccountRecord` on accept.

### 2.4 AccountsView (`features/accounts/view.py`) — Rewrite

Owns the `QStackedWidget` and coordinates Drive/GitHub sync.

On `ServiceGridPage` → first load: calls `SheetsService.fetch_accounts()` in a `QThread` worker; on result, populates `_accounts_data: dict[str, list[AccountRecord]]` and refreshes grid cards.

Save flow: serializes `_accounts_data` → `SheetsService.write_accounts()` + `GitHubSync.push()` in background worker.

---

## Section 3 — Core Additions

### 3.1 LocalConfig (`core/local_config.py`)

Singleton-ish class wrapping `%LOCALAPPDATA%\WGZ_Game_Launcher\settings.json`.

Fields managed:
```python
game_paths: dict[str, str]           # game_id → install dir
game_launchers: dict[str, str]       # game_id → relative exe path
installed_versions: dict[str, str]   # game_id → version string
custom_games: dict[str, dict]        # custom game definitions
display_name_overrides: dict[str, str]
theme_overrides: dict[str, str]
steam_path: str | None
riot_path: str | None
last_used_folder: str | None
```

`load() / save()` methods. `InstallRegistry` in `features/library/models.py` is updated to delegate install path + version tracking to `LocalConfig` (keeping its own `install_paths.json` for backwards compat or merging into `settings.json`).

### 3.2 AutoPath (`core/auto_path.py`)

Background QThread worker. Emits `steam_found(path)`, `riot_found(path)`.

Steam: `HKEY_CURRENT_USER\Software\Valve\Steam\SteamExe`  
Riot: Try Registry → `%LOCALAPPDATA%\Riot Games\RiotClientServices.exe` → shortcut scan

On result: `LocalConfig.steam_path = path; LocalConfig.save()`

### 3.3 Custom Dialogs (`widgets/dialogs.py`)

- `wgz_info(parent, title, message)` — styled QMessageBox
- `wgz_warn(parent, title, message)`
- `wgz_error(parent, title, message)`
- `wgz_ask(parent, title, message) → bool`
- `DownloadConfirmDialog(parent, game, url_count, disk_free_gb) → bool` — shows file count, estimated disk usage, confirms before download

### 3.4 App startup (`app.py`) — Updates

1. Admin rights: call `win32_utils.elevate_and_relaunch()` if `not win32_utils.is_admin()`
2. `LocalConfig().load()` — load persisted settings
3. Single instance check (already exists)
4. Configure logging
5. Create `QApplication`, load QSS, set dark palette
6. Create `MainWindow`, show, enable Mica
7. Fire `AutoPathWorker` in background; on `steam_found`/`riot_found`, update `LocalConfig` and notify `SettingsView`

---

## Section 4 — QSS Additions (`resources/qss/styles.qss`)

New selectors needed:
- `#GameCard` — dark card with hover highlight, 2px accent left border when selected
- `#TagBadge[tag="HOT"]` etc. — per-tag background colors
- `#ServiceCard` — accounts grid card
- `#HeroImage` — fixed-size image container
- `#ProgressPage` — full-content download page background
- `#AccountRow` — per-account row in AccountListPage

---

## Section 5 — Files Summary

### New files
| File | Purpose |
|---|---|
| `features/library/game_grid_page.py` | 3-column game card grid |
| `features/library/game_card.py` | Individual game card widget |
| `features/library/game_detail_page.py` | Hero image, mod selector, path, download/launch |
| `features/library/download_progress_page.py` | Full-screen download + extract progress |
| `features/library/image_loader.py` | Async image download + 2-layer cache |
| `features/accounts/service_grid_page.py` | 5-column service icon grid |
| `features/accounts/account_list_page.py` | Per-service account list with Drive sync |
| `features/accounts/account_dialog.py` | Add/edit account QDialog |
| `core/local_config.py` | settings.json wrapper (game paths, launchers, Steam/Riot paths) |
| `core/auto_path.py` | Background Steam/Riot path detection |
| `widgets/dialogs.py` | Styled dialog helpers + DownloadConfirmDialog |

### Modified files
| File | Change |
|---|---|
| `features/library/view.py` | Rewrite: QStackedWidget coordinator, wire 3 pages |
| `features/accounts/view.py` | Rewrite: QStackedWidget coordinator, wire 2 pages + Drive sync |
| `features/library/models.py` | InstallRegistry delegates to LocalConfig |
| `app.py` | Add admin check, LocalConfig load, AutoPathWorker |
| `resources/strings_vi.py` | Add missing strings for new pages |
| `resources/qss/styles.qss` | Add GameCard, ServiceCard, ProgressPage, TagBadge styles |
| `core/config.py` | Add `GameTheme(image, slideshow, trailer_url)` model; parse `"game_themes.json"` block from remote JSON into `AppConfig.themes: dict[str, GameTheme]`; verify Game model has `tag`, `launch_file`, `delete_before_extract` fields |

### Deleted files
| File | Reason |
|---|---|
| `features/library/game_detail_panel.py` | Replaced by game_detail_page.py |
| `features/library/game_table_model.py` | Table replaced by grid |
| `widgets/progress_card.py` | Replaced by download_progress_page.py |

---

## Section 6 — Verification Checklist

1. **Game grid loads**: 33 games appear as cards with images, HOT/NEW/etc. badges, correct status button text
2. **Search filters cards** in real-time
3. **Card click → detail page**: hero image, mod combobox, path_guide text, install path pre-filled
4. **Download flow**: click Download → DownloadProgressPage shows speed/ETA/cancel → extraction → success → back to grid, card shows "Đã Cài"
5. **Multi-part**: game with multiple URLs shows "Part 1/3" counter
6. **Launch game**: set install path → launch button enables → click → game launches
7. **Accounts grid**: Steam, Riot + other services appear as icon cards
8. **Drive load**: clicking "Tải từ Drive" fetches accounts from Google Sheets
9. **Account list**: service accounts shown with nickname, game tag, login/edit/delete buttons
10. **Add account**: dialog opens with all fields, saves to list, dirty flag set
11. **Drive save**: "Lưu lên Drive" pushes to Sheets + GitHub
12. **Riot auto-login**: select Riot account → Login → RiotLoginWorker fires
13. **Admin elevation**: running without admin → UAC prompt
14. **Steam/Riot auto-detect**: paths found from registry on first launch
