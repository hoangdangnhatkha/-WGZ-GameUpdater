# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```powershell
# Run from source
python -m wgz_updater

# Run the bootstrap launcher splash (updates GameUpdater.exe from GitHub, then launches it)
python -m wgz_updater.launcher

# Build standalone EXEs (PyInstaller, produces dist/GameUpdater.exe + dist/Launcher.exe)
cd wgz_updater && build\build_all.bat
```

No test suite or linter is configured in this project.

## Architecture

**Entry points:** `wgz_updater/app.py` (main app, `-m wgz_updater`) and `wgz_updater/launcher.py` (bootstrap updater splash, `-m wgz_updater.launcher`).

**Application flow (`app.py`):**
1. Load `LocalConfig`, install exception hook, create `QApplication`
2. `SingleInstance` mutex check — if another instance exists, focus it and exit
3. Load credentials from disk (`google_auth.load_credentials`) → if valid, show `MainWindow` directly; if not, show `LoginWindow` as gate
4. `MainWindow` creates the shell and `_launch_main()` installs feature views (Library, Accounts, Settings) into the stacked widget + starts `AutoPathWorker` (auto-discovers Steam/Riot install paths)

**Window shell (`main_window.py`):**
- Fixed 1280×800, frameless, Mica backdrop (DWM)
- `TitleBar` with minimize/close only (no maximize)
- `Sidebar` with numbered navigation items + `_UserBadge` (avatar initials, name, email, logout)
- `QStackedWidget` for view switching, keyed by `"library"`, `"accounts"`, `"settings"`
- Views are lazily installed via `install_view()`; the sidebar emits `nav_changed` → `_on_nav` switches stack index
- Optional `StatusStrip` widget at the bottom (installed by `install_status_strip`)

**Features are self-contained packages under `wgz_updater/features/`:**

- **`features/auth/`** — Google OAuth login flow. `LoginWindow` runs `GoogleAuthWorker` (QThread) which uses `google_auth_oauthlib` InstalledAppFlow with local server. On success emits `authenticated(UserProfile, Credentials)` signal. `AuthSession` is a class-level singleton holding the current profile+credentials. `UserProfile` is a plain dataclass.

- **`features/library/`** — Game browser with 3 sub-pages in its own `QStackedWidget`: `GameGridPage` (editorial grid with featured hero + game cards), `GameDetailPage` (mission-briefing style detail for a single game), `DownloadProgressPage` (download + extract worker with progress). `LibraryView` owns an `InstallRegistry` (persists install paths/versions to JSON in `%LOCALAPPDATA%/WGZ_Game_Launcher/userdata/`). Workers run on QThread and signals are forwarded up to `StatusStrip`.

- **`features/accounts/`** — Account manager with 2 sub-pages: `ServiceGridPage` (game grid grouped by themes) and `AccountListPage` (CRUD table for one game's accounts). Data is stored in Google Drive via `DriveAccountsService`. Load/save operations run on `_DriveLoadWorker` / `_DriveSaveWorker` QThreads. On startup, auto-loads accounts silently via `QTimer.singleShot`. The grid derives game names from config themes + games.

- **`features/settings/`** — Install path display, GitHub token editor, version info + check-update, open logs folder, reset config cache.

**Core infrastructure (`wgz_updater/core/`):**

- `paths.py` — All filesystem constants. `_resolve_base()` handles frozen (PyInstaller) vs dev. Key directories: `APP_DIR` (`%LOCALAPPDATA%/WGZ_Game_Launcher/GameUpdater`), `USER_DATA_DIR`, `LOG_DIR`. GitHub raw URLs are constants here.
- `config.py` — `AppConfig` pydantic model (updater info, games list, themes dict). `load_config(prefer_remote=True)` fetches JSON from GitHub, caches locally, falls back to bundled/local copies. `Game` model uses validators for coercion.
- `http.py` — Singleton `httpx.Client` with HTTP/2, 15s timeout. `get_json()` appends cache-bust timestamp.
- `updater.py` — Version comparison (`packaging.version`), read/write `version.txt`, spawn updater subprocess.
- `single_instance.py` — Windows named mutex + `EnumWindows` to find and focus existing window.
- `win32_utils.py` — DWM Mica backdrop enablement via `dwmapi`.
- `auto_path.py` — Scrapes known install paths for Steam/Riot games on startup.

**Data flow:** Remote config (GitHub JSON) → `AppConfig` pydantic model → feature views consume it. Install state is tracked locally via `InstallRegistry` (JSON file). Account data is read/written to Google Drive via background workers.

**Styling:** Single `resources/qss/styles.qss` loaded at app startup. No per-widget stylesheets — everything is QSS-driven with objectName selectors (`#Sidebar`, `#NavItem`, etc.).

**Strings:** All Vietnamese UI strings in `resources/strings_vi.py` — imported as constants, not a gettext/i18n system.

**Build:** PyInstaller via `.spec` files (`build/GameUpdater.spec`, `build/Launcher.spec`). `build_all.bat` cleans previous build dirs, runs both specs. The launcher uses `gdown` to download updates from Google Drive.
