# WGZ Game Updater (PyQt6)

A Win11 Fluent / clean-productivity rewrite of the original tkinter game updater.
Feature-complete with the legacy app; all underlying libraries swapped to
better-maintained / native equivalents.

## Run from source

```powershell
cd "C:\Users\Dang\Desktop\Exe File\[WGZ]GameUpdaterProject\WGZGameUpdater"
python -m pip install -r wgz_updater\requirements.txt
python -m wgz_updater
```

To run the bootstrap launcher splash:

```powershell
python -m wgz_updater.launcher
```

## Build

```powershell
cd "C:\Users\Dang\Desktop\Exe File\[WGZ]GameUpdaterProject\WGZGameUpdater\wgz_updater"
build\build_all.bat
```

Produces `dist\GameUpdater.exe` and `dist\Launcher.exe`.

## Layout

- `app.py` — `QApplication` entry, single-instance, exception hook.
- `main_window.py` — frameless shell, sidebar, stacked content, Mica.
- `launcher.py` — bootstrap splash that updates `GameUpdater.exe` from GitHub JSON.
- `core/` — paths, http (httpx), config (pydantic), updater, win32 utils, single-instance, logging.
- `widgets/` — title bar, sidebar, status strip, pill, drop zone, progress card.
- `features/library/` — game table, detail panel, download/extract workers.
- `features/accounts/` — account list, Sheets service, GitHub sync (httpx), Riot login (pywinauto), trailer (QWebEngineView).
- `features/settings/` — install path, GitHub token, version, log access.
- `resources/` — icons, qss, Vietnamese strings.

## Library swap summary

| Old | New |
|---|---|
| tkinter + ttk | PyQt6 |
| sv_ttk + pywinstyles | qss + DWM Mica |
| requests | httpx (HTTP/2) |
| PyGithub | httpx + GitHub REST |
| pyautogui + pygetwindow | pywinauto (UI Automation) |
| pyperclip | QClipboard |
| pywebview + multiprocessing | QWebEngineView |
| tkinterdnd2 | Qt drag/drop |
| rarfile | direct UnRAR.exe |
| ad-hoc dict | pydantic v2 models |
